import json
from flask import Flask, request, jsonify
import os
import whisper
import ollama
import re
import tempfile
import subprocess
import time
import glob  # Add this import for file pattern matching
from gtts import gTTS
from threading import Timer
import datetime
from phoneme_generator import process_audio_to_phonemes

app = Flask(__name__)
UPLOAD_DIR = 'uploads'
OUTPUT_DIR = 'output'
REMINDERS_FILE = 'reminders.json'
PATIENT_HISTORY_FILE = 'patient_history.json'

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize patient history if it doesn't exist
if not os.path.exists(PATIENT_HISTORY_FILE):
    # Create a basic structure for the patient history file
    default_patient_history = {
        "patient_name": "Saad",
        "age": 45,
        "medical_history": {
            "procedures": [
                {
                    "type": "heart surgery",
                    "date": "2025-05-01",
                    "doctor": "Dr. Reddys",
                    "details": "Coronary artery bypass grafting (CABG)"
                }
            ],
            "conditions": [
                "Coronary artery disease",
                "Mild hypertension",
                "Type 2 diabetes (controlled)"
            ]
        },
        "medications": [
            {
                "name": "Aspirin",
                "dosage": "81mg",
                "frequency": "once daily",
                "purpose": "Blood thinner",
                "schedule": "morning with breakfast"
            },
            {
                "name": "Metoprolol",
                "dosage": "25mg",
                "frequency": "twice daily",
                "purpose": "Beta blocker for heart",
                "schedule": "morning and evening"
            },
            {
                "name": "Lipitor",
                "dosage": "20mg",
                "frequency": "once daily",
                "purpose": "Cholesterol management",
                "schedule": "evening before bed"
            },
            {
                "name": "Metformin",
                "dosage": "500mg",
                "frequency": "twice daily",
                "purpose": "Diabetes management",
                "schedule": "with morning and evening meals"
            }
        ],
        "allergies": ["Penicillin"],
        "last_checkup": "2024-05-10",
        "next_appointment": "2025-06-10"
    }
    
    with open(PATIENT_HISTORY_FILE, 'w') as f:
        json.dump(default_patient_history, f, indent=2)
    print(f"[INFO] Created default patient history file: {PATIENT_HISTORY_FILE}")

# Initialize reminders file if it doesn't exist
if not os.path.exists(REMINDERS_FILE):
    with open(REMINDERS_FILE, 'w') as f:
        json.dump([], f)
    print(f"[INFO] Created empty reminders file: {REMINDERS_FILE}")

# Add cleanup function for JSON files
def cleanup_json_files():
    try:
        # Get all JSON files in the output directory
        json_files = glob.glob(os.path.join(OUTPUT_DIR, "*.json"))
        for file in json_files:
            try:
                os.remove(file)
                print(f"[CLEANUP] Deleted: {file}")
            except Exception as e:
                print(f"[CLEANUP] Error deleting {file}: {e}")
        print(f"[CLEANUP] Removed {len(json_files)} JSON files from {OUTPUT_DIR}")
    except Exception as e:
        print(f"[CLEANUP] Error during cleanup: {e}")

# Call cleanup function when server starts
cleanup_json_files()

model = whisper.load_model("tiny.en")
AUDIO_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "response.wav")

# Global variables to track animation state
animation_active = False
animation_start_time = 0
current_audio_duration = 0
current_keyframes_path = None

