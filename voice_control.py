import os
import json
import queue
import re
import threading
import time
import serial
import pyaudio
from vosk import Model, KaldiRecognizer

class VoiceControl:
    def __init__(self):
        # Audio configuration
        self.SAMPLE_RATE = 16000
        self.CHUNK = 8192  # Increased buffer size for better recognition
        self.AUDIO_FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        
        # Serial configuration
        self.SERIAL_PORT = 'COM9'  # Update this
        self.BAUD_RATE = 9600
        
        # Voice model path
        self.MODEL_PATH = os.path.join(
            os.path.dirname(__file__), 
            "vosk-model-small-en-us-0.15"
        )
        
        # Voice command mappings
        self.COMMANDS = {
            'open': 0,
            'close': 90,
            'shut': 90,
            'zero': 0,
            'ninety': 90,
            'one eighty': 180,
            'one hundred eighty': 180,
            'forty five': 45,
            'forty-five': 45
        }
        
        # Number patterns for better recognition
        self.NUMBER_PATTERNS = {
            r'\b(zero|oh|no|hero|nero|arrow|narrow|nora|nora|nora|nora)\b': 0,
            r'\b(one|won|when|wine|won't|want|once|on|won't|when|wine|won't|want|once|on|won't|when|wine|won't|want|once|on)\b': 1,
            r'\b(two|to|too|true|through|do|two|to|too|true|through|do|two|to|too|true|through|do)\b': 2,
            r'\b(three|free|tree|the|three|free|tree|the|three|free|tree|the)\b': 3,
            r'\b(four|for|fore|fourth|forth|for|fore|fourth|forth|for|fore|fourth|forth)\b': 4,
            r'\b(five|fire|fight|fifth|five|fire|fight|fifth|five|fire|fight|fifth)\b': 5,
            r'\b(six|sick|sikh|sikh|sick|sikh|sick|sikh|sick|sikh|sick|sikh)\b': 6,
            r'\b(seven|saving|savings|saving|savings|saving|savings|saving|savings|saving|savings)\b': 7,
            r'\b(eight|ate|hate|hate|hate|hate|hate|hate|hate|hate|hate|hate)\b': 8,
            r'\b(nine|niner|niner|niner|niner|niner|niner|niner|niner|niner|niner|niner)\b': 9,
            r'\b(ten|tennis|tenth|tennis|tenth|tennis|tenth|tennis|tenth|tennis|tenth|tennis)\b': 10,
            r'\b(twenty|20|twenty|20|twenty|20|twenty|20|twenty|20|twenty|20)\b': 20,
            r'\b(thirty|30|thirty|30|thirty|30|thirty|30|thirty|30|thirty|30)\b': 30,
            r'\b(forty|40|forty|40|forty|40|forty|40|forty|40|forty|40)\b': 40,
            r'\b(fifty|50|fifty|50|fifty|50|fifty|50|fifty|50|fifty|50)\b': 50,
            r'\b(sixty|60|sixty|60|sixty|60|sixty|60|sixty|60|sixty|60)\b': 60,
            r'\b(seventy|70|seventy|70|seventy|70|seventy|70|seventy|70|seventy|70)\b': 70,
            r'\b(eighty|80|eighty|80|eighty|80|eighty|80|eighty|80|eighty|80)\b': 80,
            r'\b(ninety|90|ninety|90|ninety|90|ninety|90|ninety|90|ninety|90)\b': 90,
            r'\b(hundred|100|hundred|100|hundred|100|hundred|100|hundred|100|hundred|100)\b': 100,
            r'\b(one hundred|100|one hundred|100|one hundred|100|one hundred|100|one hundred|100|one hundred|100)\b': 100,
            r'\b(one eighty|180|one eighty|180|one eighty|180|one eighty|180|one eighty|180|one eighty|180)\b': 180
        }
        
        self.setup_audio()
        self.setup_serial()
        self.setup_voice_model()
        
        self.running = False
        self.command_queue = queue.Queue()
        self.current_angle = 0

    def setup_audio(self):
        """Initialize audio input"""
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=self.AUDIO_FORMAT,
            channels=self.CHANNELS,
            rate=self.SAMPLE_RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )

    def setup_serial(self):
        """Initialize serial connection to Arduino"""
        try:
            self.arduino = serial.Serial(
                self.SERIAL_PORT,
                self.BAUD_RATE,
                timeout=1
            )
            print(f"✅ Connected to Arduino on {self.SERIAL_PORT}")
        except Exception as e:
            print(f"❌ Failed to connect to Arduino: {e}")
            self.arduino = None

    def setup_voice_model(self):
        """Initialize voice recognition model"""
        if not os.path.exists(self.MODEL_PATH):
            print(f"❌ Model not found at {self.MODEL_PATH}")
            print("Please download the model from:")
            print("https://alphacephei.com/vosk/models")
            exit(1)
            
        self.model = Model(self.MODEL_PATH)
        self.recognizer = KaldiRecognizer(self.model, self.SAMPLE_RATE)
        print("✅ Voice model loaded")

    def send_command(self, command):
        """Send command to Arduino"""
        if not self.arduino or not self.arduino.is_open:
            print("⚠️  Not connected to Arduino")
            return False
            
        try:
            cmd_str = f"{command}\n"
            self.arduino.write(cmd_str.encode('utf-8'))
            return True
        except Exception as e:
            print(f"❌ Error sending command: {e}")
            return False

    def extract_number(self, text):
        """Extract number from spoken text using pattern matching"""
        # First check for exact command matches
        text = text.lower()
        
        # Check for direct matches in commands
        for cmd, angle in self.COMMANDS.items():
            if cmd in text:
                return angle
        
        # Try to extract numbers
        for pattern, number in self.NUMBER_PATTERNS.items():
            if re.search(pattern, text):
                return number
                
        # Try to find numbers in the text
        numbers = re.findall(r'\d+', text)
        if numbers:
            return min(int(numbers[0]), 180)  # Cap at 180 degrees
            
        return None
    
    def process_audio(self):
        """Process audio in a separate thread"""
        print("\n🎤 Voice Control for Servo")
        print("========================")
        print("Voice Commands:")
        print("- 'open' or 'zero': Move to 0°")
        print("- 'close' or 'shut': Move to 90°")
        print("- 'one eighty' or '180': Move to 180°")
        print("- '45', '90', etc.: Move to specific angle")
        print("- 'left'/'right': Rotate 15° in that direction")
        print("- 'exit' to quit")
        print("\nListening... (Press Ctrl+C to stop)")
        
        while self.running:
            try:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").strip()
                    
                    if not text:
                        continue
                        
                    print(f"\n🎤 Heard: {text}")
                    
                    # Process exit command first
                    if "exit" in text or "quit" in text:
                        print("🛑 Exiting...")
                        self.running = False
                        continue
                        
                    # Check for directional commands
                    if "left" in text:
                        new_angle = max(0, self.current_angle - 15)
                        self.command_queue.put(new_angle)
                        continue
                        
                    if "right" in text:
                        new_angle = min(180, self.current_angle + 15)
                        self.command_queue.put(new_angle)
                        continue
                    
                    # Try to extract a number/angle from the command
                    angle = self.extract_number(text)
                    if angle is not None:
                        self.command_queue.put(angle)
                    else:
                        print("❌ Command not recognized. Try 'open', 'close', '45', '90', etc.")
                
                # Process partial results for better responsiveness
                partial_result = json.loads(self.recognizer.PartialResult())
                partial_text = partial_result.get("partial", "").strip()
                if partial_text and ("left" in partial_text or "right" in partial_text):
                    print(f"\r🎤 Processing: {partial_text}", end='', flush=True)
                    
    def listen(self):
        """Main listening loop"""
        print("\n🎤 Voice control started")
        print("Say 'open', 'close', 'stop', or 'exit'")
        print("Press Ctrl+C to quit\n")
        
        self.running = True
        audio_thread = threading.Thread(target=self.process_audio)
        audio_thread.start()
        
        while self.running:
            try:
                command = self.command_queue.get(timeout=1)
                if command is not None:
                    self.send_command(command)
                    self.current_angle = command
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                print("\n👋 Exiting gracefully...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                continue

    def cleanup(self):
        """Clean up resources"""
        print("\n🧹 Cleaning up...")
        self.running = False
        
        if hasattr(self, 'stream'):
            self.stream.stop_stream()
            self.stream.close()
            
        if hasattr(self, 'audio'):
            self.audio.terminate()
            
        if hasattr(self, 'arduino') and self.arduino and self.arduino.is_open:
            self.arduino.close()
            
        print("✅ Cleanup complete")

if __name__ == "__main__":
    vc = VoiceControl()
    try:
        vc.listen()
    finally:
        vc.cleanup()