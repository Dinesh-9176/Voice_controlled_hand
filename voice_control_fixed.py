import os
import json
import queue
import threading
import time
import serial
import pyaudio
from vosk import Model, KaldiRecognizer
#   
class VoiceControl:
    def __init__(self):
        # Audio configuration
        self.SAMPLE_RATE = 16000
        self.CHUNK = 8192
        self.AUDIO_FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        
        # Serial configuration
        self.SERIAL_PORT = 'COM9'  
        self.BAUD_RATE = 9600
        

        
        # Voice model path
        self.MODEL_PATH = os.path.join(
            os.path.dirname(__file__),
            "vosk-model-small-en-us-0.15"
        )
        
        # Voice command mappings (only open/close)
        self.OPEN_COMMANDS = ['open', 'on', 'start', 'zero']
        self.CLOSE_COMMANDS = ['close', 'shut', 'off', 'one eighty', '180']
        
        self.setup_audio()
        self.setup_serial()
        self.setup_voice_model()
        
        self.running = False
        self.command_queue = queue.Queue()
        self.current_angle = 90  # Start at 90 degrees (center)


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
            self.ser = serial.Serial(self.SERIAL_PORT, self.BAUD_RATE, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
            print(f"✅ Connected to Arduino on {self.SERIAL_PORT}")
        except Exception as e:
            print(f"❌ Failed to connect to Arduino: {e}")
            self.ser = None

    def setup_voice_model(self):
        """Initialize voice recognition model"""
        if not os.path.exists(self.MODEL_PATH):
            print(f"❌ Model not found at {self.MODEL_PATH}")
            print("Please download the model using 'python -m vosk_model_download'")  
            exit(1)
            
        self.model = Model(self.MODEL_PATH)
        self.recognizer = KaldiRecognizer(self.model, self.SAMPLE_RATE)
        self.recognizer.SetWords(True)

    def send_command(self, angle):
        """Send angle command to Arduino"""
        if not self.ser or not self.ser.is_open:
            print("⚠️  Not connected to Arduino")
            return False
            
        try:
            # Send angle as a string with newline terminator
            command = f"{angle}\n"
            self.ser.write(command.encode('utf-8'))
            print(f"→ Sent angle: {angle}°")
            
            # Wait for and read Arduino's response
            start_time = time.time()
            while self.ser.in_waiting == 0:
                if time.time() - start_time > 1.0:  # 1 second timeout
                    print("⚠️  No response from Arduino")
                    return False
                time.sleep(0.01)
                
            response = self.ser.readline().decode('utf-8').strip()
            print(f"← Arduino: {response}")
            self.current_angle = angle  # Update current angle
            return True
            
        except Exception as e:
            print(f"❌ Error sending command: {e}")
            return False

    def process_command(self, text):
        """Process voice command and return angle (0 or 180)"""
        text = text.lower().strip()
        
        # Check for open commands
        for cmd in self.OPEN_COMMANDS:
            if cmd in text:
                return 0
                
        # Check for close commands
        for cmd in self.CLOSE_COMMANDS:
            if cmd in text:
                return 180
                
        return None

    def process_audio(self):
        """Process audio in a separate thread"""
        print("\n🎤 Voice Control for Servo")
        print("========================")
        print("Voice Commands:")
        print("- 'open' or 'on' or 'start': Move to 0° (open)")
        print("- 'close' or 'shut' or 'off': Move to 180° (close)")
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
                    
                    # Process open/close commands
                    angle = self.process_command(text)
                    if angle is not None:
                        self.command_queue.put(angle)
                    else:
                        print("❌ Command not recognized. Say 'open' or 'close'.")
                
                # Process partial results for better responsiveness
                partial_result = json.loads(self.recognizer.PartialResult())
                partial_text = partial_result.get("partial", "").strip()
                if partial_text and ("left" in partial_text or "right" in partial_text):
                    print(f"\r🎤 Processing: {partial_text}", end='', flush=True)
                    
            except Exception as e:
                print(f"\n❌ Error in audio processing: {e}")
                time.sleep(0.1)

    def listen(self):
        """Main listening loop"""
        print("\n🎤 Voice control started")
        print("=====================")
        print("Press Ctrl+C to quit\n")
        
        self.running = True
        audio_thread = threading.Thread(target=self.process_audio)
        audio_thread.daemon = True
        audio_thread.start()
        
        try:
            while self.running:
                try:
                    # Process commands from the queue
                    try:
                        angle = self.command_queue.get(timeout=0.1)
                        self.send_command(str(angle))  # Convert to string for Arduino
                    except queue.Empty:
                        pass
                        
                    time.sleep(0.01)
                        
                except KeyboardInterrupt:
                    print("\n👋 Exiting gracefully...")
                    break
                    
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        if hasattr(self, 'stream'):
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, 'audio'):
            self.audio.terminate()
        if hasattr(self, 'ser') and self.ser and self.ser.is_open:
            self.ser.close()
        print("✅ Cleaned up resources")

if __name__ == "__main__":
    vc = VoiceControl()
    vc.listen()