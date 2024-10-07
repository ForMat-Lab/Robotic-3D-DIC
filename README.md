# MycoRobo3D-DIC: Automated Imaging Acquisition System

## Overview

**MycoRobo3D-DIC** is an automated imaging acquisition system designed for high-throughput studies. It integrates robotic automation with imaging hardware to capture images at predefined sample positions. The system facilitates synchronized movements and image captures between an ABB robot, Basler cameras, and an Arduino microcontroller.

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
- **Cameras**: Basler cameras compatible with Pylon SDK
- **Microcontroller**: Arduino Uno or compatible board
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
2. Execute the following commands (do not include the `$` sign):

   ```bash
   conda create --name mycorobo3d-dic python=3.8
   conda activate mycorobo3d-dic
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

Before running the experiment, configure the `config.json` file according to your setup. Here is an example configuration:

```json
{
    "experiment_name": "TestExperiment",
    "number_of_samples": 9,
    "interval_minutes": 30,
    "total_runs": -1,
    "output_folder": "captured_images",
    "display_scale_factor": 0.25,
    "camera_settings": {
        "width": 2448,
        "height": 2048,
        "exposure_time": 100000,
        "auto_exposure": true
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
   conda activate mycorobo3d-dic
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

The **MycoRobo3D-DIC** system uses digital signals to synchronize operations between the ABB robot, the Arduino microcontroller, and the Python software. This section explains how these signals are mapped, their directions, and how they facilitate communication between the components.

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
| `DI_DIC_0` | Pin **2**   | Arduino → Robot          | `DI_RUN`              | Arduino signals robot to start the run        |
| `DI_DIC_1` | Pin **3**   | Arduino → Robot          | `DI_CAPTURE_COMPLETE` | Arduino signals that image capture is complete|
| `DO_DIC_0` | Pin **6**   | Robot → Arduino          | `DO_RUN_COMPLETE`     | Robot signals that the run is complete        |
| `DO_DIC_1` | Pin **7**   | Robot → Arduino          | `DO_CAPTURE`          | Robot signals to start image capture          |

**Notes**:

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
- **Year**: 2024

---

If you have any questions or need further assistance, please contact the maintainers.