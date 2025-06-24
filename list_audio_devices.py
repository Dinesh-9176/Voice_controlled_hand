import pyaudio

def list_audio_devices():
    p = pyaudio.PyAudio()
    print("\nAvailable audio input devices:")
    print("----------------------------")
    
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        if dev_info['maxInputChannels'] > 0:  # Only show input devices
            print(f"Device {i}: {dev_info['name']}")
            print(f"   Input Channels: {dev_info['maxInputChannels']}")
            print(f"   Default Sample Rate: {dev_info['defaultSampleRate']} Hz")
            print(f"   Default Low Latency: {dev_info['defaultLowInputLatency']}")
            print()
    
    p.terminate()

if __name__ == "__main__":
    list_audio_devices()
