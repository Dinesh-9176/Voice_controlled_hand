# Voice-Controlled Servo System

This project allows you to control a servo motor using voice commands. The system uses Vosk for offline speech recognition and communicates with an Arduino to control the servo.

## Features

- Voice-controlled servo using natural language
- Offline speech recognition (no internet required)
- Simple and easy to set up
- Threaded audio processing for smooth operation

## Hardware Requirements

- Arduino board (Uno, Nano, etc.)
- Micro Servo Motor (e.g., SG90)
- USB microphone (or built-in microphone)
- Jumper wires
- Breadboard (optional)

## Wiring

Connect the servo to your Arduino as follows:
- **Servo Red (Power)** → 5V on Arduino
- **Servo Brown (Ground)** → GND on Arduino
- **Servo Orange/Yellow (Signal)** → Digital Pin 9 on Arduino

## Setup Instructions

### 1. Install Python Dependencies

```bash
# Install required Python packages
pip install -r requirements.txt
```

### 2. Download Vosk Model

Download the small English model for Vosk:

```bash
# In the project directory
python -m vosk_download_model small-en-us
```

This will create a `vosk-model-small-en-us-0.15` directory in your project folder.

### 3. Upload Arduino Code

1. Open the Arduino IDE
2. Open `arduino/servo_control.ino`
3. Select your board and port from Tools menu
4. Click the Upload button

## Usage

1. Connect your Arduino to the computer
2. Run the Python script:
   ```bash
   python voice_control.py
   ```
3. Speak the following commands:
   - Say "open" to move the servo to the open position
   - Say "close" to move the servo to the closed position

## Troubleshooting

- **No audio input detected**: Check your microphone settings and ensure it's properly connected.
- **Arduino not found**: Update the `SERIAL_PORT` in `voice_control.py` to match your Arduino's COM port.
- **Vosk model not found**: Make sure you've downloaded the model and it's in the correct directory.

## Customization

- Adjust `openPos` and `closePos` in `servo_control.ino` to change the servo angles.
- Modify the voice commands in `voice_control.py` by editing the keyword matching logic.

## License

This project is open source and available under the MIT License.
