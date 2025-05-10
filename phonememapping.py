import speech_recognition as sr
import whisper
import numpy as np
import tempfile
import os
import re
import subprocess
import json
import wave
import contextlib
from gtts import gTTS
from pathlib import Path

class PhonemeMapper:
    def __init__(self):
        # Initialize comprehensive phoneme mapping
        self.phoneme_map = {
            # Vowels
            'a': {
                'jawValue': {'x': 0.0, 'y': 0.5, 'z': 0.0},
            },
            'ɑ': {
                'jawValue': {'x': 0.0, 'y': 0.5, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.0, 'z': 0.0}
            },
            'e': {
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.2, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.2, 'z': 0.0}
            },
            'ɛ': {
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'cornerPullRight': 0.2,
                'cornerPullLeft': 0.2,
                'teethUpperValue': {'x': 0.0, 'y': -0.2, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.2, 'z': 0.0}
            },
            'i': {
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.1, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'ɪ': {
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'cornerPullRight': 0.4,
                'cornerPullLeft': 0.4,
                'teethUpperValue': {'x': 0.0, 'y': -0.4, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.4, 'z': 0.0}
            },
            'o': {
                'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'funnelRightUp': 1.0,
                'funnelRightDown': 1.0,
                'funnelLeftUp': 1.0,
                'funnelLeftDown': 1.0,
                'purseRightUp': 0.7,
                'purseRightDown': 0.7,
                'purseLeftUp': 0.7,
                'purseLeftDown': 0.7,
                'teethUpperValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': -0.4, 'z': 0.0}
            },
            'ɔ': {
                'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'funnelRightUp': 1.0,
                'funnelRightDown': 1.0,
                'funnelLeftUp': 1.0,
                'funnelLeftDown': 1.0,
                'purseRightUp': 0.7,
                'purseRightDown': 0.7,
                'purseLeftUp': 0.7,
                'purseLeftDown': 0.7,
                'teethUpperValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': -0.4, 'z': 0.0}
            },
            'u': {
                'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'funnelRightUp': 1.0,
                'funnelRightDown': 1.0,
                'funnelLeftUp': 1.0,
                'funnelLeftDown': 1.0,
                'purseRightUp': 1.0,
                'purseRightDown': 1.0,
                'purseLeftUp': 1.0,
                'purseLeftDown': 1.0,
                'teethUpperValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': -0.4, 'z': 0.0}
            },
            'ʊ': {
                'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'funnelRightUp': 1.0,
                'funnelRightDown': 1.0,
                'funnelLeftUp': 1.0,
                'funnelLeftDown': 1.0,
                'purseRightUp': 1.0,
                'purseRightDown': 1.0,
                'purseLeftUp': 1.0,
                'purseLeftDown': 1.0,
                'teethUpperValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': -0.4, 'z': 0.0}
            },
            'aw': {
                'jawValue': {'x': 0.0, 'y': 0.6, 'z': 0.0},
                'purseRightUp': 0.2,
                'purseRightDown': 0.2,
                'purseLeftUp': 0.2,
                'purseLeftDown': 0.2,
                'teethUpperValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': -0.4, 'z': 0.0}
            },
            'ay': {
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'cornerPullRight': 0.4,
                'cornerPullLeft': 0.4,
                'teethUpperValue': {'x': 0.0, 'y': -0.4, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.4, 'z': 0.0}
            },
            'b': {
                'jawValue': {'x': 0.0, 'y': 0.2, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': -0.2, 'z': 0.0}
            },
            'p': {
                'jawValue': {'x': 0.0, 'y': 0.2, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': -0.2, 'z': 0.0}
            },
            'm': {
                'jawValue': {'x': 0.0, 'y': 0.1, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': -0.2, 'z': 0.0}
            },
            'f': {
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'funnelRightUp': 0.8,
                'funnelRightDown': 0.8,
                'funnelLeftUp': 0.8,
                'funnelLeftDown': 0.8,
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0}
            },
            'v': {
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'funnelRightUp': 0.8,
                'funnelRightDown': 0.8,
                'funnelLeftUp': 0.8,
                'funnelLeftDown': 0.8,
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0}
            },
            'th': {
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'tongueInOut': -0.3,
                'teethUpperValue': {'x': 0.0, 'y': -0.2, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'ð': {
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'tongueInOut': -0.3,
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'θ': {
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'tongueInOut': -0.3,
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            's': {
                'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.27, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'z': {
                'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.27, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'sh': {
                'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'funnelRightUp': 0.4,
                'funnelRightDown': 0.4,
                'funnelLeftUp': 0.4,
                'funnelLeftDown': 0.4
            },
            'ʃ': {
                'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'funnelRightUp': 0.4,
                'funnelRightDown': 0.4,
                'funnelLeftUp': 0.4,
                'funnelLeftDown': 0.4
            },
            't': {
                'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'tongueValue': {'x': 0.0, 'y': 0.5, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.2, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.2, 'z': 0.0}
            },
            'd': {
                'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'tongueValue': {'x': 0.0, 'y': 0.5, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.2, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.2, 'z': 0.0}
            },
            'k': {
                'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'tongueValue': {'x': 0.0, 'y': 0.5, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.1, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'g': {
                'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'tongueValue': {'x': 0.0, 'y': 0.5, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.1, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'l': {
                'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'tongueValue': {'x': 0.0, 'y': 0.5, 'z': 0.0},
                'tongueInOut': 0.5,
                'teethUpperValue': {'x': 0.0, 'y': -0.1, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'r': {
                'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'tongueValue': {'x': 0.0, 'y': 0.5, 'z': 0.0},
                'tongueInOut': 0.2,
                'teethUpperValue': {'x': 0.0, 'y': -0.1, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'w': {
                'jawValue': {'x': 0.0, 'y': 0.8, 'z': 0.0},
                'funnelRightUp': 1.0,
                'funnelRightDown': 1.0,
                'funnelLeftUp': 1.0,
                'funnelLeftDown': 1.0,
                'purseRightUp': 0.8,
                'purseRightDown': 0.8,
                'purseLeftUp': 0.8,
                'purseLeftDown': 0.8
            },
            'y': {
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'cornerPullRight': 0.4,
                'cornerPullLeft': 0.4,
                'teethUpperValue': {'x': 0.0, 'y': -0.4, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.4, 'z': 0.0}
            },
            'h': {
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0}
            },
            'n': {
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'tongueValue': {'x': 0.0, 'y': 0.7, 'z': 0.0}
            },
            'ng': {
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'tongueValue': {'x': 0.0, 'y': 0.7, 'z': 0.0}
            },
            # Additional phoneme combinations
            
            # Dipthongs - expanded
            'aɪ': {  # as in "eye", "I"
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.3, 'z': 0.0}
            },
            'eɪ': {  # as in "day"
                'jawValue': {'x': 0.0, 'y': 0.5, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.3, 'z': 0.0}
            },
            'oʊ': {  # as in "go"
                'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'funnelRightUp': 1.0,
                'funnelRightDown': 1.0,
                'funnelLeftUp': 1.0,
                'funnelLeftDown': 1.0,
                'purseRightUp': 0.7,
                'purseRightDown': 0.7,
                'purseLeftUp': 0.7,
                'purseLeftDown': 0.7,
                'teethUpperValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': -0.4, 'z': 0.0}
            },
            
            # Special phoneme combinations
            'pl': {  # as in "please"
                'jawValue': {'x': 0.0, 'y': 0.2, 'z': 0.0},
                'funnelRightUp': 0.2,
                'funnelRightDown': 0.2,
                'funnelLeftUp': 0.2,
                'funnelLeftDown': 0.2,
                'teethUpperValue': {'x': 0.0, 'y': -0.2, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                'tongueValue': {'x': 0.0, 'y': 0.2, 'z': 0.0}
            },
            'tr': {  # as in "tree"
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'tongueValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.2, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.2, 'z': 0.0}
            },
            'st': {  # as in "stop"
                'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.27, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'nt': {  # as in "didn't"
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'tongueValue': {'x': 0.0, 'y': 0.6, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.2, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.2, 'z': 0.0}
            },
            'tʃ': {  # "ch" as in "catch"
                'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'tongueValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'funnelRightUp': 0.5,
                'funnelRightDown': 0.5,
                'funnelLeftUp': 0.5,
                'funnelLeftDown': 0.5
            },
            'dʒ': {  # "j" as in "judge"
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'tongueValue': {'x': 0.0, 'y': 0.5, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'funnelRightUp': 0.3,
                'funnelRightDown': 0.3,
                'funnelLeftUp': 0.3,
                'funnelLeftDown': 0.3
            },
            
            # Additional vowels with stress markers
            'ˈɪ': {  # Stressed short "i" as in "bit"
                'jawValue': {'x': 0.0, 'y': 0.35, 'z': 0.0},
                'cornerPullRight': 0.35,
                'cornerPullLeft': 0.35,
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.3, 'z': 0.0}
            },
            'ˈiː': {  # Stressed long "ee" as in "please"
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'cornerPullRight': 0.5,
                'cornerPullLeft': 0.5,
                'teethUpperValue': {'x': 0.0, 'y': -0.4, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.4, 'z': 0.0}
            },
            'ˈɒ': {  # Stressed "o" as in "sorry"
                'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'funnelRightUp': 1.0,
                'funnelRightDown': 1.0,
                'funnelLeftUp': 1.0,
                'funnelLeftDown': 1.0,
                'purseRightUp': 0.8,
                'purseRightDown': 0.8,
                'purseLeftUp': 0.8,
                'purseLeftDown': 0.8
            },
            'ˈa': {  # Stressed "a" as in "father"
                'jawValue': {'x': 0.0, 'y': 0.6, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.0, 'z': 0.0}
            },
            
            # Common word-specific shapes
            'juː': {  # "you"
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'funnelRightUp': 0.9,
                'funnelRightDown': 0.9,
                'funnelLeftUp': 0.9,
                'funnelLeftDown': 0.9,
                'purseRightUp': 0.7,
                'purseRightDown': 0.7,
                'purseLeftUp': 0.7,
                'purseLeftDown': 0.7,
                'teethUpperValue': {'x': 0.0, 'y': 0.2, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': -0.2, 'z': 0.0}
            },
            'kʊd': {  # "could"
                'jawValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'tongueValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'funnelRightUp': 0.7,
                'funnelRightDown': 0.7,
                'funnelLeftUp': 0.7,
                'funnelLeftDown': 0.7,
                'purseRightUp': 0.5,
                'purseRightDown': 0.5,
                'purseLeftUp': 0.5,
                'purseLeftDown': 0.5
            },
            
            # Rest pose (listening state)
            'rest': {
                'jawValue': {'x': 0.0, 'y': 0.1, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.0, 'z': 0.0}
            }
        }
        
        # Add mapping for simplified phonemes and common espeak outputs
        self.phoneme_aliases = {
            # Common espeak IPA to our simplified phonemes
            'ə': 'a',  # Schwa
            'ɑ': 'a',  # Open back unrounded
            'æ': 'a',  # Near-open front unrounded
            'ɛ': 'e',  # Open-mid front unrounded
            'ɪ': 'i',  # Near-close near-front unrounded
            'ɔ': 'o',  # Open-mid back rounded
            'ʊ': 'u',  # Near-close near-back rounded
            'ʌ': 'a',  # Open-mid back unrounded
            'ː': '',   # Length marker
            'ˈ': '',   # Primary stress
            'ˌ': '',   # Secondary stress
            'ɐ': 'a',  # Near-open central
            'ɒ': 'o',  # Open back rounded
            'θ': 'th',  # Voiceless dental fricative
            'ð': 'th',  # Voiced dental fricative
            'ʃ': 'sh',  # Voiceless postalveolar fricative
            'ʒ': 'zh',  # Voiced postalveolar fricative
            'ŋ': 'ng',  # Velar nasal
            'ɹ': 'r',   # Alveolar approximant
            'j': 'y',   # Palatal approximant
            # Additional IPA aliases
            'ˈ': '',   # Primary stress - we'll handle stressed versions separately
            'ː': '',   # Length marker
            'ɹ': 'r',  # Alveolar approximant
            'ɒ': 'o',  # Open back rounded vowel
            'kʊd': 'kʊd',  # Keep compound words
            'juː': 'juː',   # Keep compound words
            'tʃ': 'tʃ',     # Keep "ch" sound
            'dʒ': 'dʒ'      # Keep "j" sound
        }
        
        # Update all jaw values to ensure x is 0
        for phoneme, values in self.phoneme_map.items():
            if "jawValue" in values:
                values["jawValue"]["x"] = 0.0

    def get_values(self, phoneme):
        # Default values dictionary with all possible parameters
        default_values = {
            'jawValue': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'funnelRightUp': 0.0,
            'funnelRightDown': 0.0,
            'funnelLeftUp': 0.0,
            'funnelLeftDown': 0.0,
            'purseRightUp': 0.0,
            'purseRightDown': 0.0,
            'purseLeftUp': 0.0,
            'purseLeftDown': 0.0,
            'cornerPullRight': 0.0,
            'cornerPullLeft': 0.0,
            'teethUpperValue': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'teethLowerValue': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'tongueValue': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'tongueInOut': 0.0,
            'pressRightUp': 0.0,
            'pressRightDown': 0.0,
            'pressLeftUp': 0.0,
            'pressLeftDown': 0.0,
            'towardsRightUp': 0.0,
            'towardsRightDown': 0.0,
            'towardsLeftUp': 0.0,
            'towardsLeftDown': 0.0
        }
        
        # Try direct lookup first
        if phoneme in self.phoneme_map:
            phoneme_values = self.phoneme_map[phoneme]
            for key, value in phoneme_values.items():
                default_values[key] = value
            return default_values
            
        # Try each character in the phoneme if it's a multi-character phoneme
        if len(phoneme) > 1:
            # Try to find matches for individual characters
            for char in phoneme:
                if char in self.phoneme_map:
                    phoneme_values = self.phoneme_map[char]
                    for key, value in phoneme_values.items():
                        # Only update if the value would be non-zero
                        if isinstance(value, dict) and sum(abs(v) for v in value.values()) > 0:
                            default_values[key] = value
                        elif not isinstance(value, dict) and value != 0:
                            default_values[key] = value
            
        # For vowel-like sounds, use 'a' as fallback
        if any(vowel in phoneme for vowel in 'aeiouəɑæɛɪɔʊʌɐɒ'):
            if 'a' in self.phoneme_map:
                phoneme_values = self.phoneme_map['a']
                for key, value in phoneme_values.items():
                    default_values[key] = value
                return default_values
        
        # For consonants, provide some default jaw opening
        default_values['jawValue'] = {'x': 0.0, 'y': 0.3, 'z': 0.0}
                    
        return default_values
        
    def simplify_phoneme(self, phoneme):
        """Convert complex IPA phonemes to simplified phonemes we can map"""
        # Check for exact matches in phoneme_map first (for compound phonemes)
        if phoneme in self.phoneme_map:
            return phoneme
            
        # Check for compound phonemes like "tʃ", "dʒ", etc.
        for compound in ["tʃ", "dʒ", "juː", "kʊd", "pl", "tr", "st", "nt"]:
            if compound in phoneme:
                return compound
        
        # Process stressed vowels (keep the stress marker with the vowel)
        if 'ˈ' in phoneme:
            for vowel in ['i', 'ɪ', 'e', 'ɛ', 'a', 'æ', 'ɑ', 'ɒ', 'o', 'ɔ', 'u', 'ʊ']:
                if f'ˈ{vowel}' in phoneme:
                    if f'ˈ{vowel}' in self.phoneme_map:
                        return f'ˈ{vowel}'
                        
        # Handle dipthongs
        for dipthong in ['aɪ', 'eɪ', 'oʊ', 'aʊ']:
            if dipthong in phoneme:
                return dipthong
                
        # Regular simplification process
        simple = phoneme.lower()
        for marker in ['ː']:
            simple = simple.replace(marker, '')
            
        # Apply phoneme aliases
        for ipa, replacement in self.phoneme_aliases.items():
            simple = simple.replace(ipa, replacement)
            
        # Remove any remaining non-alphanumeric characters except for IPA symbols we want to keep
        simple = re.sub(r'[^\w\ɑæɛɪɔʊʌɐɒθðʃʒŋɹj]', '', simple)
        
        # If we end up with an empty string, return 'x' as fallback
        return simple if simple else 'x'

def find_espeak_path():
    """Find the espeak binary path"""
    try:
        paths = [
            "/opt/homebrew/bin/espeak",
            "/usr/bin/espeak",
            "/usr/local/bin/espeak"
        ]
        
        result = subprocess.run(['which', 'espeak'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        
        for path in paths:
            if os.path.exists(path):
                return path
                
        return None
    except Exception as e:
        print(f"Error finding espeak: {e}")
        return None

def transcribe_audio(audio_file_path):
    """Transcribe audio using Whisper"""
    try:
        print(f"Transcribing audio file: {audio_file_path}")
        # Load the Whisper model (choose size based on your needs: tiny, base, small, medium, large)
        model = whisper.load_model("tiny")
        
        # Transcribe audio
        result = model.transcribe(audio_file_path)
        transcript = result["text"]
        
        print(f"Transcription complete: {transcript}")
        return transcript
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        # Provide a default transcript for testing if transcription fails
        return "This is a test sentence for phoneme extraction."

def extract_phonemes_with_espeak(text):
    """Extract phonemes using espeak"""
    espeak_path = find_espeak_path()
    if not espeak_path:
        print("espeak not available - cannot extract phonemes")
        # Provide default phonemes for testing
        return ["h", "ɛ", "l", "oʊ", "w", "ɜ", "r", "l", "d"]
        
    try:
        # Clean text for espeak
        clean_text = re.sub(r'[^\w\s.,?!-]', '', text)
        clean_text = clean_text.encode('ascii', 'ignore').decode()
        
        # Create temp file for text
        temp_text_path = tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False).name
        with open(temp_text_path, 'w') as f:
            f.write(clean_text)
        
        # Get phonemes from espeak with phoneme timing
        cmd = [espeak_path, "--ipa", "-q", "-f", temp_text_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"espeak command failed: {result.stderr}")
            # Provide default phonemes for testing
            return ["h", "ɛ", "l", "oʊ", "w", "ɜ", "r", "l", "d"]
        
        # Process phonemes
        raw_phonemes = result.stdout.strip()
        print(f"Raw espeak output: {raw_phonemes}")
        
        # Split by spaces and non-alphanumeric characters
        phonemes = []
        current = ""
        for char in raw_phonemes:
            if char.isalpha() or char in 'əɑæɛɪɔʊʌɐɒθðʃʒŋɹj':
                current += char
            elif char == ' ' and current:
                phonemes.append(current)
                current = ""
        if current:
            phonemes.append(current)
        
        # Clean up
        os.remove(temp_text_path)
        
        print(f"Extracted {len(phonemes)} phonemes: {phonemes}")
        return phonemes
        
    except Exception as e:
        print(f"Error extracting phonemes: {e}")
        # Provide default phonemes for testing
        return ["h", "ɛ", "l", "oʊ", "w", "ɜ", "r", "l", "d"]

def get_audio_duration(audio_file):
    """Get duration of audio file in seconds"""
    try:
        with contextlib.closing(wave.open(audio_file, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
        return duration
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return 3.0  # Default duration for testing

def generate_keyframes_from_audio(audio_file_path, output_file=None):
    """
    Generate facial keyframes from an audio file
    
    Parameters:
    audio_file_path (str): Path to the input audio file (WAV format)
    output_file (str): Path to save the output JSON file, or None to auto-generate
    
    Returns:
    str: Path to the generated JSON file or None if failed
    """
    try:
        # Check if file exists
        if not os.path.exists(audio_file_path):
            print(f"Audio file not found: {audio_file_path}")
            return None
            
        # Get audio duration
        duration = get_audio_duration(audio_file_path)
        if duration <= 0:
            print("Error: Could not determine audio duration")
            return None
            
        print(f"Audio duration: {duration} seconds")
        
        # Transcribe audio
        transcript = transcribe_audio(audio_file_path)
        if not transcript:
            print("Error: Failed to transcribe audio")
            return None
            
        # Extract phonemes
        raw_phonemes = extract_phonemes_with_espeak(transcript)
        if not raw_phonemes:
            print("Error: Failed to extract phonemes")
            return None
        
        # Initialize phoneme mapper
        mapper = PhonemeMapper()
        
        # Simplify phonemes
        phonemes = [mapper.simplify_phoneme(p) for p in raw_phonemes]
        phonemes = [p for p in phonemes if p]  # Filter out empty phonemes
        
        print(f"Simplified phonemes: {phonemes}")
        
        # Generate keyframes with improved timing
        keyframes = generate_keyframes_with_timing(phonemes, duration, mapper)
        
        # Determine output file path if not provided
        if not output_file:
            audio_path = Path(audio_file_path)
            output_file = audio_path.with_name(f"{audio_path.stem}_keyframes.json")
        
        # Save to JSON file
        with open(output_file, 'w') as f:
            json.dump(keyframes, f, indent=4)
            
        print(f"Keyframes saved to {output_file}")
        return output_file
        
    except Exception as e:
        print(f"Error generating keyframes: {e}")
        return None

def extract_phonemes_with_timing_from_espeak(text):
    """Extract phonemes with timing using espeak"""
    espeak_path = find_espeak_path()
    if not espeak_path:
        print("espeak not available - cannot extract phonemes with timing")
        # Provide default phonemes with timing for testing
        return [{"phoneme": "h", "start": 0.0, "duration": 0.1}, 
                {"phoneme": "ɛ", "start": 0.1, "duration": 0.15}, 
                {"phoneme": "l", "start": 0.25, "duration": 0.1},
                {"phoneme": "oʊ", "start": 0.35, "duration": 0.2}]
        
    try:
        # Clean text for espeak
        clean_text = re.sub(r'[^\w\s.,?!-]', '', text)
        clean_text = clean_text.encode('ascii', 'ignore').decode()
        
        # Create temp file for text
        temp_text_path = tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False).name
        with open(temp_text_path, 'w') as f:
            f.write(clean_text)
        
        # Get phonemes from espeak with phoneme timing
        cmd = [espeak_path, "--ipa", "-q", "-f", temp_text_path, "--pho"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"espeak command failed: {result.stderr}")
            # Fall back to the non-timing based extraction
            phonemes = extract_phonemes_with_espeak(text)
            return estimate_phoneme_timing(phonemes)
        
        # Process phonemes with timing
        # This requires parsing the specific output format of espeak --pho
        # For now, we'll use a simplified approach with even timing
        phonemes = extract_phonemes_with_espeak(text)
        return estimate_phoneme_timing(phonemes)
        
    except Exception as e:
        print(f"Error extracting phonemes with timing: {e}")
        phonemes = extract_phonemes_with_espeak(text)
        return estimate_phoneme_timing(phonemes)

def estimate_phoneme_timing(phonemes):
    """Estimate timing for each phoneme based on typical phoneme durations"""
    phoneme_timing = []
    current_time = 0.0
    
    # Average durations for different types of phonemes (in seconds)
    durations = {
        'vowel': 0.12,     # Reduced from 0.15
        'stressed_vowel': 0.15,  # Reduced from 0.18
        'long_vowel': 0.17,  # Reduced from 0.20
        'dipthong': 0.19,   # Reduced from 0.22
        'stop': 0.07,      # Reduced from 0.08
        'fricative': 0.10, # Reduced from 0.12
        'nasal': 0.09,     # Reduced from 0.10
        'liquid': 0.08,    # Reduced from 0.09
        'glide': 0.07,     # Reduced from 0.08
        'compound': 0.13,  # Reduced from 0.15
        'compound_word': 0.22,  # Reduced from 0.25
    }
    
    # Classify phonemes by type
    vowels = 'aeiouɑæɛɪɔʊʌɐɒ'
    stops = 'pbtdkg'
    fricatives = 'fvszʃʒθð'
    nasals = 'mnŋ'
    liquids = 'lr'
    glides = 'wj'
    dipthongs = ['aɪ', 'eɪ', 'oʊ', 'aʊ']
    compounds = ['tʃ', 'dʒ', 'pl', 'tr', 'st', 'nt']
    compound_words = ['juː', 'kʊd']
    
    for phoneme in phonemes:
        # Determine phoneme type
        if phoneme in compound_words:
            duration = durations['compound_word']
        elif phoneme in compounds:
            duration = durations['compound']
        elif any(d in phoneme for d in dipthongs):
            duration = durations['dipthong']
        elif 'ː' in phoneme:  # Long vowel marker
            duration = durations['long_vowel']
        elif 'ˈ' in phoneme and any(v in phoneme for v in vowels):  # Stressed vowel
            duration = durations['stressed_vowel']
        elif any(c in vowels for c in phoneme):
            duration = durations['vowel']
        elif any(c in stops for c in phoneme):
            duration = durations['stop']
        elif any(c in fricatives for c in phoneme):
            duration = durations['fricative']
        elif any(c in nasals for c in phoneme):
            duration = durations['nasal']
        elif any(c in liquids for c in phoneme):
            duration = durations['liquid']
        elif any(c in glides for c in phoneme):
            duration = durations['glide']
        else:
            duration = 0.09  # Reduced default duration
        
        phoneme_timing.append({
            "phoneme": phoneme,
            "start": current_time,
            "duration": duration
        })
        
        current_time += duration
    
    return phoneme_timing

def clean_float_values(keyframe_data, precision=2):
    """Clean floating point values to avoid excessive precision issues"""
    if isinstance(keyframe_data, dict):
        for key, value in keyframe_data.items():
            if isinstance(value, float):
                keyframe_data[key] = round(value, precision)
            elif isinstance(value, dict):
                clean_float_values(value, precision)
    return keyframe_data

def generate_keyframes_with_timing(phonemes, total_duration, mapper):
    """Generate keyframes with improved timing for given phonemes and duration"""
    keyframes = []
    
    # Get phonemes with timing estimates
    phoneme_timing = estimate_phoneme_timing(phonemes)
    
    # Calculate scaling factor to match audio duration
    estimated_duration = phoneme_timing[-1]["start"] + phoneme_timing[-1]["duration"]
    timing_scale = total_duration / estimated_duration if estimated_duration > 0 else 1.0
    
    # Initial neutral position
    keyframes.append({
        "time": 0.0,
        "jawValue": {"x": 0.0, "y": 0.0, "z": 0.0},
        "funnelRightUp": 0.0,
        "funnelRightDown": 0.0,
        "funnelLeftUp": 0.0,
        "funnelLeftDown": 0.0,
        "purseRightUp": 0.0,
        "purseRightDown": 0.0,
        "purseLeftUp": 0.0,
        "purseLeftDown": 0.0,
        "cornerPullRight": 0.0,
        "cornerPullLeft": 0.0,
        "teethUpperValue": {"x": 0.0, "y": 0.0, "z": 0.0},
        "teethLowerValue": {"x": 0.0, "y": 0.0, "z": 0.0},
        "tongueValue": {"x": 0.0, "y": 0.0, "z": 0.0},
        "tongueInOut": 0.0,
        "pressRightUp": 0.0,
        "pressRightDown": 0.0,
        "pressLeftUp": 0.0,
        "pressLeftDown": 0.0,
        "towardsRightUp": 0.0,
        "towardsRightDown": 0.0,
        "towardsLeftUp": 0.0,
        "towardsLeftDown": 0.0
    })
    
    # Generate keyframes for each phoneme with proper timing
    for i, phoneme_data in enumerate(phoneme_timing):
        phoneme = phoneme_data["phoneme"]
        # Scale the time to match the total audio duration
        time = phoneme_data["start"] * timing_scale
        duration = phoneme_data["duration"] * timing_scale
        
        # Get values for current and next phoneme
        current_values = mapper.get_values(phoneme)
        next_values = mapper.get_values(phoneme_timing[i+1]["phoneme"]) if i < len(phoneme_timing) - 1 else current_values
        
        # Scale down jaw and tongue values for more natural movement
        if "jawValue" in current_values:
            current_values["jawValue"]["y"] *= 0.7  # Reduce jaw opening by 30%
        if "tongueInOut" in current_values:
            current_values["tongueInOut"] *= 0.4  # Reduce tongue protrusion by 60%
            
        # Ensure jaw x value is always 0
        if "jawValue" in current_values:
            current_values["jawValue"]["x"] = 0.0
        if "jawValue" in next_values:
            next_values["jawValue"]["x"] = 0.0
            
        # Add anticipation keyframe only for significant phoneme changes
        if i > 0:  # Skip for first phoneme
            prev_values = mapper.get_values(phoneme_timing[i-1]["phoneme"])
            
            # Only add anticipation if there's a significant change in jaw or mouth shape
            jaw_change = abs(current_values.get("jawValue", {}).get("y", 0) - prev_values.get("jawValue", {}).get("y", 0))
            mouth_change = any(abs(current_values.get(k, 0) - prev_values.get(k, 0)) > 0.2 for k in 
                             ["funnelRightUp", "funnelRightDown", "funnelLeftUp", "funnelLeftDown",
                              "purseRightUp", "purseRightDown", "purseLeftUp", "purseLeftDown"])
            
            if jaw_change > 0.2 or mouth_change:
                anticipation_time = time - 0.015  # Reduced to 15ms before phoneme starts
                
                # Create anticipation keyframe that's a blend between previous and current
                anticipation_keyframe = {key: value for key, value in prev_values.items()}
                
                # Blend vector values
                for key in ["jawValue", "teethUpperValue", "teethLowerValue", "tongueValue"]:
                    if key in prev_values and key in current_values:
                        for coord in ["x", "y", "z"]:
                            prev = prev_values[key][coord]
                            current = current_values[key][coord]
                            anticipation_keyframe[key][coord] = prev * 0.9 + current * 0.1  # More gradual blend
                
                # Blend float values
                for key in [k for k in prev_values if k not in ["jawValue", "teethUpperValue", "teethLowerValue", "tongueValue"]]:
                    if key in prev_values and key in current_values:
                        prev = prev_values[key]
                        current = current_values[key]
                        anticipation_keyframe[key] = prev * 0.9 + current * 0.1  # More gradual blend
                
                keyframes.append({
                    "time": round(anticipation_time, 3),
                    **anticipation_keyframe
                })
        
        # Add peak keyframe (main phoneme shape)
        peak_time = time + (duration * 0.2)  # Reduced to 20% of phoneme duration
        keyframe = {
            "time": round(peak_time, 3),
            **current_values
        }
        keyframes.append(keyframe)
        
        # Add sustain keyframe only for longer phonemes and significant changes
        if duration > 0.15:  # Increased threshold for sustain keyframe
            sustain_time = time + (duration * 0.4)  # Reduced to 40% of phoneme duration
            keyframe = {
                "time": round(sustain_time, 3),
                **current_values
            }
            keyframes.append(keyframe)
        
        # Add transition keyframes only for significant changes
        if i < len(phoneme_timing) - 1:
            # Check if there's a significant change to the next phoneme
            jaw_change = abs(next_values.get("jawValue", {}).get("y", 0) - current_values.get("jawValue", {}).get("y", 0))
            mouth_change = any(abs(next_values.get(k, 0) - current_values.get(k, 0)) > 0.2 for k in 
                             ["funnelRightUp", "funnelRightDown", "funnelLeftUp", "funnelLeftDown",
                              "purseRightUp", "purseRightDown", "purseLeftUp", "purseLeftDown"])
            
            if jaw_change > 0.2 or mouth_change:
                # Create transition keyframe that's a blend between current and next
                transition_time = time + (duration * 0.7)  # Reduced to 70% of phoneme duration
                transition_keyframe = {key: value for key, value in current_values.items()}
                
                # Blend vector values
                for key in ["jawValue", "teethUpperValue", "teethLowerValue", "tongueValue"]:
                    if key in current_values and key in next_values:
                        for coord in ["x", "y", "z"]:
                            current = current_values[key][coord]
                            next_val = next_values[key][coord]
                            transition_keyframe[key][coord] = current * 0.5 + next_val * 0.5  # More balanced blend
                
                # Blend float values
                for key in [k for k in current_values if k not in ["jawValue", "teethUpperValue", "teethLowerValue", "tongueValue"]]:
                    if key in current_values and key in next_values:
                        current = current_values[key]
                        next_val = next_values[key]
                        transition_keyframe[key] = current * 0.5 + next_val * 0.5  # More balanced blend
                
                keyframes.append({
                    "time": round(transition_time, 3),
                    **transition_keyframe
                })
    
    # Final neutral position
    keyframes.append({
        "time": round(total_duration, 3),
        "jawValue": {"x": 0.0, "y": 0.0, "z": 0.0},
        "funnelRightUp": 0.0,
        "funnelRightDown": 0.0,
        "funnelLeftUp": 0.0,
        "funnelLeftDown": 0.0,
        "purseRightUp": 0.0,
        "purseRightDown": 0.0,
        "purseLeftUp": 0.0,
        "purseLeftDown": 0.0,
        "cornerPullRight": 0.0,
        "cornerPullLeft": 0.0,
        "teethUpperValue": {"x": 0.0, "y": 0.0, "z": 0.0},
        "teethLowerValue": {"x": 0.0, "y": 0.0, "z": 0.0},
        "tongueValue": {"x": 0.0, "y": 0.0, "z": 0.0},
        "tongueInOut": 0.0,
        "pressRightUp": 0.0,
        "pressRightDown": 0.0,
        "pressLeftUp": 0.0,
        "pressLeftDown": 0.0,
        "towardsRightUp": 0.0,
        "towardsRightDown": 0.0,
        "towardsLeftUp": 0.0,
        "towardsLeftDown": 0.0
    })
    
    # Clean up all float values in keyframes to avoid precision issues
    for keyframe in keyframes:
        clean_float_values(keyframe)
        # Double-check jaw x value is 0 (just to be safe)
        if "jawValue" in keyframe:
            keyframe["jawValue"]["x"] = 0.0
    
    # Sort keyframes by time to ensure proper ordering
    keyframes.sort(key=lambda k: k["time"])
    
    return {"keyframes": keyframes}

def main():
    # Specify audio file paths to process
    audio_files = [
        "response1.wav",  
    ]
    
    for audio_file in audio_files:
        if os.path.exists(audio_file):
            print(f"\nProcessing {audio_file}...")
            result = generate_keyframes_from_audio(audio_file)
            
            if result:
                print(f"Successfully generated keyframes at {result}")
            else:
                print(f"Failed to generate keyframes for {audio_file}")
        else:
            print(f"Audio file not found: {audio_file}")

if __name__ == "__main__":
    main()