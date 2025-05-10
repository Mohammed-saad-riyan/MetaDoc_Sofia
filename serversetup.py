from flask import Flask, request, jsonify
import os
import whisper
import ollama
import re
import tempfile
import subprocess
import time
import json
import datetime
from gtts import gTTS
from threading import Timer
from hassan2 import generate_keyframes_from_audio
from transformers import AutoModelForCausalLM, AutoTokenizer
from datetime import datetime, timedelta
from dateutil import parser

app = Flask(__name__)
UPLOAD_DIR = 'uploads'
OUTPUT_DIR = 'output'
REMINDERS_FILE = "reminders.json"
APPOINTMENTS_FILE = "appointments.json"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize Whisper model
model = whisper.load_model("tiny.en")
AUDIO_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "response.wav")
KEYFRAMES_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "response_keyframes.json")

# Global variables
animation_active = False
animation_start_time = 0
current_audio_duration = 0

# System prompt for the medical assistant
SYSTEM_PROMPT = """You are Dr. Sophia (Smart Optimized Physician Health Intelligence Assistant), 
a metahuman doctor providing comprehensive healthcare support through advanced AI capabilities.

Key Capabilities:
1. Schedule and manage medical appointments
2. Set medication reminders and health-related alerts
3. Provide basic medical information and guidance
4. Assist with healthcare scheduling and organization

IMPORTANT GUIDELINES:
- Keep responses professional, clear, and concise
- Focus on healthcare-related inquiries
- Maintain patient privacy and confidentiality
- NEVER create or mention fictional appointments or reminders
- Only reference actual appointments and reminders from the system database
- Use specific command tags for data operations:
  * <VIEW_REMINDERS> - To view existing reminders
  * <SET_REMINDER> - To set a new reminder
  * <VIEW_APPOINTMENTS> - To view actual scheduled appointments
  * <SCHEDULE_APPOINTMENT> - To schedule a new appointment

Remember: 
- You are Dr. Sophia, combining medical expertise with a compassionate approach
- Only discuss appointments and reminders that actually exist in the system
- If asked about specific appointments or reminders, always verify with the database first
- Never make assumptions about existing appointments or reminders
"""

def load_json_data(filename, default=None):
    """Load data from a JSON file"""
    if default is None:
        default = []
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        else:
            with open(filename, 'w') as f:
                json.dump(default, f)
            return default
    except Exception as e:
        print(f"Error loading {filename}: {str(e)}")
        return default