def get_patient_history():
    """Load the patient history data"""
    try:
        with open(PATIENT_HISTORY_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load patient history: {e}")
        return {}

SYSTEM_PROMPT = """
You are Dr. Sophia, a warm and friendly metahuman doctor providing quick and accurate medical support using advanced AI.

Guidelines:
- Always answer in 1-2 sentences, clear and medically accurate.
- Keep the tone friendly, casual, and comforting.
- Never sound too formal or robotic.
- If the issue sounds critical, urgent, or life-threatening, kindly say: 
  'That sounds serious, please book an appointment with a doctor as soon as possible.'
- You have access to Saad's medical history who recently had heart surgery. If asked about medications, history, or treatment, refer to this information.
- If asked to set a reminder, acknowledge that you've set it and briefly mention what it's for.
- When asked about existing reminders, ONLY reference actual reminders from the reminders.json file. Never create fictional reminders or make up reminder information that doesn't exist in the file.
- If there are no reminders when asked, simply state "You don't have any reminders set up at the moment."
"""

def parse_reminder(transcript):
    """
    Parse a transcript to extract reminder details
    Returns: (is_reminder, reminder_text, reminder_time) or (False, None, None) if not a reminder
    """
    # Common reminder request patterns
    reminder_patterns = [
        r"(?:set|create|add|make)(?:\s+a)?\s+reminder(?:\s+for)?\s+(.+?)(?:\s+(?:at|on|for)\s+(.+?))?(?:\.|\?|$)",
        r"remind\s+(?:me\s+)?(?:to\s+)?(.+?)(?:\s+(?:at|on|for)\s+(.+?))?(?:\.|\?|$)",
        r"don't\s+(?:let\s+me\s+)?forget\s+(?:to\s+)?(.+?)(?:\s+(?:at|on|for)\s+(.+?))?(?:\.|\?|$)"
    ]
    
    # Check each pattern
    for pattern in reminder_patterns:
        match = re.search(pattern, transcript, re.IGNORECASE)
        if match:
            reminder_text = match.group(1).strip()
            reminder_time = match.group(2).strip() if match.group(2) else "today"
            return True, reminder_text, reminder_time
    
    return False, None, None

def is_asking_about_reminders(transcript):
    """Check if the user is asking about existing reminders"""
    reminder_query_patterns = [
        r"(?:what|show|tell|list)(?:\s+are)?\s+(?:my|the)\s+reminders",
        r"(?:show|list|tell\s+me)(?:\s+my|the)\s+reminders",
        r"(?:do\s+i\s+have)(?:\s+any)?\s+reminders",
        r"(?:remind\s+me\s+of)(?:\s+my)?\s+reminders",
        r"what\s+do\s+i\s+need\s+to\s+remember"
    ]
    
    for pattern in reminder_query_patterns:
        if re.search(pattern, transcript, re.IGNORECASE):
            return True
    
    return False

def get_all_reminders():
    """Load and return all reminders from the reminders file"""
    try:
        with open(REMINDERS_FILE, 'r') as f:
            reminders = json.load(f)
        return reminders
    except Exception as e:
        print(f"[ERROR] Failed to load reminders: {e}")
        return []

def format_reminders_response(reminders):
    """Format reminders into a nice response"""
    if not reminders:
        return "You don't have any reminders set up at the moment."
    
    if len(reminders) == 1:
        reminder = reminders[0]
        return f"You have one reminder: to {reminder['text']} at {reminder['time']}."
    
    # Multiple reminders
    reminder_texts = []
    for i, reminder in enumerate(reminders):
        reminder_texts.append(f"{i+1}) to {reminder['text']} at {reminder['time']}")
    
    return f"You have {len(reminders)} reminders: {'. '.join(reminder_texts)}"

def save_reminder(reminder_text, reminder_time):
    """Save a reminder to the reminders file"""
    try:
        # Load existing reminders
        with open(REMINDERS_FILE, 'r') as f:
            reminders = json.load(f)
        
        # Add new reminder
        reminder = {
            "id": len(reminders) + 1,
            "text": reminder_text,
            "time": reminder_time,
            "created_at": datetime.datetime.now().isoformat(),
            "completed": False
        }
        reminders.append(reminder)
        
        # Save updated reminders
        with open(REMINDERS_FILE, 'w') as f:
            json.dump(reminders, f, indent=2)
            
        print(f"[INFO] Saved reminder: '{reminder_text}' for {reminder_time}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save reminder: {e}")
        return False

def clean_llm_output(raw: str) -> str:
    return re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

def estimate_audio_duration(text):
   
    words = len(text.split())
    estimated_seconds = words / 2.5
    # Add a little buffer
    return max(estimated_seconds + 0.5, 1.0)

def reset_animation_after_delay(delay_seconds):
    global animation_active
    
    def reset():
        global animation_active
        animation_active = False
        print(f"[INFO] Animation automatically deactivated after {delay_seconds:.2f} seconds")
    
    # Schedule the reset
    timer = Timer(delay_seconds, reset)
    timer.daemon = True  # So the timer doesn't prevent app shutdown
    timer.start()

def text_to_speech_and_save(text, output_audio_path=AUDIO_OUTPUT_FILE):
    global current_audio_duration, current_keyframes_path
    
    try:
        # Estimate duration before generating audio
        current_audio_duration = estimate_audio_duration(text)
        print(f"[INFO] Estimated audio duration: {current_audio_duration:.2f} seconds")
        
        tts = gTTS(text=text, lang='en', tld='com.au', slow=False)

        temp_mp3_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
        tts.save(temp_mp3_path)

        try:
            subprocess.run([
                'ffmpeg',
                '-y',
                '-i', temp_mp3_path,
                '-acodec', 'pcm_s16le',
                '-ar', '22050',
                '-ac', '1',
                output_audio_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            from pydub import AudioSegment
            sound = AudioSegment.from_mp3(temp_mp3_path)
            sound = sound.set_frame_rate(22050).set_channels(1)
            sound.export(output_audio_path, format="wav")

        os.remove(temp_mp3_path)
        
        # Generate phonemes after creating the audio file
        print("[INFO] Generating phoneme keyframes...")
        current_keyframes_path = process_audio_to_phonemes(output_audio_path, OUTPUT_DIR)
        if current_keyframes_path:
            print(f"[INFO] Generated keyframes at: {current_keyframes_path}")
        else:
            print("[WARNING] Failed to generate phoneme keyframes")
            
        return output_audio_path
    except Exception as e:
        print(f"[ERROR] TTS generation failed: {e}")
        current_audio_duration = 0
        current_keyframes_path = None
        return None

def generate_response(transcript):
    try:
        prompt = transcript.strip()
        if not prompt:
            return "I'm sorry, I didn't catch that. Could you please repeat?"

        # Check if this is a request to list existing reminders
        if is_asking_about_reminders(prompt):
            reminders = get_all_reminders()
            return format_reminders_response(reminders)
            
        # Check if this is a reminder request
        is_reminder, reminder_text, reminder_time = parse_reminder(prompt)
        if is_reminder and reminder_text:
            # Save the reminder
            if save_reminder(reminder_text, reminder_time):
                return f"I've set a reminder for you to {reminder_text} at {reminder_time}."
        
        # Load patient history to provide context
        patient_history = get_patient_history()
        
        # Add patient context to the system prompt
        context_prompt = SYSTEM_PROMPT
        if patient_history:
            medications = patient_history.get("medications", [])
            med_list = ", ".join([f"{m['name']} ({m['dosage']}, {m['frequency']}, {m['purpose']})" for m in medications[:3]])
            history = ", ".join(patient_history.get("medical_history", {}).get("conditions", [])[:3])
            
            additional_context = f"""
Additional patient context:
- Patient name: {patient_history.get('patient_name', 'Saad')}
- Recent procedures: {patient_history.get('medical_history', {}).get('procedures', [{}])[0].get('type', 'heart surgery')} on {patient_history.get('medical_history', {}).get('procedures', [{}])[0].get('date', 'N/A')} with {patient_history.get('medical_history', {}).get('procedures', [{}])[0].get('doctor', 'N/A')}
- Key conditions: {history}
- Current medications: {med_list}
- Next appointment: {patient_history.get('next_appointment', 'N/A')}

Current reminders:
{format_reminders_response(get_all_reminders())}
"""
            context_prompt += additional_context

        print(f"[INFO] Sending prompt to Ollama: {prompt[:50]}...")
        response = ollama.chat(
            model="deepseek-r1:1.5b",
            messages=[
                {"role": "system", "content": context_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        if response and "message" in response and "content" in response["message"]:
            raw_content = response["message"]["content"]
            return clean_llm_output(raw_content)
        else:
            print("[ERROR] Unexpected response format from Ollama")
            return "Sorry, I couldn't generate a response."
    except Exception as e:
        print(f"[ERROR] Error generating LLM response: {e}")
        return f"Error generating response: {str(e)}"

@app.route('/', methods=['POST'])
def transcribe_trail():
    global animation_active, animation_start_time, current_keyframes_path
    print("[INFO] Incoming request")
    audio_file_path = os.path.join(UPLOAD_DIR, 'trail.wav')
    transcript = None
    llm_response = None

    if os.path.exists(audio_file_path):
        print(f"[SCAN] Found audio file: {audio_file_path}")
        try:
            result = model.transcribe(audio_file_path)
            transcript = result["text"].strip()
            print(f"[TRANSCRIPT] {transcript}")

            llm_response = generate_response(transcript)
            print(f"[LLM] Response: {llm_response}")

            text_to_speech_and_save(llm_response, AUDIO_OUTPUT_FILE)
            
            # Set animation to active when we have a response
            animation_active = True
            animation_start_time = time.time()
            print(f"[INFO] Animation activated and will remain active for ~{current_audio_duration:.2f} seconds")
            
            # Schedule animation to turn off after audio finishes
            reset_animation_after_delay(current_audio_duration)

        except Exception as e:
            print(f"[ERROR] Error processing trail.wav: {e}")
            return jsonify({"status": "error", "message": f"Failed to process audio: {e}"}), 500
    else:
        print("[ERROR] trail.wav not found")
        return jsonify({"status": "error", "message": "trail.wav not found in uploads/"}), 404

    return jsonify({
        "status": "success",
        "message": "Transcription and audio response completed",
        "transcript": transcript,
        "llm_response": llm_response,
        "audio_file": "output/response.wav",
        "start_animation": True,
        "audio_duration": current_audio_duration,
        "keyframes_path": current_keyframes_path
    }), 200

@app.route('/', methods=['GET'])
def home():
    return "Server is running!"

@app.route('/start_animation', methods=['GET'])
def start_animation():
    global animation_active, current_keyframes_path
    
    # Convert to absolute path if we have a keyframes file
    absolute_keyframes_path = os.path.abspath(current_keyframes_path) if current_keyframes_path else None
    
    # Get the current state but immediately reset it
    current_state = animation_active
    if animation_active:
        animation_active = False
        print("[DEBUG] Animation flag reset after query")
    
    # Return the animation state with absolute keyframes path
    response = {
        "start_animation": current_state,
        "json_file_path": absolute_keyframes_path if current_state else None
    }
    
    # Add some debug info
    elapsed = time.time() - animation_start_time if current_state else 0
    print(f"[DEBUG] Animation status returned: {current_state}, elapsed time: {elapsed:.2f}s")
    print(f"[DEBUG] Current keyframes path: {absolute_keyframes_path}")
    
    return jsonify(response)

@app.route('/force_animation', methods=['GET'])
def force_animation():
    """Manually control animation state"""
    global animation_active
    
    action = request.args.get('action', 'status')
    
    if action == 'start':
        animation_active = True
        return jsonify({"status": "Animation started", "start_animation": True})
    elif action == 'stop':
        animation_active = False
        return jsonify({"status": "Animation stopped", "start_animation": False})
    else:
        return jsonify({"status": "Current animation state", "start_animation": animation_active})

@app.route('/reminders', methods=['GET'])
def get_reminders():
    """API endpoint to get all reminders"""
    try:
        with open(REMINDERS_FILE, 'r') as f:
            reminders = json.load(f)
        return jsonify({"status": "success", "reminders": reminders})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to load reminders: {e}"}), 500

@app.route('/patient_history', methods=['GET'])
def get_history():
    """API endpoint to get patient history"""
    try:
        patient_history = get_patient_history()
        return jsonify({"status": "success", "patient_history": patient_history})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to load patient history: {e}"}), 500

if __name__ == '__main__':
    print("[BOOT] Flask server running on port 5050")
    app.run(host='0.0.0.0', port=5050, debug=True)
