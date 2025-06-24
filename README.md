# Robotic-3D-DIC: Automated Imaging Acquisition System

## Overview

**Robotic-3D-DIC** is an automated imaging acquisition system designed for high-throughput studies. It integrates robotic automation with imaging hardware to capture images at predefined sample positions. The system facilitates synchronized movements and image captures between an ABB robot, Basler cameras, and an Arduino microcontroller.

---

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation and Setup](#installation-and-setup)
  - [1. Install Basler Pylon Software](#1-install-basler-pylon-software)
  - [2. Install Anaconda](#2-install-anaconda)
  - [3. Create Anaconda Environment and Install Libraries](#3-create-anaconda-environment-and-install-libraries)
  - [4. Install Arduino IDE](#4-install-arduino-ide)
  - [5. Flash Arduino with StandardFirmata](#5-flash-arduino-with-standardfirmata)
- [Usage](#usage)
  - [Configuration](#configuration)
    - [Configuration Options](#configuration-options)
    - [Sample Configuration File](#sample-configuration-file)
  - [Running the Experiment](#running-the-experiment)
- [Signal Mapping and Communication Flow](#signal-mapping-and-communication-flow)
  - [Overview](#overview-1)
  - [Signal Definitions and Flow Logic](#signal-definitions-and-flow-logic)
  - [Signal Mapping Table](#signal-mapping-table)
  - [Communication Flow Logic](#communication-flow-logic)
- [Acknowledgments](#acknowledgments)

---

## System Requirements

- **Operating System**: Windows (required for Basler Pylon Software)
- **Cameras**: Basler cameras compatible with the Pylon SDK
- **Microcontroller**: Arduino Uno or a compatible board
- **Robot**: ABB robot with RAPID programming capability
- **Software**:
  - Basler Pylon Software
  - Anaconda Python Distribution
  - Arduino IDE

---

## Installation and Setup

### 1. Install Basler Pylon Software

Download and install the Basler Pylon Software from the official website:

- **[Basler Pylon Software Download](https://www2.baslerweb.com/en/downloads/software-downloads)**

**Installation Steps**:

- **Profiles**: Select **Developer** during installation.
- **Interfaces**: Choose **USB** as the interface type.

---

### 2. Install Anaconda

Download and install Anaconda for Python 3.x from the official website:

- **[Anaconda Installation Guide](https://docs.anaconda.com/anaconda/install/windows/)**

---

### 3. Create Anaconda Environment and Install Libraries

1. **Open Anaconda Prompt**.
2. Execute the following commands:

   ```bash
   conda create --name Robotic-3D-dic python=3.8
   conda activate Robotic-3D-dic
   pip install pypylon opencv-python pyfirmata reportlab
   ```

---

### 4. Install Arduino IDE

Download and install the Arduino IDE from the official website:

- **[Arduino IDE Download](https://www.arduino.cc/en/software)**

---

### 5. Flash Arduino with StandardFirmata

1. **Open the Arduino IDE**.
2. Navigate to **Tools > Manage Libraries**.
3. **Search** for **Firmata** and **install** it.
4. Go to **File > Examples > Firmata > StandardFirmata**.
5. **Upload** the **StandardFirmata** sketch to your Arduino board.

---

## Usage

### Configuration

Before running the experiment, you must set up a configuration file (typically named `config.json`) that specifies system parameters. The configuration is validated at startup, so ensure all required keys are provided and are of the correct type.

#### Configuration Options

**Top-Level Keys:**

- **`experiment_name`** (string):  
  The name of the experiment.  
  _Example_: `'TestExperiment'`

- **`number_of_samples`** (integer):  
  The number of sample positions to capture images from during each run.  
  _Example_: `9`

- **`interval_minutes`** (integer, default: `30`):  
  The break interval (in minutes) between consecutive runs.

- **`total_runs`** (integer, default: `-1`):  
  The total number of runs to perform. Use `-1` for an indefinite number of runs until manually terminated.

- **`output_folder`** (string):  
  The directory where captured images, CSV logs, and the PDF report will be saved.

- **`display_scale_factor`** (number, default: `0.5`):  
  Factor used to scale images for display.

- **`display_images`** (boolean, default: `true`):  
  Whether to display images during acquisition.

- **`turn_off_cameras_between_runs`** (boolean, default: `true`):  
  If set to `true`, the cameras will be turned off during the break interval between runs.

- **`interval_calculation_mode`** (string, default: `'constant_interval'`):  
  Defines how the break interval is calculated. Allowed values are `'constant_interval'` and `'constant_break'`.

**Camera Settings (`camera_settings` object):**

- **`width`** (integer):  
  The image width in pixels.
  
- **`height`** (integer):  
  The image height in pixels.
  
- **`exposure_time`** (number):  
  The exposure time in microseconds.
  
- **`exposure_mode`** (string, default: `'Manual'`):  
  Sets the exposure mode. Allowed values:
  - `'Manual'`: Uses the specified `exposure_time`.
  - `'Continuous'`: Enables auto-exposure continuously.
  - `'SetOnce'`: Auto-exposes once per sample capture and then uses the learned exposure.
  
- **`scale_factor`** (number):  
  (If needed) Scale factor used for generating the PDF report’s camera settings section.

**Arduino Settings (`arduino_settings` object):**

- **`input_pins`** (object):  
  A mapping of Arduino digital input pins. Must include:
  - **`DO_CAPTURE`** (integer): Pin used to detect a capture signal from the robot.
  - **`DO_RUN_COMPLETE`** (integer): Pin used to detect when a run is complete.
  
- **`output_pins`** (object):  
  A mapping of Arduino digital output pins. Must include:
  - **`DI_RUN`** (integer): Pin used to signal the robot to start a run.
  - **`DI_CAPTURE_COMPLETE`** (integer): Pin used to signal the robot that image capture is complete.
  
- **`auto_detect_port`** (boolean, default: `false`):  
  If set to `true`, the system will attempt to auto-detect the Arduino port.
  
- **`port`** (string, *required if* `auto_detect_port` is `false`):  
  The COM port or device file for the Arduino connection.

#### Sample Configuration File

Below is an example `config.json` file:

```json
{
    "experiment_name": "TestExperiment",
    "number_of_samples": 9,
    "total_runs": -1,
    "interval_minutes": 30,
    "interval_calculation_mode": "constant_interval",
    "turn_off_cameras_between_runs": false,
    "output_folder": "captured_images",
    "display_scale_factor": 0.25,
    "display_images": true,
    "camera_settings": {
        "width": 2448,
        "height": 2048,
        "exposure_time": 100000,
        "exposure_mode": "Manual"
    },
    "arduino_settings": {
        "port": "COM3",
        "auto_detect_port": true,
        "input_pins": {
            "DO_RUN_COMPLETE": 6,
            "DO_CAPTURE": 7
        },
        "output_pins": {
            "DI_RUN": 2,
            "DI_CAPTURE_COMPLETE": 3
        }
    }
}
```

**Note**: Adjust the parameters to match your experimental setup, including the number of samples, camera settings, and Arduino pin configurations.

---

### Running the Experiment

1. **Connect Hardware**:

   - Ensure that the Basler cameras are connected via USB.
   - Connect the Arduino to your computer via USB.
   - Set up the ABB robot and ensure it is connected to the Arduino via the appropriate I/O channels.

2. **Activate the Anaconda Environment**:

   ```bash
   conda activate Robotic-3D-dic
   ```

3. **Run the Main Script**:

   ```bash
   python main.py
   ```

4. **Follow On-Screen Instructions**:

   - The script will display a header and prompt you to start the experiment.
   - Type `'start'` to begin or `'quit'` to exit.
   - The experiment will run according to the configuration settings.
   - The script provides logging information about the experiment's progress.

---

## Signal Mapping and Communication Flow

### Overview

The **Robotic-3D-DIC** system uses digital signals to synchronize operations between the ABB robot, the Arduino microcontroller, and the Python software. This section explains how these signals are mapped, their directions, and how they facilitate communication between the components.

### Signal Definitions and Flow Logic

#### Signals from Robot to Arduino (Inputs to Arduino)

- **`DO_CAPTURE`**: The robot sets this signal HIGH to indicate that it is in position and ready for the Python software to capture images.
- **`DO_RUN_COMPLETE`**: The robot sets this signal HIGH to indicate that it has completed a run.

#### Signals from Arduino to Robot (Outputs from Arduino)

- **`DI_RUN`**: The Arduino sets this signal HIGH to tell the robot to start a run.
- **`DI_CAPTURE_COMPLETE`**: The Arduino sets this signal HIGH to tell the robot that image capture is complete, and it can proceed to the next position.

### Signal Mapping Table

The following table summarizes the signals, their Arduino pin assignments, directions, corresponding variables in the Python code, and descriptions:

| Signal Name (Robot)      | Arduino Pin | Direction                | Python Variable             | Description                                    |
|--------------------------|-------------|--------------------------|-----------------------------|------------------------------------------------|
| `DI_DIC_0` | Pin **2**   | Arduino → Robot          | `DI_RUN`              | Arduino signals the robot to start the run        |
| `DI_DIC_1` | Pin **3**   | Arduino → Robot          | `DI_CAPTURE_COMPLETE` | Arduino signals that image capture is complete|
| `DO_DIC_0` | Pin **6**   | Robot → Arduino          | `DO_RUN_COMPLETE`     | Robot signals that the run is complete        |
| `DO_DIC_1` | Pin **7**   | Robot → Arduino          | `DO_CAPTURE`          | Robot signals to start image capture          |

*Notes*:

- **Direction**: Indicates the flow of the signal. For example, "Robot → Arduino" means the robot sets the signal, and the Arduino reads it.
- **Arduino Pin**: The digital pin number on the Arduino board where the signal is connected.
- **Python Variable**: The variable name used in the Python code (`main.py`) to reference the pin.

### Communication Flow Logic

#### 1. Session Start

- **Arduino**: Sets `DI_RUN` HIGH to signal the robot to start the run.
- **Robot**: Waits for `DI_RUN` to be HIGH before beginning the run.

#### 2. Robot Movement and Image Capture

- **Robot**: Moves to the first sample position.
- **Robot**: Sets `DO_CAPTURE` HIGH to signal the Arduino/Python that it is ready for image capture.
- **Arduino/Python**:
  - Detects `DO_CAPTURE` rising edge (0 -> 1).
  - Initiates image capture and save using the cameras.
  - Sets `DI_CAPTURE_COMPLETE` HIGH to signal the robot that image capture is complete.
- **Robot**:
  - Waits for `DI_CAPTURE_COMPLETE` to be HIGH before moving to the next position.
  - Resets `DO_CAPTURE` to LOW after acknowledging `DI_CAPTURE_COMPLETE`.

- **This process repeats** for each sample position.

#### 3. Session Completion

- **Robot**: After completing movements to all sample positions, sets `DO_RUN_COMPLETE` HIGH to indicate the run is complete.
- **Arduino/Python**:
  - Detects `DO_RUN_COMPLETE` rising edge (0 -> 1).
  - Resets `DI_RUN` to LOW to acknowledge the run completion.
- **Robot**:
  - Waits for `DI_RUN` to be LOW before resetting `DO_RUN_COMPLETE` to LOW.
  - Ends the run and returns to the home position.

#### 4. Break Interval and Next Session

- **Python Software**:
  - Enters a break period as configured (e.g., 30 minutes).
  - After the break, repeats the process starting from step 1 for the next run, if applicable.

---

## Acknowledgments

- **Author**: Özgüç B. Çapunaman
- **Maintainers**: Özgüç B. Çapunaman, Alale Mohseni
- **Institution**: ForMatLab @ Penn State University
- **Year**: 2025

---

If you have any questions or need further assistance, please contact the maintainers.