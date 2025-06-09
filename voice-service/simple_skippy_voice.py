#!/usr/bin/env python3
"""
Skippy Voice Interface - Simple Test Version
Full voice conversation with Skippy AI
"""

import speech_recognition as sr
import pyttsx3
import requests
import json

# Check if speech recognition is available
try:
    import speech_recognition as sr
    import pyaudio  # Test if PyAudio is available
    STT_AVAILABLE = True
    print("✅ SpeechRecognition and PyAudio imported successfully")
except ImportError as e:
    print(f"❌ Speech recognition not available: {e}")
    print("   (This is OK - we can still do text-to-speech)")
    STT_AVAILABLE = False

# Check if TTS is available
try:
    import pyttsx3
    TTS_AVAILABLE = True
    print("✅ pyttsx3 imported successfully")
except ImportError:
    print("❌ pyttsx3 not available - text-to-speech disabled")
    TTS_AVAILABLE = False

class SkippyVoice:
    def __init__(self, skippy_api_url="http://192.168.0.229:5678/webhook-test/skippy/chat"):
        self.skippy_api_url = skippy_api_url
        
        # Initialize TTS
        self.tts_available = TTS_AVAILABLE
        if self.tts_available:
            try:
                self.tts_engine = pyttsx3.init()
                self.setup_tts()
                print("✅ Text-to-speech initialized")
            except Exception as e:
                print(f"❌ TTS initialization error: {e}")
                self.tts_available = False
        
        # Initialize STT if available  
        self.stt_available = STT_AVAILABLE
        if self.stt_available:
            try:
                self.recognizer = sr.Recognizer()
                
                # Tune recognizer for better phrase detection
                self.recognizer.energy_threshold = 200  # Lower for better sensitivity
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 1.5   # Wait longer before stopping
                self.recognizer.phrase_threshold = 0.3  # More sensitive to start of speech
                self.recognizer.non_speaking_duration = 1.2  # Wait much longer for speech end
                
                self.microphone = sr.Microphone()
                print("✅ Speech recognition initialized with better phrase detection")
            except Exception as e:
                print(f"❌ STT error: {e}")
                self.stt_available = False
    
    def setup_tts(self):
        """Configure Skippy's voice for HDMI speakers"""
        if not self.tts_available:
            return
        
        try:
            voices = self.tts_engine.getProperty('voices')
            print(f"Available voices: {len(voices)}")
            
            # List available voices for debugging
            for i, voice in enumerate(voices):
                print(f"  {i}: {voice.name}")
            
            # Configure for HDMI compatibility
            self.tts_engine.setProperty('rate', 180)  # Good pace for HDMI
            self.tts_engine.setProperty('volume', 1.0)  # Full volume
            
            # Try to use a more compatible voice
            if len(voices) > 0:
                self.tts_engine.setProperty('voice', voices[0].id)
                print(f"Selected voice: {voices[0].name}")
            
            print("✅ TTS configured for HDMI speakers")
            
        except Exception as e:
            print(f"❌ TTS setup error: {e}")
    
    def speak(self, text):
        """Make Skippy speak"""
        print(f"🎤 Skippy: {text}")
        
        if self.tts_available:
            try:
                print("🔊 Attempting to speak...")
                
                self.tts_engine.say(text)
                
                print("🔊 TTS engine processing...")
                self.tts_engine.runAndWait()
                
                print("✅ TTS completed")
                
            except Exception as e:
                print(f"❌ TTS Error: {e}")
        else:
            print("❌ Text-to-speech not available")
    
    def listen(self):
        """Listen for user speech with better timing"""
        if not self.stt_available:
            print("Speech recognition not available. Type your message:")
            return input("You: ")
        
        try:
            print("🎧 Listening... (Speak clearly, I'll wait for you to finish)")
            
            with self.microphone as source:
                # Longer calibration for better accuracy
                print("📢 Calibrating microphone...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("🎤 Speak now! (I'll automatically detect when you're done)")
                
                # Better timing settings to catch full phrases
                audio = self.recognizer.listen(
                    source, 
                    timeout=20,           # Wait up to 20 seconds for speech to start
                    phrase_time_limit=20  # Allow 20 seconds for complete phrase
                )
            
            print("🔄 Processing your complete message...")
            text = self.recognizer.recognize_google(audio)
            print(f"👤 You said: {text}")
            return text
            
        except sr.WaitTimeoutError:
            print("⏰ Timeout - no speech detected in 20 seconds")
            return None
        except sr.UnknownValueError:
            print("❓ Couldn't understand that - try speaking more clearly")
            return None
        except Exception as e:
            print(f"❌ Speech recognition error: {e}")
            # Fall back to text input
            print("Falling back to text input:")
            return input("You: ")
    
    def send_to_skippy(self, message):
        """Send message to Skippy API with fallback URLs"""
        urls_to_try = [
            "http://192.168.0.229:5678/webhook/skippy/chat",  # Active mode
            "http://192.168.0.229:5678/webhook-test/skippy/chat"  # Test mode
        ]
        
        for url in urls_to_try:
            try:
                payload = {"message": message}
                print(f"🔗 Trying: {url}")
                
                response = requests.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=60  # Increase timeout for Skippy's thinking time
                )
                
                print(f"📥 Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Success with: {url}")
                    # Update the instance URL to the working one
                    self.skippy_api_url = url
                    return data.get('response', 'No response from Skippy')
                else:
                    print(f"❌ Failed: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Exception with {url}: {e}")
        
        return "Could not reach Skippy's brain - all endpoints failed"
    
    def test_voice_system(self):
        """Test the voice system"""
        print("="*50)
        print("🤖 SKIPPY VOICE SYSTEM TEST")
        print("="*50)
        
        self.speak("Voice system test initiated. Testing text-to-speech.")
        
        print("🔗 Testing API connection...")
        response = self.send_to_skippy("Voice system test - are you there?")
        
        if response:
            self.speak(response)
        
        print("✅ Voice system test complete!")
    
    def chat_mode(self):
        """Interactive chat with Skippy"""
        print("="*50)
        print("🎤 SKIPPY VOICE CHAT MODE")
        print("="*50)
        print("Say 'exit', 'quit', or 'goodbye' to end the conversation")
        print("="*50)
        
        # Initial greeting
        greeting = self.send_to_skippy("Hello Skippy, I want to have a voice conversation")
        if greeting:
            self.speak(greeting)
        
        while True:
            # Listen for user input
            user_input = self.listen()
            
            if user_input is None:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'goodbye', 'bye']:
                farewell = self.send_to_skippy("Goodbye Skippy")
                if farewell:
                    self.speak(farewell)
                break
            
            # Send to Skippy and get response
            response = self.send_to_skippy(user_input)
            
            if response:
                self.speak(response)
    
    def text_only_test(self):
        """Text-only test for debugging"""
        print("="*50)
        print("📝 TEXT-ONLY TEST MODE")
        print("="*50)
        
        while True:
            user_input = input("\n👤 You: ")
            
            if user_input.lower() in ['exit', 'quit', 'goodbye']:
                print("👋 Goodbye!")
                break
            
            response = self.send_to_skippy(user_input)
            print(f"🎤 Skippy: {response}")
            
            if self.tts_available:
                self.speak(response)

def main():
    print("\n" + "="*60)
    print("🎤 SKIPPY VOICE INTERFACE")
    print("="*60)
    print("🚀 Starting Skippy Voice Test...")
    
    skippy = SkippyVoice()
    
    print("\nChoose an option:")
    print("1. Test voice system")
    print("2. Chat with Skippy")
    print("3. Text-only test")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        skippy.test_voice_system()
    elif choice == "2":
        skippy.chat_mode()
    elif choice == "3":
        skippy.text_only_test()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()