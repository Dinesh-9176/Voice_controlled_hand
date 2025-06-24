import pyaudio
import wave
import os

def record_sample(device_index, filename="test_mic.wav", duration=3):
    """Record a short audio sample and save it to a file"""
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024
    
    audio = pyaudio.PyAudio()
    
    print(f"\n=== Testing Microphone (Device {device_index}) ===")
    print(f"Recording for {duration} seconds...")
    
    try:
        # Open stream
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK
        )
        
        print("Recording... Speak into the microphone!")
        frames = []
        
        # Record for the specified duration
        for i in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            print(f"\rRecording... {i * CHUNK / RATE:.1f}/{duration} seconds", end='', flush=True)
        
        print("\nRecording complete!")
        
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        
        # Save the recorded data as a WAV file
        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        # Get file size
        file_size = os.path.getsize(filename)
        print(f"Saved recording to {filename} ({file_size} bytes)")
        
        # Check if the file contains any audio data
        if file_size < 100:  # Very small file, probably no audio
            print("WARNING: The recorded file is very small. The microphone may not be working correctly.")
        else:
            print("Try playing the file to check if your voice was recorded.")
        
        return True
        
    except Exception as e:
        print(f"\nError: {e}")
        return False
    finally:
        audio.terminate()

def list_devices():
    """List all available audio input devices"""
    p = pyaudio.PyAudio()
    print("\n=== Available Audio Input Devices ===")
    input_devices = []
    
    for i in range(p.get_device_count()):
        try:
            dev_info = p.get_device_info_by_index(i)
            if dev_info['maxInputChannels'] > 0:
                input_devices.append((i, dev_info['name']))
                print(f"{i}: {dev_info['name']} (Channels: {dev_info['maxInputChannels']}, "
                      f"Rate: {int(dev_info['defaultSampleRate'])} Hz)")
        except Exception as e:
            print(f"Error getting device {i}: {e}")
    
    p.terminate()
    return input_devices

def main():
    print("Microphone Access Tester")
    print("========================")
    
    # List all input devices
    input_devices = list_devices()
    
    if not input_devices:
        print("No input devices found!")
        return
    
    # Test the first input device by default
    device_index = input_devices[0][0]
    
    # Try to record a sample
    if record_sample(device_index):
        print("\nRecording completed successfully!")
        print(f"Check the file 'test_mic.wav' in this directory to hear the recording.")
    else:
        print("\nFailed to record audio. Please check your microphone settings.")
    
    print("\nTroubleshooting Tips:")
    print("1. Make sure your microphone is properly connected.")
    print("2. Check your system's sound settings to ensure the correct microphone is selected.")
    print("3. Make sure the microphone is not muted and the volume is turned up.")
    print("4. Try using a different microphone if available.")
    print("5. Check if other applications can use the microphone.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
    input("\nPress Enter to exit...")
