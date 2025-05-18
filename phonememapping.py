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
import traceback
from gtts import gTTS
from pathlib import Path
import random

try:
    import nltk
    from nltk.corpus import cmudict
    
    # Download required NLTK resources if not already present
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("Downloading NLTK punkt resource...")
        nltk.download('punkt', quiet=True)
        
    try:
        nltk.data.find('corpora/cmudict')
    except LookupError:
        print("Downloading NLTK cmudict resource...")
        nltk.download('cmudict', quiet=True)
        
    NLTK_AVAILABLE = True
except ImportError:
    print("[WARNING] nltk not found. Syllable-aware phoneme mapping disabled.")
    NLTK_AVAILABLE = False

class PhonemeMapper:
    def __init__(self):
        # Initialize comprehensive phoneme mapping (without jaw values - they will be derived from audio)
        self.phoneme_map = {
            # Vowels - Calibrated for facial expressions only (no jaw)
            'a': {
                'teethUpperValue': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.0, 'z': 0.0}
            },
            'ɑ': {
                'teethUpperValue': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.0, 'z': 0.0}
            },
            'e': {
                'teethUpperValue': {'x': 0.0, 'y': -0.2, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.2, 'z': 0.0}
            },
            'ɛ': {
                'cornerPullRight': 0.2,
                'cornerPullLeft': 0.2,
                'teethUpperValue': {'x': 0.0, 'y': -0.2, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.2, 'z': 0.0}
            },
            'i': {
                'teethUpperValue': {'x': 0.0, 'y': -0.1, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'ɪ': {
                'cornerPullRight': 0.4,
                'cornerPullLeft': 0.4,
                'teethUpperValue': {'x': 0.0, 'y': -0.4, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.4, 'z': 0.0}
            },
            'o': {
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
                'purseRightUp': 0.2,
                'purseRightDown': 0.2,
                'purseLeftUp': 0.2,
                'purseLeftDown': 0.2,
                'teethUpperValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': -0.4, 'z': 0.0}
            },
            'ay': {
                'cornerPullRight': 0.4,
                'cornerPullLeft': 0.4,
                'teethUpperValue': {'x': 0.0, 'y': -0.4, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.4, 'z': 0.0}
            },
            'b': {
                'teethLowerValue': {'x': 0.0, 'y': -0.2, 'z': 0.0}
            },
            'p': {
                'teethLowerValue': {'x': 0.0, 'y': -0.2, 'z': 0.0}
            },
            'm': {
                'teethLowerValue': {'x': 0.0, 'y': -0.2, 'z': 0.0}
            },
            'f': {
                'funnelRightUp': 0.8,
                'funnelRightDown': 0.8,
                'funnelLeftUp': 0.8,
                'funnelLeftDown': 0.8,
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0}
            },
            'v': {
                'funnelRightUp': 0.8,
                'funnelRightDown': 0.8,
                'funnelLeftUp': 0.8,
                'funnelLeftDown': 0.8,
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0}
            },
            'th': {
                'tongueInOut': -0.3,
                'teethUpperValue': {'x': 0.0, 'y': -0.2, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'ð': {
                'tongueInOut': -0.3,
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'θ': {
                'tongueInOut': -0.3,
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            's': {
                'teethUpperValue': {'x': 0.0, 'y': -0.27, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'z': {
                'teethUpperValue': {'x': 0.0, 'y': -0.27, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'sh': {
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'funnelRightUp': 0.4,
                'funnelRightDown': 0.4,
                'funnelLeftUp': 0.4,
                'funnelLeftDown': 0.4
            },
            'ʃ': {
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'funnelRightUp': 0.4,
                'funnelRightDown': 0.4,
                'funnelLeftUp': 0.4,
                'funnelLeftDown': 0.4
            },
            't': {
                'tongueValue': {'x': 0.0, 'y': 0.5, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.2, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.2, 'z': 0.0}
            },
            'd': {
                'tongueValue': {'x': 0.0, 'y': 0.5, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.2, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.2, 'z': 0.0}
            },
            'k': {
                'tongueValue': {'x': 0.0, 'y': 0.5, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.1, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'g': {
                'tongueValue': {'x': 0.0, 'y': 0.5, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.1, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'l': {
                'tongueValue': {'x': 0.0, 'y': 0.5, 'z': 0.0},
                'tongueInOut': 0.5,
                'teethUpperValue': {'x': 0.0, 'y': -0.1, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'r': {
                'tongueValue': {'x': 0.0, 'y': 0.5, 'z': 0.0},
                'tongueInOut': 0.2,
                'teethUpperValue': {'x': 0.0, 'y': -0.1, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'w': {
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
                'cornerPullRight': 0.4,
                'cornerPullLeft': 0.4,
                'teethUpperValue': {'x': 0.0, 'y': -0.4, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.4, 'z': 0.0}
            },
            'h': {
                'teethUpperValue': {'x': 0.0, 'y': -0.1, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'n': {
                'tongueValue': {'x': 0.0, 'y': 0.7, 'z': 0.0}
            },
            'ng': {
                'tongueValue': {'x': 0.0, 'y': 0.7, 'z': 0.0}
            },
            
            # Dipthongs - expanded
            'aɪ': {  # as in "eye", "I"
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.3, 'z': 0.0}
            },
            'eɪ': {  # as in "day"
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.3, 'z': 0.0}
            },
            'oʊ': {  # as in "go"
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
                'funnelRightUp': 0.2,
                'funnelRightDown': 0.2,
                'funnelLeftUp': 0.2,
                'funnelLeftDown': 0.2,
                'teethUpperValue': {'x': 0.0, 'y': -0.2, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                'tongueValue': {'x': 0.0, 'y': 0.2, 'z': 0.0}
            },
            'tr': {  # as in "tree"
                'tongueValue': {'x': 0.0, 'y': 0.4, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.2, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.2, 'z': 0.0}
            },
            'st': {  # as in "stop"
                'teethUpperValue': {'x': 0.0, 'y': -0.27, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.1, 'z': 0.0}
            },
            'nt': {  # as in "didn't"
                'tongueValue': {'x': 0.0, 'y': 0.6, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.2, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.2, 'z': 0.0}
            },
            'tʃ': {  # "ch" as in "catch"
                'tongueValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.3, 'z': 0.0},
                'funnelRightUp': 0.5,
                'funnelRightDown': 0.5,
                'funnelLeftUp': 0.5,
                'funnelLeftDown': 0.5
            },
            'dʒ': {  # "j" as in "judge"
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
                'cornerPullRight': 0.35,
                'cornerPullLeft': 0.35,
                'teethUpperValue': {'x': 0.0, 'y': -0.3, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.3, 'z': 0.0}
            },
            'ˈiː': {  # Stressed long "ee" as in "please"
                'cornerPullRight': 0.5,
                'cornerPullLeft': 0.5,
                'teethUpperValue': {'x': 0.0, 'y': -0.4, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.4, 'z': 0.0}
            },
            'ˈɒ': {  # Stressed "o" as in "sorry"
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
                'teethUpperValue': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.0, 'z': 0.0}
            },
            
            # Common word-specific shapes
            'juː': {  # "you"
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
            
            # Rest pose - Critical for natural transitions
            'rest': {
                'teethUpperValue': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                'teethLowerValue': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                'cornerPullRight': 0.0,
                'cornerPullLeft': 0.0,
                'funnelRightUp': 0.0,
                'funnelRightDown': 0.0,
                'funnelLeftUp': 0.0,
                'funnelLeftDown': 0.0,
                'purseRightUp': 0.0,
                'purseRightDown': 0.0,
                'purseLeftUp': 0.0,
                'purseLeftDown': 0.0,
                'tongueValue': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                'tongueInOut': 0.0
            }
        }
        
        # Keep the existing phoneme aliases
        self.phoneme_aliases = {
            'ə': 'a',  # Schwa sounds map to 'a'
            'ɑ': 'a',  # Open back unrounded
            'æ': 'a',  # Near-open front unrounded
            'ɛ': 'e',  # Open-mid front unrounded
            'ɪ': 'i',  # Near-close near-front unrounded
            'ɔ': 'o',  # Open-mid back rounded
            'ʊ': 'u',  # Near-close near-back rounded
            'ʌ': 'a',  # Open-mid back unrounded
            'ː': '',   # Length marker (remove)
            'ˈ': '',   # Primary stress (remove)
            'ˌ': '',   # Secondary stress (remove)
            'ɐ': 'a',  # Near-open central
            'ɒ': 'o',  # Open back rounded
            'θ': 'th', # Voiceless dental fricative
            'ð': 'th', # Voiced dental fricative
            'ʃ': 'sh', # Voiceless postalveolar fricative
            'ʒ': 'zh', # Voiced postalveolar fricative
            'ŋ': 'ng', # Velar nasal
            'ɹ': 'r',  # Alveolar approximant
            'j': 'y'   # Palatal approximant
        }
        
        # Ensure all jaw values have x=0 for consistent movement
        for phoneme, values in self.phoneme_map.items():
            if "jawValue" in values:
                values["jawValue"]["x"] = 0.0

    def get_values(self, phoneme):
        # Default values dictionary with all possible parameters EXCEPT jawValue
        default_values = {
            # jawValue removed from default values - will be handled separately
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
            
        # Enhanced multi-character phoneme handling
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
            
        # Improved fallback for vowel-like sounds
        if any(vowel in phoneme for vowel in 'aeiouəɑæɛɪɔʊʌɐɒθðʃʒŋɹj'):
            if 'a' in self.phoneme_map:
                phoneme_values = self.phoneme_map['a']
                for key, value in phoneme_values.items():
                    default_values[key] = value
                return default_values
        
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

class SyllablePhonemeMapper:
    """
    Enhanced mapper that provides syllable-aware phoneme mapping for more
    realistic facial animations beyond just jaw movements.
    """
    
    def __init__(self):
        # Initialize the base phoneme mapper
        self.phoneme_mapper = PhonemeMapper()
        
        # Load CMU dictionary for syllable decomposition
        self.cmu_dict = cmudict.dict() if cmudict.dict() else {}
        
        # Cache for syllabified words
        self.syllable_cache = {}
        
        # Vowel phonemes (used for syllable detection)
        self.vowel_phonemes = set(['AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 
                                  'ER', 'EY', 'IH', 'IY', 'OW', 'OY', 'UH', 'UW'])
        
        # Mapping from CMU phonemes to our phoneme set
        self.cmu_to_phoneme = {
            'AA': 'a', 'AE': 'æ', 'AH': 'ə', 'AO': 'ɔ',
            'AW': 'aw', 'AY': 'ay', 'EH': 'ɛ', 'ER': 'ər',
            'EY': 'eɪ', 'IH': 'ɪ', 'IY': 'i', 'OW': 'oʊ',
            'OY': 'ɔɪ', 'UH': 'ʊ', 'UW': 'u',
            'B': 'b', 'CH': 'tʃ', 'D': 'd', 'DH': 'ð',
            'F': 'f', 'G': 'g', 'HH': 'h', 'JH': 'dʒ',
            'K': 'k', 'L': 'l', 'M': 'm', 'N': 'n',
            'NG': 'ŋ', 'P': 'p', 'R': 'r', 'S': 's',
            'SH': 'ʃ', 'T': 't', 'TH': 'θ', 'V': 'v',
            'W': 'w', 'Y': 'y', 'Z': 'z', 'ZH': 'ʒ'
        }
    
    def word_to_syllables(self, word):
        """
        Split a word into syllables using CMU dictionary.
        
        Args:
            word (str): The word to syllabify
            
        Returns:
            list: List of syllables with their phoneme sequences
        """
        # Check cache first
        word = word.lower().strip()
        if word in self.syllable_cache:
            return self.syllable_cache[word]
            
        # Not in cache, process it
        if word in self.cmu_dict:
            # Get the first pronunciation (most common)
            phonemes = self.cmu_dict[word][0]
            
            # Remove stress markers (numbers) from phonemes
            clean_phonemes = [re.sub(r'\d+', '', p) for p in phonemes]
            
            # Identify syllables based on vowel sounds
            syllables = []
            current_syllable = []
            
            for phoneme in clean_phonemes:
                current_syllable.append(phoneme)
                # If this is a vowel phoneme, it's the nucleus of a syllable
                if phoneme in self.vowel_phonemes:
                    # Look ahead to decide where to break the syllable
                    if len(current_syllable) > 1:
                        syllables.append(current_syllable)
                        current_syllable = []
            
            # Add any remaining phonemes to the last syllable
            if current_syllable:
                if syllables:
                    syllables[-1].extend(current_syllable)
                else:
                    syllables.append(current_syllable)
            
            # Map CMU phonemes to our phoneme set
            mapped_syllables = []
            for syllable in syllables:
                mapped = [self.cmu_to_phoneme.get(p, p) for p in syllable]
                mapped_syllables.append(mapped)
            
            self.syllable_cache[word] = mapped_syllables
            return mapped_syllables
        else:
            # Fallback: just treat each character as a potential phoneme
            # This is a very naive approach but serves as a fallback
            return [[char] for char in word if char.isalpha()]
    
    def text_to_syllable_phonemes(self, text):
        """
        Convert a text string to syllable-phoneme sequences.
        
        Args:
            text (str): Input text
            
        Returns:
            list: List of words with their syllable-phoneme mappings
        """
        # Simple tokenization instead of using nltk.word_tokenize
        # Split by spaces and remove punctuation
        words = []
        for word in text.split():
            # Remove punctuation
            clean_word = ''.join(c for c in word if c.isalpha() or c == "'")
            if clean_word:
                words.append(clean_word)
        
        # Process each word into syllables
        word_syllables = []
        for word in words:
            if word.isalpha():  # Skip punctuation
                syllables = self.word_to_syllables(word)
                word_syllables.append({
                    'word': word,
                    'syllables': syllables
                })
        
        return word_syllables
    
    def distribute_word_timing(self, word_data, start_time, duration):
        """
        Distribute timing information for a word across its syllables.
        
        Args:
            word_data (dict): Word with syllable information
            start_time (float): Start time of the word
            duration (float): Duration of the word
            
        Returns:
            list: List of syllables with timing information
        """
        word = word_data['word']
        syllables = word_data['syllables']
        
        num_syllables = len(syllables)
        
        # Equal distribution (could be improved with more sophisticated models)
        syllable_duration = duration / num_syllables
        
        timed_syllables = []
        for i, syllable in enumerate(syllables):
            syllable_start = start_time + (i * syllable_duration)
            
            # Create timing data for this syllable
            timed_syllables.append({
                'word': word,  # Add word information for debugging
                'syllable_index': i,  # Which syllable in the word
                'syllable_count': num_syllables,  # Total syllables in word
                'phonemes': syllable,
                'start': syllable_start,
                'duration': syllable_duration
            })
        
        return timed_syllables
    
    def align_phonemes_to_syllables(self, transcript, speech_segments, duration):
        """
        Align phonemes to syllables based on speech segments.
        
        Args:
            transcript (str): Transcribed text
            speech_segments (list): List of speech segments with timing
            duration (float): Total duration of the audio
            
        Returns:
            list: List of syllable-based phoneme timings
        """
        # Get syllable-phoneme mappings for the transcript
        word_syllables = self.text_to_syllable_phonemes(transcript)
        
        # Total syllable count for distribution across speech segments
        total_syllables = sum(len(word['syllables']) for word in word_syllables)
        
        if not speech_segments or not word_syllables:
            return []
        
        # Distribute words across speech segments
        # This is a simplified approach - more sophisticated alignment would use
        # forced alignment techniques
        
        # First, get total speech duration from segments
        total_speech_duration = sum(seg['end'] - seg['start'] for seg in speech_segments)
        
        # Calculate average syllable duration
        avg_syllable_duration = total_speech_duration / total_syllables if total_syllables > 0 else 0.1
        
        # Distribute syllables across speech segments
        syllable_timings = []
        syllable_index = 0
        word_index = 0
        
        for segment in speech_segments:
            segment_duration = segment['end'] - segment['start']
            segment_start = segment['start']
            
            # Estimate number of syllables in this segment
            segment_syllable_count = int(round(segment_duration / avg_syllable_duration))
            
            syllables_processed = 0
            current_time = segment_start
            
            # Process words until we've assigned enough syllables for this segment
            while syllables_processed < segment_syllable_count and word_index < len(word_syllables):
                current_word = word_syllables[word_index]
                word_syllable_count = len(current_word['syllables'])
                
                # Calculate word duration proportionally
                word_duration = word_syllable_count * avg_syllable_duration
                
                # Distribute timing for this word's syllables
                word_syllable_timings = self.distribute_word_timing(
                    current_word, 
                    current_time, 
                    word_duration
                )
                
                # Add to our syllable timings list
                syllable_timings.extend(word_syllable_timings)
                
                # Update trackers
                syllables_processed += word_syllable_count
                current_time += word_duration
                word_index += 1
                
                # If we've processed too many syllables for this segment,
                # adjust the timing of the last word
                if syllables_processed > segment_syllable_count:
                    excess = syllables_processed - segment_syllable_count
                    # Simply adjust the end time to match segment end
                    for timing in word_syllable_timings[-excess:]:
                        # Shrink duration to fit within segment
                        scale_factor = (segment['end'] - timing['start']) / timing['duration']
                        if scale_factor < 1.0:
                            timing['duration'] *= scale_factor
            
        return syllable_timings
    
    def generate_keyframes_from_syllables(self, syllable_timings, jaw_keyframes):
        """
        Generate facial animation keyframes based on syllable-phoneme mappings,
        combined with jaw movement data from audio amplitude analysis.
        
        Args:
            syllable_timings (list): List of syllables with timing information
            jaw_keyframes (list): Jaw keyframes from audio amplitude analysis
            
        Returns:
            list: Complete facial animation keyframes
        """
        # Create a mapping of times to jaw values from jaw_keyframes
        jaw_time_map = {kf['time']: kf['jawValue'] for kf in jaw_keyframes}
        jaw_times = sorted(jaw_time_map.keys())
        
        # Generate keyframes for each syllable
        keyframes = []
        
        for syllable in syllable_timings:
            phonemes = syllable['phonemes']
            start_time = syllable['start']
            duration = syllable['duration']
            word = syllable['word']
            syllable_index = syllable['syllable_index']
            syllable_count = syllable['syllable_count']
            
            # Create syllable text representation
            if syllable_count == 1:
                # Single syllable word
                syllable_text = word
            else:
                # Multi-syllable word - include which syllable it is
                syllable_text = f"{word}_{syllable_index+1}of{syllable_count}"
            
            # Calculate keyframe timings for this syllable
            # Each phoneme gets positioned strategically within the syllable
            phoneme_count = len(phonemes)
            
            # Emphasize the middle of the syllable - typically the vowel
            if phoneme_count == 1:
                # Only one phoneme in syllable - place keyframe at peak (40% through)
                keyframe_times = [start_time + (duration * 0.4)]
            else:
                # Multiple phonemes - distribute with more emphasis on early-middle
                keyframe_times = []
                for i in range(phoneme_count):
                    # Position keyframes with emphasis on vowel position (typically in middle)
                    if phoneme_count <= 2:
                        # For 2 phonemes, position at 30% and 70%
                        pos = 0.3 + (0.4 * (i / max(1, phoneme_count - 1)))
                    else:
                        # For 3+ phonemes, distribute with emphasis on middle
                        pos = 0.2 + (0.6 * (i / max(1, phoneme_count - 1)))
                    
                    keyframe_times.append(start_time + (duration * pos))
            
            # Generate keyframes for each phoneme in the syllable
            for i, phoneme in enumerate(phonemes):
                time = keyframe_times[min(i, len(keyframe_times) - 1)]
                
                # Find the closest jaw keyframe time
                closest_jaw_time = min(jaw_times, key=lambda x: abs(x - time))
                jaw_value = jaw_time_map[closest_jaw_time]
                
                # Get facial values for this phoneme from PhonemeMapper
                if isinstance(phoneme, list):
                    # Handle case where phoneme is a list
                    phoneme_str = phoneme[0]  # Just use the first one
                else:
                    phoneme_str = phoneme
                
                facial_values = self.phoneme_mapper.get_values(phoneme_str)
                
                # Create keyframe with jaw value from audio and all other values from phoneme
                keyframe = {
                    'time': round(time, 3),
                    'word': word,
                    'syllable': syllable_text,
                    'phoneme': phoneme_str if isinstance(phoneme_str, str) else str(phoneme_str),
                    'jawValue': jaw_value  # Use jaw movement from audio analysis
                }
                
                # Add all other facial values from phoneme mapping
                for key, value in facial_values.items():
                    if key != 'jawValue':  # Skip jaw as we're using the audio-derived one
                        keyframe[key] = value
                
                keyframes.append(keyframe)
            
            # Add a transition keyframe at the end of the syllable (for smoothing)
            end_time = start_time + duration
            
            # Find the closest jaw keyframe for the end transition
            closest_jaw_time = min(jaw_times, key=lambda x: abs(x - end_time))
            jaw_value = jaw_time_map[closest_jaw_time]
            
            # Add a subtle transition keyframe with reduced values
            transition_keyframe = {
                'time': round(end_time - (duration * 0.1), 3),  # Slightly before end
                'word': word,
                'syllable': syllable_text + "_transition",
                'phoneme': "transition",
                'jawValue': jaw_value  # Use jaw movement from audio analysis
            }
            
            # Add all other facial values from phoneme mapping but reduced
            last_phoneme = phonemes[-1]
            if isinstance(last_phoneme, list):
                last_phoneme = last_phoneme[0]
                
            facial_values = self.phoneme_mapper.get_values(last_phoneme)
            
            for key, value in facial_values.items():
                if key != 'jawValue':
                    if isinstance(value, dict):
                        # Handle vector values like teethUpperValue
                        reduced_value = {k: v * 0.7 for k, v in value.items()}
                        transition_keyframe[key] = reduced_value
                    else:
                        # Handle scalar values
                        transition_keyframe[key] = value * 0.7
            
            keyframes.append(transition_keyframe)
        
        # Sort keyframes by time
        keyframes.sort(key=lambda k: k['time'])
        
        # Filter out any duplicate times
        unique_keyframes = []
        seen_times = set()
        
        for kf in keyframes:
            time = kf['time']
            if time not in seen_times:
                seen_times.add(time)
                unique_keyframes.append(kf)
        
        return unique_keyframes
    
    def smooth_keyframes(self, keyframes, window_size=3):
        """
        Apply smoothing to keyframes to ensure natural transitions
        
        Args:
            keyframes (list): Raw keyframes
            window_size (int): Smoothing window size
            
        Returns:
            list: Smoothed keyframes
        """
        if not keyframes or len(keyframes) <= window_size:
            return keyframes
        
        smoothed = []
        
        # Keep the first and last keyframes unchanged
        smoothed.append(keyframes[0])
        
        # Apply smoothing to middle keyframes
        for i in range(1, len(keyframes) - 1):
            # Determine window boundaries
            start = max(0, i - window_size//2)
            end = min(len(keyframes), i + window_size//2 + 1)
            window = keyframes[start:end]
            
            # Create smoothed keyframe with metadata preserved
            smoothed_kf = {
                'time': keyframes[i]['time'],
                'word': keyframes[i].get('word', ''),
                'syllable': keyframes[i].get('syllable', ''),
                'phoneme': keyframes[i].get('phoneme', '')
            }
            
            # Process each attribute
            for key in keyframes[i]:
                if key in ['time', 'word', 'syllable', 'phoneme']:
                    continue
                
                if isinstance(keyframes[i][key], dict):
                    # Handle vector values (like jawValue)
                    smoothed_kf[key] = {}
                    for coord in keyframes[i][key]:
                        values = [kf.get(key, {}).get(coord, 0) for kf in window if key in kf]
                        if values:
                            smoothed_kf[key][coord] = round(sum(values) / len(values), 3)
                        else:
                            smoothed_kf[key][coord] = keyframes[i][key][coord]
                else:
                    # Handle scalar values
                    values = [kf.get(key, 0) for kf in window if key in kf]
                    if values:
                        smoothed_kf[key] = round(sum(values) / len(values), 3)
                    else:
                        smoothed_kf[key] = keyframes[i][key]
            
            smoothed.append(smoothed_kf)
        
        # Add the last keyframe
        smoothed.append(keyframes[-1])
        
        return smoothed
    
    def process_audio_to_syllable_phonemes(self, transcript, speech_segments, jaw_keyframes, duration):
        """
        Process audio transcript to generate syllable-aware phoneme keyframes
        
        Args:
            transcript (str): Transcribed text
            speech_segments (list): Speech segments with timing
            jaw_keyframes (list): Jaw keyframes from audio amplitude
            duration (float): Audio duration
            
        Returns:
            list: Enhanced keyframes with syllable-aware phoneme mapping
        """
        # Align phonemes to syllables with timing
        syllable_timings = self.align_phonemes_to_syllables(transcript, speech_segments, duration)
        
        # Generate keyframes based on syllable-phoneme mapping and jaw data
        keyframes = self.generate_keyframes_from_syllables(syllable_timings, jaw_keyframes)
        
        return keyframes

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
        model = whisper.load_model("tiny")
        result = model.transcribe(audio_file_path)
        transcript = result["text"]
        print(f"Transcription complete: {transcript}")
        return transcript
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return "This is a test sentence for phoneme extraction."

def extract_phonemes_with_espeak(text):
    """Extract phonemes using espeak"""
    espeak_path = find_espeak_path()
    if not espeak_path:
        print("[ERROR] espeak not found")
        return None
        
    try:
        # Clean text for espeak
        clean_text = re.sub(r'[^\w\s.,?!-]', '', text)
        clean_text = clean_text.encode('ascii', 'ignore').decode()
        
        # Create temp file for text
        temp_text_path = tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False).name
        with open(temp_text_path, 'w') as f:
            f.write(clean_text)
        
        # Get phonemes from espeak
        cmd = [espeak_path, "--ipa", "-q", "-f", temp_text_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"[ERROR] espeak command failed: {result.stderr}")
            return None
        
        # Process phonemes
        raw_phonemes = result.stdout.strip()
        print(f"[INFO] Raw espeak output: {raw_phonemes}")
        
        # Split into individual phonemes
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
        
        print(f"[INFO] Extracted {len(phonemes)} phonemes: {phonemes}")
        return phonemes
        
    except Exception as e:
        print(f"[ERROR] Failed to extract phonemes: {str(e)}")
        traceback.print_exc()
        return None

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

def normalize_audio(input_file):
    """Normalize audio using ffmpeg for consistent analysis"""
    try:
        output_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
        
        # Run ffmpeg normalization
        subprocess.run([
            'ffmpeg',
            '-y',  # Overwrite output file
            '-i', input_file,
            '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',  # Industry standard normalization
            '-ar', '22050',  # Consistent sample rate
            '-ac', '1',      # Mono audio
            '-acodec', 'pcm_s16le',  # 16-bit PCM
            output_file
        ], check=True, capture_output=True)
        
        return output_file
    except Exception as e:
        print(f"[ERROR] Audio normalization failed: {e}")
        return None

def process_audio_to_phonemes(audio_file_path, output_dir=None):
    """Process audio file to generate accurate phoneme keyframes"""
    try:
        print(f"[INFO] Processing audio file: {audio_file_path}")
        
        # First normalize audio using ffmpeg
        normalized_audio = normalize_audio(audio_file_path)
        if not normalized_audio:
            print("[ERROR] Failed to normalize audio")
            return None
            
        # Get audio duration
        with wave.open(normalized_audio, 'rb') as wav_file:
            duration = wav_file.getnframes() / float(wav_file.getframerate())
        
        print(f"[INFO] Audio duration: {duration} seconds")
        
        # Initialize enhanced phoneme generator
        generator = EnhancedPhonemeGenerator()
        
        # Generate keyframes using the enhanced system
        keyframes = generator.generate_keyframes(normalized_audio, duration)
        
        if not keyframes:
            print("[ERROR] Failed to generate keyframes")
            return None
            
        # Package the result
        result = {
            "keyframes": keyframes,
            "duration": duration
        }
        
        # Save output with random number to avoid conflicts
        random_num = random.randint(1000, 9999)
        output_file = os.path.join(output_dir, f"responsekeyframes{random_num}.json")
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
            
        print(f"[INFO] Successfully generated {len(keyframes)} keyframes")
        print(f"[INFO] Output saved to: {output_file}")
        
        return output_file
            
    except Exception as e:
        print(f"[ERROR] Failed to process audio: {str(e)}")
        traceback.print_exc()
        return None

class WordTimingExtractor:
    """Extracts precise word timing information from audio using Whisper."""
    
    def __init__(self):
        self.model = whisper.load_model("tiny")
        if NLTK_AVAILABLE:
            self.cmu_dict = cmudict.dict()
        else:
            self.cmu_dict = {}
            
    def get_word_phonemes(self, word):
        """Get the phoneme sequence for a word using CMU dictionary."""
        word = word.lower().strip()
        if word in self.cmu_dict:
            # Get first pronunciation from CMU dict
            phones = self.cmu_dict[word][0]
            # Convert CMU format to our phoneme format
            phoneme_seq = []
            for phone in phones:
                # Remove stress markers
                phone = ''.join([c for c in phone if not c.isdigit()])
                phoneme_seq.append(phone)
            return phoneme_seq
        return [word]  # Return word itself if not found
        
    def extract_word_timings(self, audio_file):
        """
        Extract word-level timing information from audio.
        
        Args:
            audio_file (str): Path to audio file
            
        Returns:
            list: List of dictionaries containing word timing information
        """
        try:
            print("[INFO] Transcribing with Whisper...")
            # Get the transcription with word timestamps
            result = self.model.transcribe(
                audio_file,
                language="en",
                word_timestamps=True
            )
            
            word_timings = []
            audio_duration = 0.0
            
            # Process each segment
            for segment in result["segments"]:
                if "words" not in segment:
                    continue
                    
                # Keep track of the total duration
                if segment["end"] > audio_duration:
                    audio_duration = segment["end"]
                    
                # Process each word in the segment
                for word_data in segment["words"]:
                    if not word_data.get("text"):
                        continue
                        
                    # Clean the word text
                    word = word_data["text"].strip()
                    if not word:
                        continue
                        
                    # Get timing information
                    start = word_data["start"]
                    end = word_data["end"]
                    
                    # Get phonemes for this word
                    phonemes = self.get_word_phonemes(word)
                    
                    # Create word timing entry
                    word_timing = {
                        "word": word,
                        "start": start,
                        "end": end,
                        "phonemes": phonemes
                    }
                    
                    word_timings.append(word_timing)
            
            if not word_timings:
                print("[WARNING] No word timings found, using fallback...")
                # Get duration from audio file if available
                try:
                    with contextlib.closing(wave.open(audio_file, 'r')) as f:
                        frames = f.getnframes()
                        rate = f.getframerate()
                        audio_duration = frames / float(rate)
                except Exception as e:
                    print(f"[WARNING] Could not get audio duration: {e}")
                    audio_duration = 3.0  # Default fallback duration
                
                return self._fallback_word_timing(result["text"], audio_duration)
                
            print(f"[INFO] Extracted timing for {len(word_timings)} words")
            return word_timings
            
        except Exception as e:
            print(f"[ERROR] Failed to extract word timings: {str(e)}")
            traceback.print_exc()
            return None
            
    def _fallback_word_timing(self, text, duration):
        """Fallback method to generate approximate word timings."""
        words = text.strip().split()
        if not words:
            return None
            
        word_timings = []
        avg_duration = duration / len(words)
        
        for i, word in enumerate(words):
            start = i * avg_duration
            end = start + avg_duration
            
            word_timings.append({
                "word": word,
                "start": start,
                "end": end,
                "phonemes": self.get_word_phonemes(word)
            })
            
        return word_timings

class SyllableAnalyzer:
    """Analyzes words for syllable count and timing."""
    
    def __init__(self):
        self.cmu_dict = cmudict.dict() if NLTK_AVAILABLE else {}
        
    def count_syllables(self, word):
        """Count syllables in a word using CMU dictionary."""
        word = word.lower().strip()
        
        # Try CMU dictionary first
        if word in self.cmu_dict:
            phones = self.cmu_dict[word][0]  # Get first pronunciation
            return len([ph for ph in phones if ph[-1].isdigit()])  # Count stress markers
            
        # Fallback: count vowel sequences
        count = 0
        vowels = 'aeiouy'
        prev_is_vowel = False
        
        for char in word:
            is_vowel = char.lower() in vowels
            if is_vowel and not prev_is_vowel:
                count += 1
            prev_is_vowel = is_vowel
            
        return max(1, count)  # Every word has at least one syllable
        
    def get_syllable_timings(self, word_timing):
        """
        Calculate timing for each syllable in a word.
        
        Args:
            word_timing (dict): Word timing information
            
        Returns:
            list: List of syllable timings
        """
        word = word_timing['text']
        start = word_timing['start']
        duration = word_timing['duration']
        
        syllable_count = self.count_syllables(word)
        syllable_duration = duration / syllable_count
        
        syllables = []
        for i in range(syllable_count):
            syllable_start = start + (i * syllable_duration)
            syllable = {
                'word': word,
                'syllable_index': i,
                'syllable_count': syllable_count,
                'start': syllable_start,
                'duration': syllable_duration
            }
            syllables.append(syllable)
            
        return syllables

class EnhancedPhonemeGenerator:
    """Generates enhanced phoneme-based facial animation."""
    
    def __init__(self):
        self.word_extractor = WordTimingExtractor()
        self.syllable_analyzer = SyllableAnalyzer()
        self.phoneme_mapper = PhonemeMapper()
        
    def gaussian_smooth_keyframes(self, keyframes, sigma=1.5, window_size=5):
        """
        Apply Gaussian smoothing to keyframe values for smoother transitions.
        
        Args:
            keyframes (list): List of keyframes to smooth
            sigma (float): Standard deviation for Gaussian kernel
            window_size (int): Size of the smoothing window
            
        Returns:
            list: Smoothed keyframes
        """
        if not keyframes or len(keyframes) <= window_size:
            return keyframes
            
        # Generate Gaussian kernel
        kernel_half_size = window_size // 2
        x = np.linspace(-2, 2, window_size)
        kernel = np.exp(-(x ** 2) / (2 * sigma ** 2))
        kernel = kernel / np.sum(kernel)
        
        smoothed = []
        # Keep first and last keyframes unchanged for proper start/end poses
        smoothed.append(keyframes[0])
        
        # Smooth middle keyframes
        for i in range(1, len(keyframes) - 1):
            # Get window of frames
            start_idx = max(0, i - kernel_half_size)
            end_idx = min(len(keyframes), i + kernel_half_size + 1)
            window = keyframes[start_idx:end_idx]
            
            # Adjust kernel size if window is smaller than expected
            if len(window) < window_size:
                # Create a subset of the kernel that matches the window size
                kernel_subset = kernel[kernel_half_size - (i - start_idx):kernel_half_size + (end_idx - i)]
                kernel_subset = kernel_subset / np.sum(kernel_subset)  # Renormalize
            else:
                kernel_subset = kernel
                
            # Create smoothed keyframe with metadata preserved
            smoothed_kf = {
                'time': keyframes[i]['time'],
                'word': keyframes[i].get('word', ''),
                'syllable': keyframes[i].get('syllable', '')
            }
            
            # For each parameter, apply Gaussian weighting
            for param in keyframes[i]:
                if param in ['time', 'word', 'syllable', 'phoneme']:
                    continue
                    
                if isinstance(keyframes[i][param], dict):
                    # Handle vector values (like jawValue)
                    smoothed_kf[param] = {}
                    for coord in keyframes[i][param]:
                        # Extract values from all keyframes in window
                        values = []
                        for j, kf in enumerate(window):
                            if param in kf and coord in kf[param]:
                                values.append(kf[param][coord])
                            else:
                                values.append(0.0)  # Default if missing
                                
                        # Apply weighted average using Gaussian kernel
                        if len(values) == len(kernel_subset):
                            smoothed_val = sum(v * k for v, k in zip(values, kernel_subset))
                            smoothed_kf[param][coord] = round(smoothed_val, 3)
                        else:
                            smoothed_kf[param][coord] = keyframes[i][param][coord]
                else:
                    # Handle scalar values
                    values = []
                    for j, kf in enumerate(window):
                        if param in kf:
                            values.append(kf[param])
                        else:
                            values.append(0.0)  # Default if missing
                            
                    # Apply weighted average using Gaussian kernel
                    if len(values) == len(kernel_subset):
                        smoothed_val = sum(v * k for v, k in zip(values, kernel_subset))
                        smoothed_kf[param] = round(smoothed_val, 3)
                    else:
                        smoothed_kf[param] = keyframes[i][param]
            
            smoothed.append(smoothed_kf)
        
        # Add last keyframe unchanged
        smoothed.append(keyframes[-1])
        return smoothed
    
    def generate_intermediate_keyframes(self, keyframes, num_intermediates=1):
        """
        Generate intermediate keyframes between existing keyframes for smoother transitions.
        
        Args:
            keyframes (list): Original keyframes
            num_intermediates (int): Number of intermediate frames to insert
            
        Returns:
            list: Keyframes with intermediates added
        """
        if not keyframes or len(keyframes) < 2:
            return keyframes
            
        expanded_keyframes = [keyframes[0]]  # Start with first keyframe
        
        for i in range(1, len(keyframes)):
            prev_kf = keyframes[i-1]
            curr_kf = keyframes[i]
            
            # Calculate time step between keyframes
            time_step = (curr_kf['time'] - prev_kf['time']) / (num_intermediates + 1)
            
            # Skip if keyframes are too close together
            if time_step < 0.015:  # Less than 15ms apart
                expanded_keyframes.append(curr_kf)
                continue
                
            # Add intermediate keyframes with eased values
            for j in range(1, num_intermediates + 1):
                # Use cubic ease-in-out for more natural transitions
                t = j / (num_intermediates + 1)
                # Apply cubic easing: t^2 * (3 - 2t)
                t_eased = t * t * (3 - 2 * t)
                
                intermediate_time = prev_kf['time'] + (time_step * j)
                
                # Create intermediate keyframe
                intermediate_kf = {
                    'time': round(intermediate_time, 3),
                    'word': prev_kf.get('word', ''),
                    'syllable': prev_kf.get('syllable', '') + "_intermediate"
                }
                
                # Interpolate values
                for param in prev_kf:
                    if param in ['time', 'word', 'syllable', 'phoneme']:
                        continue
                        
                    if param not in curr_kf:
                        intermediate_kf[param] = prev_kf[param]
                        continue
                        
                    if isinstance(prev_kf[param], dict):
                        # Handle vector values (like jawValue)
                        intermediate_kf[param] = {}
                        for coord in prev_kf[param]:
                            if coord in curr_kf[param]:
                                # Linear interpolation between values
                                start_val = prev_kf[param][coord]
                                end_val = curr_kf[param][coord]
                                interp_val = start_val + (end_val - start_val) * t_eased
                                intermediate_kf[param][coord] = round(interp_val, 3)
                            else:
                                intermediate_kf[param][coord] = prev_kf[param][coord]
                    else:
                        # Handle scalar values
                        start_val = prev_kf[param]
                        end_val = curr_kf[param]
                        interp_val = start_val + (end_val - start_val) * t_eased
                        intermediate_kf[param] = round(interp_val, 3)
                
                expanded_keyframes.append(intermediate_kf)
            
            # Add current keyframe
            expanded_keyframes.append(curr_kf)
        
        return expanded_keyframes
        
    def generate_keyframes(self, audio_file, duration):
        """Generate keyframes based on word timing and syllable analysis."""
        # Extract word timings with phonemes
        word_timings = self.word_extractor.extract_word_timings(audio_file)
        if not word_timings:
            print("[ERROR] No word timings extracted")
            return []
            
        keyframes = []
        
        # Add initial rest position
        rest_values = self.phoneme_mapper.get_values('rest')
        rest_values['jawValue'] = {'x': 0.0, 'y': 0.0, 'z': 0.0}  # Start with closed jaw
        keyframes.append({
            'time': 0.0,
            **rest_values
        })
        
        # Process each word
        for word_data in word_timings:
            word = word_data['word']
            start_time = word_data['start']
            end_time = word_data['end']
            duration = end_time - start_time
            
            # Get syllables for this word
            syllables = self.syllable_analyzer.count_syllables(word)
            
            # Always add word start with open jaw
            keyframes.append({
                'time': start_time,
                'word': word,
                'syllable': f"{word}_start",
                **self.phoneme_mapper.get_values(word),
                'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0}  # Open jaw at word start
            })
            
            if syllables == 0 or syllables == 1:
                # For words with no syllables or single syllable
                # Add syllable start
                syllable_start_time = start_time + (duration * 0.1)  # Slightly after word start
                keyframes.append({
                    'time': syllable_start_time,
                    'word': word,
                    'syllable': f"{word}_syllable_1_start",
                    **self.phoneme_mapper.get_values(word),
                    'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0}  # Open jaw
                })
                
                # Add syllable end
                syllable_end_time = end_time - (duration * 0.1)  # Slightly before word end
                keyframes.append({
                    'time': syllable_end_time,
                    'word': word,
                    'syllable': f"{word}_syllable_1_end",
                    **self.phoneme_mapper.get_values(word),
                    'jawValue': {'x': 0.0, 'y': 0.2, 'z': 0.0}  # Partial close
                })
                
                # Add word end with closed jaw
                keyframes.append({
                    'time': end_time,
                    'word': word,
                    'syllable': f"{word}_end",
                    **self.phoneme_mapper.get_values(word),
                    'jawValue': {'x': 0.0, 'y': 0.0, 'z': 0.0}  # Close jaw completely
                })
            else:
                # Handle multi-syllable words
                syllable_duration = duration / syllables
                
                for i in range(syllables):
                    syllable_start = start_time + (i * syllable_duration)
                    syllable_end = syllable_start + syllable_duration
                    
                    # Add syllable start for each syllable
                    keyframes.append({
                        'time': syllable_start,
                        'word': word,
                        'syllable': f"{word}_syllable_{i+1}_start",
                        **self.phoneme_mapper.get_values(word),
                        'jawValue': {'x': 0.0, 'y': 0.4, 'z': 0.0}  # Open jaw
                    })
                    
                    # Add syllable end
                    between_time = syllable_end - (syllable_duration * 0.2)  # Close slightly before next syllable
                    keyframes.append({
                        'time': between_time,
                        'word': word,
                        'syllable': f"{word}_syllable_{i+1}_end",
                        **self.phoneme_mapper.get_values(word),
                        'jawValue': {'x': 0.0, 'y': 0.2 if i < syllables - 1 else 0.0, 'z': 0.0}  # Partial close between syllables, full close at end
                    })
                
                # Add final word end if not already added
                if keyframes[-1]['time'] < end_time:
                    keyframes.append({
                        'time': end_time,
                        'word': word,
                        'syllable': f"{word}_end",
                        **self.phoneme_mapper.get_values(word),
                        'jawValue': {'x': 0.0, 'y': 0.0, 'z': 0.0}  # Complete close at end of word
                    })
        
        # Add final rest position if not already at rest
        if keyframes[-1]['time'] < duration:
            final_rest = self.phoneme_mapper.get_values('rest')
            final_rest['jawValue'] = {'x': 0.0, 'y': 0.0, 'z': 0.0}  # Ensure jaw ends closed
            keyframes.append({
                'time': round(duration, 3),
                **final_rest
            })
        
        # Sort by time and remove duplicates
        keyframes.sort(key=lambda k: k['time'])
        unique_keyframes = []
        seen_times = set()
        
        for kf in keyframes:
            time = round(kf['time'], 3)  # Round to 3 decimal places for comparison
            if time not in seen_times:
                kf['time'] = time  # Update the time to rounded value
                seen_times.add(time)
                unique_keyframes.append(kf)
        
        # Add intermediate keyframes for smoother transitions
        print("[INFO] Adding intermediate keyframes for smoother transitions...")
        expanded_keyframes = self.generate_intermediate_keyframes(unique_keyframes, num_intermediates=1)
        
        # Apply Gaussian smoothing for more natural movement
        print("[INFO] Applying Gaussian smoothing to animation keyframes...")
        smoothed_keyframes = self.gaussian_smooth_keyframes(expanded_keyframes, sigma=1.5, window_size=5)
        
        print(f"[INFO] Generated {len(smoothed_keyframes)} keyframes with enhanced smoothing")
        return smoothed_keyframes
