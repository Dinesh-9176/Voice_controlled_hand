import dash
from dash import dcc, html, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate
import serial
import serial.tools.list_ports
import threading
import time
from datetime import datetime
import queue
import os
from vosk import Model, KaldiRecognizer
import pyaudio
import json
import numpy as np

# Configuration
MODEL_PATH = os.path.join(os.path.dirname(__file__), "vosk-model-small-en-us-0.15")
SAMPLE_RATE = 16000
CHUNK = 4000
SERIAL_PORT = 'COM9'  # Default, will be updated by user
BAUD_RATE = 9600

def create_gauge(angle):
    """Create a gauge chart showing the servo position"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = angle,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Servo Position: {angle}°", 'font': {'size': 24}},
        gauge = {
            'axis': {'range': [0, 180], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 60], 'color': 'lightgreen'},
                {'range': [60, 120], 'color': 'yellow'},
                {'range': [120, 180], 'color': 'red'}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': angle
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        height=400
    )
    return fig

def process_audio():
    """Background thread to process audio input"""
    global is_listening, audio_stream
    
    print("Starting audio processing thread...")
    
    try:
        # List available audio devices
        print("\nAvailable audio devices:")
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            print(f"{i}: {dev['name']} (Input Channels: {dev['maxInputChannels']})")
        
        # Try to find a suitable input device
        input_device_index = None
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev['maxInputChannels'] > 0 and 'microphone' in dev['name'].lower():
                input_device_index = i
                print(f"\nUsing input device: {dev['name']}")
                break
        
        if input_device_index is None:
            print("\nWarning: No suitable microphone found. Using default input device.")
        
        # Open audio stream with error handling
        try:
            audio_stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=input_device_index,
                frames_per_buffer=CHUNK,
                start=False
            )
            audio_stream.start_stream()
            print("Audio stream started successfully")
        except Exception as e:
            print(f"Error opening audio stream: {e}")
            return
        
        print("Listening for voice commands...")
        
        while is_listening:
            try:
                if audio_stream.is_active():
                    data = audio_stream.read(4000, exception_on_overflow=False)
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        if 'text' in result and result['text']:
                            command = result['text'].lower()
                            print(f"Recognized command: {command}")
                            # Process commands directly for better reliability
                            if 'open' in command:
                                command_queue.put(('button', 'open'))
                            elif 'close' in command or 'shut' in command:
                                command_queue.put(('button', 'close'))
                            else:
                                print(f"Unknown command: {command}")
                else:
                    print("Audio stream is not active")
                    break
                time.sleep(0.1)
            except Exception as e:
                print(f"Error in audio processing: {e}")
                break
                
    except Exception as e:
        print(f"Error in process_audio: {e}")
    finally:
        if audio_stream:
            print("Stopping audio stream...")
            if audio_stream.is_active():
                audio_stream.stop_stream()
            if not audio_stream.is_stopped():
                audio_stream.close()
            p.terminate()
            print("Audio stream closed")

def send_command(command):
    """Send command to Arduino"""
    global arduino
    
    if arduino and arduino.is_open:
        try:
            arduino.write(f"{command}\n".encode('utf-8'))
            response = arduino.readline().decode('utf-8').strip()
            return True, response
        except Exception as e:
            return False, str(e)
    return False, "Not connected to Arduino"

# Initialize the Dash app with a dark theme
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.DARKLY],
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}])

# App layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("Voice-Controlled Servo Dashboard", className="text-center my-4"),
            html.Hr(),
        ], width=12)
    ]),
    
    # Main Content
    dbc.Row([
        # Left Column - Controls
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Connection Settings", className="bg-primary text-white"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Select COM Port"),
                            dcc.Dropdown(
                                id='com-port-dropdown',
                                options=[],
                                placeholder="Select a COM port",
                                className="mb-3"
                            ),
                        ], width=8),
                        dbc.Col([
                            html.Label("Baud Rate"),
                            dcc.Dropdown(
                                id='baud-rate-dropdown',
                                options=[
                                    {'label': '9600', 'value': 9600},
                                    {'label': '19200', 'value': 19200},
                                    {'label': '38400', 'value': 38400},
                                    {'label': '57600', 'value': 57600},
                                    {'label': '115200', 'value': 115200},
                                ],
                                value=9600,
                                className="mb-3"
                            ),
                        ], width=4)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Connect", id='connect-btn', color="success", className="w-100"),
                            html.Div(id='connection-status', className="mt-2 text-center")
                        ])
                    ])
                ])
            ], className="mb-4"),
            
            dbc.Card([
                dbc.CardHeader("Voice Commands", className="bg-primary text-white"),
                dbc.CardBody([
                    html.Div([
                        dbc.Button("🎤 Start Listening", id='listen-btn', color="primary", className="w-100 mb-2"),
                        html.Div(id='voice-command-status', className="text-center my-2"),
                        html.Div(id='last-command', className="text-center h4 my-3"),
                    ])
                ])
            ]),
            
            dbc.Card([
                dbc.CardHeader("Manual Control", className="bg-primary text-white"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Open (0°)", id='open-btn', color="info", className="w-100 mb-2")
                        ]),
                        dbc.Col([
                            dbc.Button("Close (90°)", id='close-btn', color="warning", className="w-100 mb-2")
                        ])
                    ]),
                    html.Div([
                        html.Label("Custom Angle (0-180°)"),
                        dcc.Slider(
                            id='angle-slider',
                            min=0,
                            max=180,
                            step=1,
                            value=90,
                            marks={0: '0°', 45: '45°', 90: '90°', 135: '135°', 180: '180°'},
                            className="p-2"
                        ),
                        dbc.Button("Set Angle", id='set-angle-btn', color="primary", className="w-100 mt-2")
                    ])
                ])
            ])
        ], width=12, lg=4),
        
        # Right Column - Visualizations
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Servo Position", className="bg-primary text-white"),
                dbc.CardBody([
                    dcc.Graph(
                        id='servo-gauge',
                        figure=create_gauge(90),  # Initial position at 90°
                        className="h-100"
                    )
                ], className="h-100")
            ], className="h-100")
        ], width=12, lg=8, className="mb-4"),
        
        # Command History
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Command History", className="bg-primary text-white"),
                dbc.CardBody([
                    html.Div(id='command-history', className="command-history")
                ])
            ])
        ], width=12)
    ]),
    
    # Hidden div to store data
    dcc.Store(id='command-store', data=[]),
    dcc.Interval(id='update-interval', interval=1000, n_intervals=0),
    
    # Audio processing components
    dcc.Store(id='audio-processing', data={'is_listening': False}),
    dcc.Store(id='arduino-connection', data={'connected': False, 'port': None, 'baud': None})
], fluid=True, className="p-4")

# Initialize global variables
arduino = None
is_listening = False
command_queue = queue.Queue()

# Initialize Vosk model
if not os.path.exists(MODEL_PATH):
    print(f"Please download the Vosk model to {MODEL_PATH}")
    print("Run: python download_model.py")
    exit(1)

model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, SAMPLE_RATE)

# Audio setup
audio_stream = None
p = pyaudio.PyAudio()



# Callbacks
@app.callback(
    Output('com-port-dropdown', 'options'),
    Input('update-interval', 'n_intervals')
)
def update_com_ports(n):
    """Update available COM ports"""
    ports = [{'label': port.device, 'value': port.device} 
             for port in serial.tools.list_ports.comports()]
    return ports

@app.callback(
    [Output('connection-status', 'children'),
     Output('connect-btn', 'children'),
     Output('connect-btn', 'color'),
     Output('arduino-connection', 'data')],
    [Input('connect-btn', 'n_clicks')],
    [State('com-port-dropdown', 'value'),
     State('baud-rate-dropdown', 'value'),
     State('arduino-connection', 'data')]
)
def toggle_connection(n_clicks, port, baud, connection_data):
    """Handle connection to Arduino"""
    global arduino
    
    if n_clicks is None:
        raise PreventUpdate
    
    if connection_data['connected']:
        # Disconnect
        if arduino and arduino.is_open:
            arduino.close()
        return "Disconnected", "Connect", "success", {'connected': False, 'port': None, 'baud': None}
    
    # Connect
    if not port or not baud:
        return "Please select port and baud rate", "Connect", "success", connection_data
    
    try:
        arduino = serial.Serial(port, baud, timeout=1)
        time.sleep(2)  # Wait for Arduino to initialize
        return f"Connected to {port} @ {baud} baud", "Disconnect", "danger", {'connected': True, 'port': port, 'baud': baud}
    except Exception as e:
        return f"Connection failed: {str(e)}", "Connect", "success", connection_data

@app.callback(
    [Output('voice-command-status', 'children'),
     Output('audio-processing', 'data'),
     Output('last-command', 'children')],
    [Input('listen-btn', 'n_clicks')],
    [State('audio-processing', 'data')]
)
def toggle_listening(n_clicks, data):
    """Toggle voice command listening"""
    global is_listening, audio_thread, p
    
    if n_clicks is None:
        raise PreventUpdate
    
    is_listening = not data.get('is_listening', False)
    
    if is_listening:
        print("\n" + "="*50)
        print("Starting voice command listener...")
        print("="*50 + "\n")
        
        # Reinitialize PyAudio if needed
        try:
            p.terminate()
        except:
            pass
        p = pyaudio.PyAudio()
        
        # Start listening thread
        audio_thread = threading.Thread(target=process_audio, daemon=True)
        audio_thread.start()
        return "🎤 Listening... Speak clearly (say 'open' or 'close')", {'is_listening': True}, ""
    else:
        print("\nStopping voice command listener...\n")
        return "Click to start listening", {'is_listening': False}, ""

@app.callback(
    [Output('servo-gauge', 'figure'),
     Output('command-history', 'children'),
     Output('command-store', 'data')],
    [Input('open-btn', 'n_clicks'),
     Input('close-btn', 'n_clicks'),
     Input('set-angle-btn', 'n_clicks'),
     Input('command-store', 'data')],
    [State('angle-slider', 'value'),
     State('command-store', 'data')]
)
def update_servo(open_clicks, close_clicks, set_angle_clicks, stored_commands, angle, _):
    """Handle servo control buttons and update gauge"""
    # Initialize variables
    ctx = dash.callback_context
    button_id = None
    command = ""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Process voice commands first if any in queue
    try:
        print(f"\n{'='*50}")
        print(f"Command queue size: {command_queue.qsize()}")
        if not command_queue.empty():
            cmd_type, cmd = command_queue.get_nowait()
            print(f"Got command from queue - Type: {cmd_type}, Command: {cmd}")
            if cmd_type == 'button':
                command = cmd  # 'open' or 'close'
                button_id = f"{command}-btn"
                print(f"Processing voice command: {command}")
                print(f"Button ID set to: {button_id}")
            else:
                print(f"Unexpected command type: {cmd_type}")
        else:
            print("No commands in queue")
    except Exception as e:
        print(f"Error processing command queue: {e}")
    
    # If no voice command, check which button was clicked
    if not button_id:
        if not ctx.triggered:
            return create_gauge(90), stored_commands, stored_commands
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Map button IDs to commands
    if button_id == 'open-btn':
        command = "open"
    elif button_id == 'close-btn':
        command = "close"
    elif button_id == 'set-angle-btn':
        command = f"set {angle}"
    else:
        return create_gauge(90), stored_commands, stored_commands
    
    # Send command to Arduino
    success = False
    response = ""
    
    try:
        if command:  # Only send if we have a valid command
            print(f"\nPreparing to send command: {command}")
            print(f"Arduino connected: {arduino is not None and arduino.is_open if arduino else False}")
            if arduino:
                print(f"Arduino port: {arduino.port}, is_open: {arduino.is_open}")
            
            print(f"Sending command to Arduino: {command}")
            success, response = send_command(command)
            print(f"Command sent. Success: {success}, Response: {response}")
            
            # Update command history
            if success:
                new_command = {
                    'time': timestamp,
                    'command': command,
                    'response': response
                }
                stored_commands = [new_command] + stored_commands[:9]  # Keep last 10 commands
        else:
            print("No valid command to send to Arduino")
    except Exception as e:
        print(f"Error in command processing: {e}")
        response = str(e)
    
    # Create history items
    history_items = []
    for cmd in stored_commands:
        history_items.append(
            dbc.ListGroupItem([
                html.Div([
                    html.Small(cmd['time'], className="text-muted"),
                    html.Strong(f" {cmd['command'].title()}", className="ms-2")
                ]),
                html.Small(cmd['response'], className="text-info")
            ], className="d-flex justify-content-between align-items-start")
        )
    
    # Update gauge based on command
    if command == "open":
        angle = 0
    elif command == "close":
        angle = 90
    elif command.startswith("set"):
        angle = int(command.split()[1])
    
    return create_gauge(angle), history_items, stored_commands

# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=8050)
