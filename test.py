# main.py

import os
from datetime import datetime
import logging
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from classes.Arduino import ArduinoController
from classes.camera import Camera  # Import the Camera class

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_folder_size(folder_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)
    return total_size

def capture_images(camera_controller, num_samples, output_folder, experiment_name, experiment_description, arduino_controller, trigger_pin):
    start_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    logger.info(f"Experiment started at {start_time}")

    # Create sample folders
    sample_folders = [os.path.join(output_folder, f'Sample_{i}') for i in range(1, num_samples + 1)]
    for folder in sample_folders:
        os.makedirs(folder, exist_ok=True)

    # Set camera settings
    camera_controller.set_camera_settings()

    # Setup the digital input pin
    arduino_controller.setup_digital_input(trigger_pin)

    sample_index = 0
    visit_counts = [0] * num_samples
    capture_continues = True

    while capture_continues:
        if arduino_controller.check_rising_edge(trigger_pin):
            logger.info(f"Capture signal received for Sample {sample_index + 1}")

            # Grab frames
            frames = camera_controller.grab_frames()

            # Display and save the frames
            camera_controller.display_frames(frames)
            camera_controller.save_frames(frames, sample_folders[sample_index], sample_index, visit_counts[sample_index])

            visit_counts[sample_index] += 1
            sample_index = (sample_index + 1) % num_samples

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            capture_continues = False

    camera_controller.close_cameras()

    end_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    total_filesize = get_folder_size(output_folder)
    total_filesize_str = f"{total_filesize / (1024 * 1024):.2f} MB"

    generate_pdf_report(start_time, end_time, num_samples, visit_counts, experiment_name, experiment_description, output_folder, 
                        ", ".join([camera.GetDeviceInfo().GetModelName() for camera in camera_controller.cameras]),
                        "Arduino", "3 seconds", output_folder, "TIFF", total_filesize_str, "None", "3 seconds")

def generate_pdf_report(start_time, end_time, num_samples, visit_counts, experiment_name, experiment_description, output_folder, 
                        recording_devices, trigger_devices, trigger_interval, image_folder_filepath, image_format, total_filesize, file_compression, delay_to_trigger):
    # (PDF generation code remains unchanged)
    pass

if __name__ == "__main__":
    arduino_controller = ArduinoController()
    trigger_pin = 6  # Set to the pin you're using for the trigger

    try:
        # Initialize the Camera class with configurable parameters
        camera_controller = Camera(width=1920, height=1080, exposure_time=10000, timeout=3000, scale_factor=0.25)
        camera_controller.initialize_cameras()

        # Experiment details
        experiment_name = input("Enter the experiment name (Calibration, Speckle, Other): ")
        logger.info(f"Experiment name set: {experiment_name}")

        experiment_description = input("Enter an experimental description: ")
        logger.info(f"Experiment description set: {experiment_description}")

        num_samples = int(input("Enter the number of samples in a single experiment: "))
        logger.info(f"Number of samples set: {num_samples}")

        # Specify the output folder
        output_folder = os.path.join("captured_images", datetime.now().strftime('%Y-%m-%d_%H-%M-%S'), experiment_name)
        os.makedirs(output_folder, exist_ok=True)

        # Capture images and generate a report
        capture_images(camera_controller, num_samples, output_folder, experiment_name, experiment_description, arduino_controller, trigger_pin)

    finally:
        arduino_controller.close()