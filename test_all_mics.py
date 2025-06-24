import pyaudio
import time

def test_microphone(device_index, device_name):
    p = pyaudio.PyAudio()
    print(f"\n=== Testing: {device_name} (Device {device_index}) ===")
    
    try:
        # Open stream
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=1024
        )
        
        print("Listening for 5 seconds... Speak into the microphone!")
        print("If you see numbers changing, the microphone is working!")
        print("Press Ctrl+C to skip to the next device...\n")
        
        start_time = time.time()
        last_print = 0
        
        while time.time() - start_time < 5:  # Test for 5 seconds
            try:
                # Read audio data
                data = stream.read(1024, exception_on_overflow=False)
                # Calculate max amplitude
                max_val = max(abs(int.from_bytes(data[i:i+2], 'little', signed=True)) 
                             for i in range(0, len(data), 2) if i+2 <= len(data))
                print(f"\rMax amplitude: {max_val:6d}", end='', flush=True)
                time.sleep(0.1)  # Small delay to prevent flooding the output
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\nError reading from device: {e}")
                break
                
    except Exception as e:
        print(f"Error opening device: {e}")
    finally:
        print("\n--- Test complete ---\n")
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        p.terminate()

def main():
    print("Microphone Testing Tool")
    print("=======================")
    
    p = pyaudio.PyAudio()
    
    # List all input devices
    print("\nAvailable input devices:")
    input_devices = []
    for i in range(p. get_device_count()):
        try:
            dev_info = p.get_device_info_by_index(i)
            if dev_info['maxInputChannels'] > 0:
                input_devices.append((i, dev_info['name']))
                print(f"{i}: {dev_info['name']} (Channels: {dev_info['maxInputChannels']}, "
                      f"Rate: {int(dev_info['defaultSampleRate'])} Hz)")
        except:
            pass
    
    p.terminate()
    
    if not input_devices:
        print("No input devices found!")
        return
    
    # Test each input device
    for device_index, device_name in input_devices:
        test_microphone(device_index, device_name)
        
        # Ask if user wants to continue
        if device_index != input_devices[-1][0]:  # If not the last device
            try:
                response = input("Test next device? (y/n): ").strip().lower()
                if response != 'y':
                    break
            except KeyboardInterrupt:
                print("\nTesting stopped by user.")
                break

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
    input("\nPress Enter to exit...")
