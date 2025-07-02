# Virtual Strain Toolkit

This repository includes three Python scripts for simulating, visualizing, and exporting virtual strain image sequences.

---

## 🧪 1. VirtualStrain_generation.py

**Purpose:**  
Generates a sequence of images that simulate stretching and recovery along horizontal (`x`) and vertical (`y`) directions, mimicking strain deformation.

**Key Features:**
- Adds a white frame to avoid clipping during transformations.
- Stretches and shrinks the image incrementally.
- Outputs a complete image sequence in a dated folder.

---

## 🎥 2. Strain_series_video.py

**Purpose:**  
Creates a video from a sequence of images stored in a selected subfolder.

**Key Features:**
- Prompts user to select a folder of images.
- Repeats each image to simulate a time-lapse effect.
- Saves output as a `.avi` video file.

---

## 🖥️ 3. strain_series_simulation.py

**Purpose:**  
Displays images in fullscreen, simulating real-time strain playback.

**Key Features:**
- Allows folder selection and fullscreen playback.
- Resizes and centers images to fit screen.
- Waits a fixed time between images or until interrupted.

---

## 🔧 Dependencies

All scripts require the following Python libraries:

```bash
pip install opencv-python pillow tqdm numpy
