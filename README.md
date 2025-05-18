# LIPRA – Real-Time Conversational MetaHuman System

LIPRA (Lifelike Intelligent Persona for Real-Time Assistance) is a system built to enable human-like conversations with MetaHumans in Unreal Engine. It combines AI-generated speech, phoneme-level lip sync, and facial animation to create realistic, expressive digital interactions in real time.

## What This Project Does

This project enables MetaHumans to speak and animate naturally in response to AI-generated conversations. It uses a local AI pipeline to process voice, generate responses, synthesize speech, and drive facial animation with phoneme precision inside Unreal Engine 5.

## Tech Stack

- Python (LLM pipeline, phoneme extraction, TTS)
- Flask (serving audio and phoneme JSON to Unreal)
- Unreal Engine 5.5 (MetaHuman integration, ControlRig, Blueprints, C++ components)
- DeepSeek, Whisper or equivalent for speech and text processing
- FFmpeg for audio conversion

## What’s Included in This Repository

This repository includes:

- All backend Python files:
  - Flask server to serve generated audio and phoneme data
  - Python scripts for processing LLM response, text-to-speech, and generating phoneme JSON
- C++ Unreal components:
  - MyClass.cpp
  - MyClass.h

These files contains the full logic for handling audio playback, phoneme-based control mapping, and triggering facial animations.

## Unreal Assets

Due to Unreal Engine size limitations and MetaHuman licensing, Unreal assets such as animation blueprints, ControlRig graphs, and MetaHuman meshes are **not included** in this repository. However, the included C++ code files represent the complete runtime logic used inside the project.

## How the System Works

1. User input is captured and sent to a local Python backend.
2. The backend processes the input with a local LLM and generates a response.
3. The response is converted to audio using TTS and analyzed into phoneme data.
4. Both the audio and the phoneme `.json` file are served via Flask.
5. Unreal Engine loads the files, plays the audio, and drives MetaHuman facial animation based on phoneme timings and mappings.


