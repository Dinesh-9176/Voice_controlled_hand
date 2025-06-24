import pyaudio
import numpy as np

# Initialize PyAudio
p = pyaudio.PyAudio()

# List all audio devices
print("\n=== Available Audio Input Devices ===")
for i in range(p.get_device_count()):
    try:
        dev_info = p.get_device_info_by_index(i)
        if dev_info['maxInputChannels'] > 0:  # Only show input devices
            print(f"\nDevice {i}: {dev_info['name']}")
            print(f"  - Input Channels: {dev_info['maxInputChannels']}")
            print(f"  - Default Sample Rate: {dev_info['defaultSampleRate']} Hz")
            print(f"  - Default Low Latency: {dev_info['defaultLowInputLatency']}")
    except Exception as e:
        print(f"Error getting device {i}: {e}")

# Test a specific device
def test_device(device_index):
    print(f"\n=== Testing Device {device_index} ===")
    try:
        # Open stream with the selected device
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=1024
        )
        
        print("Listening... (Speak into the microphone. Press Ctrl+C to stop)")
        print("If you see numbers changing, the microphone is working!")
        
        while True:
            try:
                # Read audio data
                data = np.frombuffer(stream.read(1024, exception_on_overflow=False), dtype=np.int16)
                # Print the maximum value in the buffer (loudness indicator)
                print(f"\rMax amplitude: {np.max(np.abs(data)):6d}", end='', flush=True)
            except KeyboardInterrupt:
                break
                
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        print("\nTest complete.")

if __name__ == "__main__":
    try:
        # Try to test the default input device
        default_device = p.get_default_input_device_info()
        print(f"\nDefault input device: {default_device['name']} (Index: {default_device['index']})")
        test_device(default_device['index'])
    except Exception as e:
        print(f"Error testing default device: {e}")
        print("Please try running with a specific device index: python simple_mic_test.py <device_index>")
    
    p.terminate()
