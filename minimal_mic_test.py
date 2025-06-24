import pyaudio
import sys

def main():
    print("Minimal Microphone Test")
    print("======================")
    print("This script will try to read from your default microphone.")
    print("If you see binary data when you speak, your microphone is working!")
    print("Press Ctrl+C to stop\n")
    
    p = pyaudio.PyAudio()
    
    try:
        # Open stream with default settings
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            frames_per_buffer=1024
        )
        
        print("Listening... Speak into your microphone!")
        
        while True:
            try:
                # Read a small chunk of audio
                data = stream.read(1024, exception_on_overflow=False)
                # Print the first 10 bytes of the audio data
                print(f"\rAudio data: {data[:10]}...", end='', flush=True)
            except KeyboardInterrupt:
                break
                
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print("\nCleaning up...")
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        p.terminate()
        print("Done!")

if __name__ == "__main__":
    main()
