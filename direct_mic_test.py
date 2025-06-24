import pyaudio
import sys

def list_devices():
    p = pyaudio.PyAudio()
    print("\n=== Available Audio Input Devices ===")
    for i in range(p.get_device_count()):
        try:
            dev_info = p.get_device_info_by_index(i)
            if dev_info['maxInputChannels'] > 0:
                print(f"\nDevice {i}: {dev_info['name']}")
                print(f"  - Input Channels: {dev_info['maxInputChannels']}")
                print(f"  - Default Sample Rate: {int(dev_info['defaultSampleRate'])} Hz")
        except Exception as e:
            print(f"Error getting device {i}: {e}")
    p.terminate()

def test_microphone(device_index):
    p = pyaudio.PyAudio()
    
    try:
        # Get device info
        dev_info = p.get_device_info_by_index(device_index)
        print(f"\n=== Testing Microphone ===")
        print(f"Device: {dev_info['name']}")
        print(f"Sample Rate: {int(dev_info['defaultSampleRate'])} Hz")
        print(f"Channels: {dev_info['maxInputChannels']}")
        
        # Open stream
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=int(dev_info['defaultSampleRate']),
            input=True,
            input_device_index=device_index,
            frames_per_buffer=1024
        )
        
        print("\nSpeak into the microphone. You should see numbers changing if it's working.")
        print("Press Ctrl+C to stop...\n")
        
        while True:
            try:
                # Read raw audio data
                data = stream.read(1024, exception_on_overflow=False)
                # Print the first few bytes of the audio data
                print(f"\rAudio data: {data[:10]}...", end='', flush=True)
            except KeyboardInterrupt:
                break
                
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print("\n\n=== Test Complete ===")
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        p.terminate()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_devices()
    elif len(sys.argv) > 1 and sys.argv[1].isdigit():
        test_microphone(int(sys.argv[1]))
    else:
        print("Usage:")
        print("  python direct_mic_test.py list      - List all audio input devices")
        print("  python direct_mic_test.py <number> - Test the specified device")
