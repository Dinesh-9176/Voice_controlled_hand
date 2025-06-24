#include <Servo.h>

// Create a servo object
Servo myServo;

// Define the servo pin
const int servoPin = 10;

void setup() {
  // Attach the servo to the pin
  myServo.attach(servoPin);
  
  // Initialize serial communication for debugging
  Serial.begin(9600);
  
  // Move servo to 90 degrees
  myServo.write(90);
  Serial.println("Servo set to 90 degrees");
}

void loop() {
  // Nothing to do here, servo will stay at 90 degrees
}