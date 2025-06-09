def speak(self, text):
        """Make Skippy speak with better audio handling and debugging"""
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
            print("❌ Text-to-speech not available")#!/usr/bin/env python3
"""
Simple Skippy Voice Test
Minimal dependencies for testing voice functionality
"""

import requests
import json

# Try importing optional voice libraries
TTS_AVAILABLE = False
STT_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
    print("✅ pyttsx3 imported successfully")
except ImportError:
    print("❌ pyttsx3 not available - text-to-speech disabled")

try:
    import speech_recognition as sr
    import pyaudio  # Test if PyAudio is available
    STT_AVAILABLE = True
    print("✅ SpeechRecognition and PyAudio imported successfully")
except ImportError as e:
    print(f"❌ Speech recognition not available: {e}")
    print("   (This is OK - we can still do text-to-speech)")
    STT_AVAILABLE = False

class SimpleSkippyVoice:
    def __init__(self, skippy_api_url="http://192.168.0.229:5678/webhook-test/skippy/chat"):
        self.skippy_api_url = skippy_api_url
        
        # Initialize TTS if available
        self.tts_available = TTS_AVAILABLE
        if self.tts_available:
            try:
                self.tts_engine = pyttsx3.init()
                self.setup_tts()
                print("✅ Text-to-speech initialized")
            except Exception as e:
                print(f"❌ TTS error: {e}")
                self.tts_available = False
        
        # Initialize STT if available  
        self.stt_available = STT_AVAILABLE
        if self.stt_available:
            try:
                self.recognizer = sr.Recognizer()
                
                # Tune recognizer for better phrase detection
                self.recognizer.energy_threshold = 200  # Lower for Bluetooth headphones
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 1.5   # Even longer pause before stopping
                self.recognizer.phrase_threshold = 0.3  # More sensitive to start of speech
                self.recognizer.non_speaking_duration = 1.2  # Wait much longer for speech end
                
                self.microphone = sr.Microphone()
                print("✅ Speech recognition initialized with better phrase detection")
            except Exception as e:
                print(f"❌ STT error: {e}")
                self.stt_available = False
    
    def setup_tts(self):
        """Configure Skippy's voice"""
        if not self.tts_available:
            return
            
        voices = self.tts_engine.getProperty('voices')
        
        # Find a good voice for Skippy
        for voice in voices:
            if any(name in voice.name.lower() for name in ['david', 'male', 'mark']):
                self.tts_engine.setProperty('voice', voice.id)
                break
        
        # Make Skippy talk faster (he's impatient)
        self.tts_engine.setProperty('rate', 200)
        self.tts_engine.setProperty('volume', 0.9)
    
    def speak(self, text):
        """Make Skippy speak with better audio handling and debugging"""
        print(f"🎤 Skippy: {text}")
        
        if self.tts_available:
            try:
                print("🔊 Attempting to speak...")
                
                # Add small delay before speaking
                time.sleep(0.1)
                
                self.tts_engine.say(text)
                
                print("🔊 TTS engine processing...")
                self.tts_engine.runAndWait()
                
                print("✅ TTS completed")
                
                # Add small delay after speaking to prevent cutoff
                time.sleep(0.2)
                
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
    
    def test_system(self):
        """Test the voice system"""
        print("\n" + "="*50)
        print("🤖 SKIPPY VOICE SYSTEM TEST")
        print("="*50)
        
        # Test TTS
        self.speak("Voice system test initiated. Testing text-to-speech.")
        
        # Test API connection
        print("\n🔗 Testing API connection...")
        response = self.send_to_skippy("Voice system test - are you there?")
        if response:
            self.speak(response)
        
        # Test speech recognition
        if self.stt_available:
            self.speak("Now testing speech recognition. Say something.")
            user_input = self.listen()
            if user_input:
                self.speak(f"I heard: {user_input}")
        
        print("\n✅ Voice system test complete!")
    
    def chat_mode(self):
        """Simple chat mode"""
        print("\n" + "="*50)
        print("🎤 SKIPPY VOICE CHAT")
        print("Say 'exit' to stop")
        print("="*50)
        
        self.speak("Skippy voice interface online. What do you need?")
        
        while True:
            # Get user input (voice or text)
            if self.stt_available:
                user_input = self.listen()
            else:
                user_input = input("\nYou: ")
            
            if not user_input:
                continue
            
            # Check for exit
            if any(word in user_input.lower() for word in ['exit', 'quit', 'goodbye', 'stop']):
                self.speak("Skippy voice interface shutting down. Finally, some peace.")
                break
            
            # Send to Skippy
            response = self.send_to_skippy(user_input)
            if response:
                self.speak(response)

def main():
    """Main function"""
    print("🚀 Starting Skippy Voice Test...")
    
    skippy = SimpleSkippyVoice()
    
    print("\nChoose an option:")
    print("1. Test voice system")
    print("2. Chat with Skippy")
    print("3. Text-only test")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        skippy.test_system()
    elif choice == "2":
        skippy.chat_mode()
    elif choice == "3":
        # Text-only test
        response = skippy.send_to_skippy("Hello Skippy, testing text communication")
        print(f"\nSkippy response: {response}")
    else:
        print("Invalid choice. Running test...")
        skippy.test_system()

if __name__ == "__main__":
    main()