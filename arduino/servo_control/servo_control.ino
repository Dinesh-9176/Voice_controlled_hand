#include <Servo.h>

// Create a servo object
Servo myServo;

// Define servo pin
const int SERVO_PIN = 9;  // Servo on pin 9

// Define positions (0-180 degrees)
const int OPEN_POS = 0;     // Open position (0°)
const int CLOSE_POS = 90;   // Close position (90°)

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  while (!Serial) {
    ; // Wait for serial port to connect
  }
  
  // Attach the servo to its pin
  if (myServo.attach(SERVO_PIN) == 0) {
    Serial.println("Failed to attach servo! Check wiring.");
  } else {
    Serial.println("Servo attached successfully to pin 9");
  }
  
  // Start with servo in closed position
  closeServo();
  Serial.println("\nSingle Servo Control Ready!");
  Serial.println("Send 'open' or 'shut' to control the servo");
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    // Echo back the received command for debugging
    Serial.print("\nReceived command: ");
    Serial.println(command);
    
    // Process commands
    if (command == "open") {
      Serial.println("Opening servo...");
      openServo();
    } 
    else if (command == "shut" || command == "close") {
      Serial.println("Closing servo...");
      closeServo();
    }
    else {
      Serial.println("Unknown command. Use 'open' or 'close'");
    }
  }
}

void openServo() {
  moveServo(OPEN_POS);
  Serial.println("Servo: Opened to 0°");
}

void closeServo() {
  moveServo(CLOSE_POS);
  Serial.println("Servo: Closed to 90°");
}

// Function to move the servo to a specific position
void moveServo(int angle) {
  // Constrain the angle to valid range (0-180)
  angle = constrain(angle, 0, 180);
  
  Serial.print("Moving to ");
  Serial.print(angle);
  Serial.println("°");
  
  // Move the servo to the specified angle
  myServo.write(angle);
  
  // Add a small delay to allow the servo to reach the position
  delay(500);
}