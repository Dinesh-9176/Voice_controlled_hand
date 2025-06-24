import pyaudio
import numpy as np
import time

# Audio configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
THRESHOLD = 500  # Adjust this value based on your microphone sensitivity

def list_devices(p):
    print("\nAvailable audio input devices:")
    print("=" * 50)
    for i in range(p.get_device_count()):
        try:
            dev_info = p.get_device_info_by_index(i)
            if dev_info['maxInputChannels'] > 0:
                print(f"Device {i}: {dev_info['name']}")
                print(f"   Input Channels: {dev_info['maxInputChannels']}")
                print(f"   Default Sample Rate: {dev_info['defaultSampleRate']} Hz")
                print()
        except Exception as e:
            print(f"Error getting info for device {i}: {e}")

def test_microphone(device_index=None):
    p = pyaudio.PyAudio()
    
    # List all devices first
    list_devices(p)
    
    if device_index is None:
        try:
            device_index = p.get_default_input_device_info()['index']
            print(f"\nUsing default input device: {device_index}")
        except:
            print("\nNo default input device found. Please specify a device index.")
            return
    
    print(f"\nTesting microphone on device {device_index}...")
    print("Speak into the microphone. Press Ctrl+C to stop.")
    
    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK
        )
        
        print("\nListening... (Make some noise!)")
        
        while True:
            try:
                # Read audio data
                data = np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
                
                # Calculate volume level (RMS)
                rms = np.sqrt(np.mean(np.square(data)))
                level = min(int((rms / 32768) * 100), 100)
                
                # Show a simple level meter
                bar = '█' * (level // 5)  # Each █ represents 5%
                print(f"\r[{'|' + bar:<20}] {level:3d}% ", end='', flush=True)
                
            except IOError as e:
                if e.errno == -9981:
                    print("\nInput overflow - some audio data was lost")
                else:
                    raise
                    
    except KeyboardInterrupt:
        print("\n\nStopping...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print("Closing stream...")
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    # You can specify a device index here if needed, e.g., test_microphone(1)
    test_microphone()
