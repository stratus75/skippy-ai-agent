#!/usr/bin/env python3
"""
Skippy Voice Service
Handles speech-to-text, text-to-speech, and wake word detection
"""

import speech_recognition as sr
import pyttsx3
import requests
import json
import threading
import time
import queue
import logging
from typing import Optional
import pvporcupine
import pyaudio
import struct

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SkippyVoice:
    def __init__(self, skippy_api_url: str = "http://192.168.0.229:5678/webhook-test/skippy/chat"):
        self.skippy_api_url = skippy_api_url
        self.is_listening = False
        self.audio_queue = queue.Queue()
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize text-to-speech
        self.tts_engine = pyttsx3.init()
        self.setup_tts_voice()
        
        # Wake word detection
        self.porcupine = None
        self.wake_word_detected = False
        
        logger.info("Skippy Voice Service initialized")
    
    def setup_tts_voice(self):
        """Configure text-to-speech voice settings"""
        voices = self.tts_engine.getProperty('voices')
        
        # Try to find a suitable voice for Skippy (prefer male, faster)
        for voice in voices:
            if 'male' in voice.name.lower() or 'david' in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break
        
        # Set speech rate (make Skippy talk faster - he's impatient)
        self.tts_engine.setProperty('rate', 200)  # Default is usually 200
        self.tts_engine.setProperty('volume', 0.9)
        
        logger.info("Text-to-speech configured")
    
    def calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        logger.info("Calibrating microphone for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        logger.info("Microphone calibrated")
    
    def listen_for_speech(self, timeout: int = 5) -> Optional[str]:
        """Listen for speech and convert to text"""
        try:
            logger.info("Listening for speech...")
            with self.microphone as source:
                # Listen for audio with timeout
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            logger.info("Processing speech...")
            # Use Google's speech recognition (free tier)
            text = self.recognizer.recognize_google(audio)
            logger.info(f"Recognized: {text}")
            return text
            
        except sr.WaitTimeoutError:
            logger.warning("Listening timeout")
            return None
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {e}")
            return None
    
    def speak_text(self, text: str):
        """Convert text to speech"""
        logger.info(f"Skippy says: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
    
    def send_to_skippy(self, message: str) -> Optional[str]:
        """Send message to Skippy API and get response"""
        try:
            payload = {"message": message}
            response = requests.post(
                self.skippy_api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('response', 'Error: No response from Skippy')
            else:
                logger.error(f"API error: {response.status_code}")
                return "Sorry, I'm having trouble connecting to my brain right now."
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return "My connection seems to be having issues. Try again in a moment."
    
    def conversation_mode(self):
        """Interactive conversation mode"""
        logger.info("Starting conversation mode. Say 'exit' or 'goodbye' to stop.")
        self.speak_text("Hello! Skippy here. What do you need, meat-sack?")
        
        while True:
            # Listen for user input
            user_input = self.listen_for_speech(timeout=10)
            
            if user_input is None:
                continue
            
            # Check for exit commands
            if any(word in user_input.lower() for word in ['exit', 'goodbye', 'stop', 'quit']):
                self.speak_text("Finally, some peace and quiet. Skippy out.")
                break
            
            # Send to Skippy and get response
            skippy_response = self.send_to_skippy(user_input)
            
            if skippy_response:
                self.speak_text(skippy_response)
    
    def wake_word_mode(self):
        """Always listening for 'Hey Skippy' wake word"""
        # This would require Porcupine wake word detection
        # For now, we'll use a simpler approach
        logger.info("Wake word mode not fully implemented yet. Use conversation_mode() instead.")
        self.conversation_mode()
    
    def test_voice_system(self):
        """Test all voice components"""
        logger.info("Testing Skippy Voice System...")
        
        # Test TTS
        self.speak_text("Voice system test initiated. Can you hear me, human?")
        
        # Test microphone calibration
        self.calibrate_microphone()
        
        # Test speech recognition
        self.speak_text("Say something so I can test if I can understand your primitive vocalizations.")
        user_input = self.listen_for_speech(timeout=10)
        
        if user_input:
            self.speak_text(f"I heard you say: {user_input}")
            
            # Test API connection
            response = self.send_to_skippy("Voice system test")
            if response:
                self.speak_text(response)
            else:
                self.speak_text("My brain seems to be offline. That's concerning.")
        else:
            self.speak_text("I couldn't understand you. Perhaps speak more clearly next time.")

def main():
    """Main function to run Skippy Voice Service"""
    skippy = SkippyVoice()
    
    print("\n" + "="*50)
    print("SKIPPY VOICE SERVICE")
    print("="*50)
    print("1. Test voice system")
    print("2. Start conversation mode")
    print("3. Wake word mode (coming soon)")
    print("="*50)
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        skippy.test_voice_system()
    elif choice == "2":
        skippy.conversation_mode()
    elif choice == "3":
        skippy.wake_word_mode()
    else:
        print("Invalid choice. Starting test mode...")
        skippy.test_voice_system()

if __name__ == "__main__":
    main()