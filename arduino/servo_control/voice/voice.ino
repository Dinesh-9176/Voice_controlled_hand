#include <Servo.h>

Servo myServo;          // Create servo object
const int servoPin = 10; // Servo signal pin

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
  // Attach the servo to the pin
  myServo.attach(servoPin);
  
  // Move to initial position (closed)
  myServo.write(180);
  Serial.println("Servo initialized to CLOSED position (180 degrees)");
  Serial.println("Send '0' to open or '180' to close");
}

void loop() {
  if (Serial.available() > 0) {
    // Read the incoming command
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    if (input == "0") {
      myServo.write(0);
      Serial.println("Opened (0 degrees)");
    } 
    else if (input == "180") {
      myServo.write(180);
      Serial.println("Closed (180 degrees)");
    }
    else {
      Serial.println("Invalid command. Send '0' to open or '180' to close");
    }
  }
}