def save_json_data(filename, data):
    """Save data to a JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving to {filename}: {str(e)}")
        return False

def extract_date_time(text):
    """Extract date and time from text"""
    try:
        now = datetime.now()
        
        if "tomorrow" in text.lower():
            return now + timedelta(days=1)
        elif "day after tomorrow" in text.lower():
            return now + timedelta(days=2)
        elif "next week" in text.lower():
            return now + timedelta(weeks=1)
        
        return parser.parse(text, fuzzy=True)
    except Exception as e:
        print(f"Error extracting date/time: {str(e)}")
        return now

def set_reminder(text):
    """Set a reminder"""
    try:
        reminder_text = text.lower()
        reminder_for = re.search(r'remind (?:me|the patient|us) (?:to|about) (.*?)(?:at|on|in|$)', reminder_text)
        if not reminder_for:
            reminder_for = re.search(r'set (?:a|an) reminder (?:to|for|about) (.*?)(?:at|on|in|$)', reminder_text)
            
        reminder_subject = reminder_for.group(1).strip() if reminder_for else "General reminder"
        reminder_time = extract_date_time(reminder_text)
        
        reminders = load_json_data(REMINDERS_FILE, [])
        new_reminder = {
            "id": len(reminders) + 1,
            "subject": reminder_subject,
            "time": reminder_time.strftime("%Y-%m-%d %H:%M"),
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "completed": False
        }
        
        reminders.append(new_reminder)
        save_json_data(REMINDERS_FILE, reminders)
        
        return f"Reminder set for {reminder_subject} at {reminder_time.strftime('%Y-%m-%d %H:%M')}"
    except Exception as e:
        print(f"Error setting reminder: {str(e)}")
        return "I couldn't set that reminder. Please try again with a specific time and subject."

def schedule_appointment(text):
    """Schedule an appointment"""
    try:
        appointment_text = text.lower()
        appointment_type_match = re.search(r'(appointment|visit|consultation|checkup|follow-up) (?:with|for) (.*?)(?:on|at|in|$)', appointment_text)
        
        appointment_type = appointment_type_match.group(1).strip() if appointment_type_match else "General appointment"
        doctor_or_dept = appointment_type_match.group(2).strip() if appointment_type_match else "Doctor MEDICAL"
        
        appointment_time = extract_date_time(appointment_text)
        
        appointments = load_json_data(APPOINTMENTS_FILE, [])
        new_appointment = {
            "id": len(appointments) + 1,
            "type": appointment_type,
            "with": doctor_or_dept,
            "time": appointment_time.strftime("%Y-%m-%d %H:%M"),
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "notes": ""
        }
        
        appointments.append(new_appointment)
        save_json_data(APPOINTMENTS_FILE, appointments)
        
        return f"Appointment scheduled: {appointment_type} with {doctor_or_dept} on {appointment_time.strftime('%Y-%m-%d at %H:%M')}"
    except Exception as e:
        print(f"Error scheduling appointment: {str(e)}")
        return "I couldn't schedule that appointment. Please try again with a specific time and doctor."

def view_reminders():
    """View active reminders - Only returns actual reminders from database"""
    try:
        reminders = load_json_data(REMINDERS_FILE, [])
        active_reminders = [r for r in reminders if not r.get('completed', False)]
        
        if not active_reminders:
            return "You currently have no active reminders in the system."
            
        result = "Here are your confirmed reminders from the system:\n"
        for i, reminder in enumerate(active_reminders, 1):
            time_str = reminder['time'].split()[1] if ' ' in reminder['time'] else reminder['time']
            date_str = reminder['time'].split()[0] if ' ' in reminder['time'] else "today"
            result += f"{i}. {reminder['subject']} at {time_str} on {date_str}\n"
            
        return result.strip()
    except Exception as e:
        print(f"Error viewing reminders: {str(e)}")
        return "I couldn't access the reminders database at this time."

def view_appointments():
    """View upcoming appointments - Only returns actual appointments from database"""
    try:
        appointments = load_json_data(APPOINTMENTS_FILE, [])
        now = datetime.now()
        upcoming = []
        
        for apt in appointments:
            apt_time = datetime.strptime(apt['time'], "%Y-%m-%d %H:%M")
            if apt_time > now:
                upcoming.append(apt)
                
        if not upcoming:
            return "You currently have no appointments scheduled in the system."
            
        result = "Here are your confirmed appointments from the system:\n"
        for i, apt in enumerate(upcoming, 1):
            result += f"{i}. {apt['type']} with {apt['with']} on {apt['time']}\n"
            
        return result.strip()
    except Exception as e:
        print(f"Error viewing appointments: {str(e)}")
        return "I couldn't access the appointments database at this time."

def generate_medical_response(text):
    """Generate response using Ollama with deepseek model"""
    try:
        # Check if the query is about appointments or reminders
        query_lower = text.lower()
        if any(word in query_lower for word in ['appointment', 'scheduled', 'booked', 'meeting']):
            # First check actual appointments
            appointments = load_json_data(APPOINTMENTS_FILE, [])
            if not appointments and 'view' in query_lower:
                return "I don't see any appointments currently scheduled in the system. Would you like to schedule one?"
                
        if any(word in query_lower for word in ['reminder', 'remind', 'alert']):
            # First check actual reminders
            reminders = load_json_data(REMINDERS_FILE, [])
            if not reminders and 'view' in query_lower:
                return "I don't see any active reminders in the system. Would you like to set one?"

        # Generate response using Ollama
        response = ollama.chat(
            model="deepseek-r1:1.5b",
            messages=[{"role": "user", "content": text}]
        )
        
        if response and "message" in response and "content" in response["message"]:
            raw_content = response["message"]["content"]
            response_text = clean_llm_output(raw_content)
        else:
            return "I apologize, but I'm having trouble generating a response at the moment."
        
        # Process commands in the response
        if "view reminders" in response_text.lower():
            return view_reminders()
        elif "view appointments" in response_text.lower():
            return view_appointments()
        elif "set reminder" in response_text.lower():
            return set_reminder(text)
        elif "schedule appointment" in response_text.lower():
            return schedule_appointment(text)
            
        return response_text
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return "I apologize, but I'm having trouble accessing the system at the moment. Please try again."

def clean_llm_output(raw: str) -> str:
    return re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

def estimate_audio_duration(text):
    words = len(text.split())
    estimated_seconds = words / 2.5
    return max(estimated_seconds + 0.5, 1.0)

def reset_animation_after_delay(delay_seconds):
    global animation_active
    
    def reset():
        global animation_active
        animation_active = False
        print(f"[INFO] Animation automatically deactivated after {delay_seconds:.2f} seconds")
    
    timer = Timer(delay_seconds, reset)
    timer.daemon = True
    timer.start()

def text_to_speech_and_save(text, output_audio_path=AUDIO_OUTPUT_FILE):
    global current_audio_duration
    
    try:
        current_audio_duration = estimate_audio_duration(text)
        print(f"[INFO] Estimated audio duration: {current_audio_duration:.2f} seconds")
        
        tts = gTTS(text=text, lang='en', tld='com', slow=False)
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
        return output_audio_path
    except Exception as e:
        print(f"[ERROR] TTS generation failed: {e}")
        current_audio_duration = 0
        return None

def process_audio_response():
    """Generate keyframes from the response audio"""
    try:
        if not os.path.exists(AUDIO_OUTPUT_FILE):
            print("[ERROR] Response audio file not found")
            return None
            
        print("[INFO] Generating keyframes from response audio")
        keyframes_file = generate_keyframes_from_audio(AUDIO_OUTPUT_FILE, KEYFRAMES_OUTPUT_FILE)
        
        if keyframes_file and os.path.exists(keyframes_file):
            print(f"[INFO] Successfully generated keyframes: {keyframes_file}")
            return keyframes_file
        else:
            print("[ERROR] Failed to generate keyframes")
            return None
    except Exception as e:
        print(f"[ERROR] Error processing audio response: {e}")
        return None

@app.route('/', methods=['POST'])
def transcribe_trail():
    global animation_active, animation_start_time
    print("[INFO] Incoming request")
    audio_file_path = os.path.join(UPLOAD_DIR, 'trail.wav')
    transcript = None
    response_text = None
    keyframes_file = None

    if os.path.exists(audio_file_path):
        print(f"[SCAN] Found audio file: {audio_file_path}")
        try:
            # Step 1: Transcribe input audio
            result = model.transcribe(audio_file_path)
            transcript = result["text"].strip()
            print(f"[TRANSCRIPT] {transcript}")

            # Step 2: Generate response
            response_text = generate_medical_response(transcript)
            print(f"[MEDICAL] Response: {response_text}")

            # Step 3: Convert response to speech
            audio_path = text_to_speech_and_save(response_text, AUDIO_OUTPUT_FILE)
            if not audio_path:
                raise Exception("Failed to generate speech audio")
            
            # Step 4: Generate keyframes from response audio
            keyframes_file = process_audio_response()
            if not keyframes_file:
                raise Exception("Failed to generate keyframes")
            
            # Step 5: Only activate animation after everything is ready
            print(f"[INFO] All assets generated, activating animation for {current_audio_duration:.2f} seconds")
            animation_active = True
            animation_start_time = time.time()
            
            # Schedule animation to turn off after audio finishes
            reset_animation_after_delay(current_audio_duration)

        except Exception as e:
            print(f"[ERROR] Error processing trail.wav: {e}")
            animation_active = False  # Ensure animation is off if there's an error
            return jsonify({"status": "error", "message": f"Failed to process audio: {e}"}), 500
    else:
        print("[ERROR] trail.wav not found")
        return jsonify({"status": "error", "message": "trail.wav not found in uploads/"}), 404

    # Return complete response with audio and keyframes
    response_data = {
        "status": "success",
        "message": "Processing completed successfully",
        "transcript": transcript,
        "medical_response": response_text,
        "audio_file": "output/response.wav",
        "keyframes_file": "output/response_keyframes.json" if keyframes_file else None,
        "start_animation": True,
        "audio_duration": current_audio_duration
    }
    
    return jsonify(response_data), 200

@app.route('/', methods=['GET'])
def home():
    return "Dr. Sophia's Medical Assistant is running!"

@app.route('/start_animation', methods=['GET'])
def start_animation():
    global animation_active
    response = {
        "start_animation": animation_active
    }
    elapsed = time.time() - animation_start_time if animation_active else 0
    print(f"[DEBUG] Animation status: {animation_active}, elapsed time: {elapsed:.2f}s")
    return jsonify(response)

@app.route('/force_animation', methods=['GET'])
def force_animation():
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

if __name__ == '__main__':
    print("[BOOT] Dr. Sophia's Medical Assistant running on port 5050")
    app.run(host='0.0.0.0', port=5050, debug=True)