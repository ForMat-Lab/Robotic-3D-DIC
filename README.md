# Project Setup Instructions

This README provides instructions on how to install the necessary Python libraries for the experiment image capture and PDF report generation project. You can install these libraries either in a virtual environment or directly on your system. It is recommended to set this up in the directory of the script.

## Required Libraries

The following libraries are required for this project:

- `os` (built-in)
- `cv2` (OpenCV)
- `pypylon`
- `datetime` (built-in)
- `reportlab`
- `logging` (built-in)

## Installation Instructions

First, navigate to the directory containing the script.

### Using a Virtual Environment

Create a virtual environment (optional but recommended):

bash

``python -m venv venv``


Activate the virtual environment:

On Windows:

bash

''venv\Scripts\activate''


On macOS and Linux:

bash

''source venv/bin/activate''



Install the required libraries:

bash

``pip install opencv-python-headless pypylon reportlab``


### Without a Virtual Environment

If you choose not to use a virtual environment, you can install the required libraries directly on your system:

bash

``pip install opencv-python-headless pypylon reportlab``


## Setting Up the Arduino

To use an Arduino as the trigger, you will need to set up the Arduino to send a signal to your system when it detects a trigger event. Here are the steps:

1. **Gather the required components**:
    - Arduino board (e.g., Arduino Uno)
    - USB cable to connect the Arduino to your computer
    
    

2. **Install the Arduino IDE**:
    - Download and install the Arduino IDE from the [official website](https://www.arduino.cc/en/software).

3. **Write the Arduino code (oprtional)** :
    - Open the Arduino IDE and write a simple sketch to send a signal to the computer. For example:

\`\`\`cpp
const int triggerPin = 2; // Pin connected to the trigger sensor
void setup() {
    Serial.begin(9600);
    pinMode(triggerPin, INPUT);
}

void loop() {
    if (digitalRead(triggerPin) == HIGH) {
        Serial.println("TRIGGER");
        delay(1000); // Debounce delay
    }
}
\`\`\`

4. **Upload the code to the Arduino**:
    - Connect your Arduino to your computer using the USB cable.
    - Select the correct board and port from the Tools menu.
    - Click the Upload button in the Arduino IDE.

5. **Test the Arduino setup**:
    - Open the Serial Monitor in the Arduino IDE to ensure it is sending "TRIGGER" messages when the sensor is activated.

## Running the Code

### Steps

1. **Initialize cameras**: Ensure your cameras are connected and recognized by the Basler Pylon SDK.

2. **Run the script**:

bash

``python script.py``


3. Follow the prompts to enter:
    - Experiment name (e.g., Calibration, Speckle, Other)
    - Experimental description
    - Number of samples in the experiment
    - Exposure time (in microseconds)
    - Press Enter to start the experiment

4. **Monitor for triggers**:
    - Modify your Python script to listen for the "TRIGGER" message from the Arduino over the serial port and initiate image capture. 



# Initialize serial connection (adjust COM port as needed)
``ser = serial.Serial('COM3', 9600)``




5. **Terminate the script**: During execution, press 'q' to quit and terminate the image capture process.

## Notes

- Ensure your Arduino is properly set up and connected to your computer.
- Modify the trigger detection logic as per your specific setup.

## Troubleshooting

### Common Issues

- **Failed to initialize cameras**: Ensure that the cameras are properly connected and the Pylon SDK is correctly installed.
- **TimeoutException during image retrieval**: Check camera connections and ensure the exposure time is correctly set.
- **Arduino not detected**: Ensure the correct COM port is selected and the Arduino drivers are installed.

## Logging

- Logs are configured to provide detailed information and errors, which can be helpful for troubleshooting.
- Check the log messages in the console for any errors and follow the suggested actions.

## References

For further assistance, refer to the official documentation of the libraries used:

- [OpenCV Documentation](https://docs.opencv.org/)
- [ReportLab Documentation](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [Pypylon Documentation](https://github.com/basler/pypylon)
- [Arduino Documentation](https://www.arduino.cc/en/Tutorial/HomePage)
