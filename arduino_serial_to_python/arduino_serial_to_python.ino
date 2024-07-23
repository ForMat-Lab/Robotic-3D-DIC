/*
  Blink with Serial Communication

  Turns an LED on for one second, then off for one second, repeatedly.
  Sends a signal via serial communication to capture an image three seconds after the LED turns on.

  This example code is in the public domain.
*/

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);  // Initialize the LED pin as an output
  Serial.begin(9600);            // Initialize serial communication at 9600 bps
}

void loop() {
  digitalWrite(LED_BUILTIN, HIGH);  // Turn the LED on
  delay(1000);                      // Wait for one second
  digitalWrite(LED_BUILTIN, LOW);   // Turn the LED off
  delay(2000);                      // Wait for two more seconds (total 3 seconds from LED on)
  Serial.println("CAPTURE");        // Send a capture signal to the serial port
  delay(1000);                      // Wait for one second before repeating the loop
}
