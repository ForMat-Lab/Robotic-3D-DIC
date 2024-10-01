# MycoRobo3D-DIC: Automated Imaging Acquisition System

## Overview

**MycoRobo3D-DIC** is an automated imaging acquisition system designed for high-throughput studies. It integrates robotic automation with imaging hardware to capture images at predefined sample positions. The system facilitates synchronized movements and image captures between an ABB robot, Basler cameras, and an Arduino microcontroller.

---

## Table of Contents

- [Features](#features)
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
- [License](#license)
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

- **[Basler Pylon Software Download](https://www.baslerweb.com/en/products/software/basler-pylon-camera-software-suite/)**

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
    "number_of_samples": 10,
    "interval_minutes": 30,
    "total_runs": -1,
    "output_folder": "captured_images",
    "camera_settings": {
        "width": 2448,
        "height": 2048,
        "exposure_time": 100000,
        "auto_exposure": true,
        "auto_exposure_mode": "Once",
        "scale_factor": 0.5
    },
    "arduino_settings": {
        "input_pins": {
            "DO_CAPTURE": 6,
            "DO_RUN_COMPLETE": 7
        },
        "output_pins": {
            "DI_START": 8,
            "DI_CAPTURE_COMPLETE": 9
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
   - Type `'start'` to begin or `'q'` to exit.
   - The experiment will run according to the configuration settings.

5. **Monitor the Experiment**:

   - The script provides logging information about the experiment's progress.
   - You can exit the experiment at any time by pressing `Ctrl+C`.

---

## Acknowledgments

- **Author**: Özgüç B. Çapunaman
- **Maintainers**: Özgüç B. Çapunaman, Alale Mohseni
- **Institution**: ForMatLab @ Penn State University
- **Year**: 2024

---

If you have any questions or need further assistance, please contact the maintainers.