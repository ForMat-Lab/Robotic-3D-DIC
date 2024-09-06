import os
import cv2
import logging
from datetime import datetime
from pypylon import pylon
from util import load_config, generate_pdf_report, get_folder_size
from src.Arduino import ArduinoController
from src.Camera import Camera

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_components(config):
    """Initialize Arduino and Cameras."""
    # Initialize Arduino
    arduino_controller = ArduinoController()

    # Initialize cameras
    camera = Camera(
        width=config['camera_settings']['width'],
        height=config['camera_settings']['height'],
        exposure_time=config['camera_settings']['exposure_time']
    )
    camera.initialize_cameras()

    logger.info(f"{len(camera.cameras)} cameras initialized.")
    return arduino_controller, camera

def capture_images(arduino_controller, camera, config):
    """Capture images and generate PDF report."""
    num_samples = config['number_of_samples']
    output_folder = os.path.join(config['output_folder'], datetime.now().strftime('%Y-%m-%d_%H-%M-%S'), config['experiment_name'])
    os.makedirs(output_folder, exist_ok=True)

    trigger_pin = config['arduino']['trigger_pin']

    # Record start time
    start_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    logger.info(f"Experiment started at {start_time}")

    # Setup digital input pin for Arduino
    arduino_controller.setup_digital_input(trigger_pin)

    sample_index = 0
    visit_counts = [0] * num_samples
    capture_continues = True

    while capture_continues:
        # Wait for a capture signal from Arduino
        if arduino_controller.check_rising_edge(trigger_pin):
            logger.info(f"Capture signal received for Sample {sample_index + 1}")

            # Capture images from all cameras
            frames = camera.grab_frames()
            if frames:
                # Increment the visit count for the current sample
                visit_counts[sample_index] += 1

                # Resize and display frames
                camera.display_frames(frames)

                # Save images
                sample_folder = os.path.join(output_folder, f'Sample_{sample_index + 1}')
                os.makedirs(sample_folder, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                for j, frame in enumerate(frames):
                    filename = f'sample_{sample_index + 1}_{timestamp}_{j}.tif'
                    cv2.imwrite(os.path.join(sample_folder, filename), frame, [cv2.IMWRITE_TIFF_COMPRESSION, 1])
                    logger.info(f"Image captured for Sample {sample_index + 1}. Filename: {filename}")

            # Move to the next sample after capturing images
            sample_index = (sample_index + 1) % num_samples

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            capture_continues = False

    # Stop grabbing and close all cameras
    camera.close_cameras()

    # Record end time
    end_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    logger.info(f"Experiment ended at {end_time}")

    # Calculate the total size of the output folder
    total_filesize_str = f"{get_folder_size(output_folder) / (1024 * 1024):.2f} MB"

    # Generate PDF report
    generate_pdf_report(
        config=config,
        start_time=start_time,
        end_time=end_time,
        num_samples=num_samples,
        visit_counts=visit_counts,
        output_folder=output_folder
    )

if __name__ == "__main__":
    try:
        # Load configuration
        config = load_config()

        # Initialize Arduino and Cameras
        arduino_controller, camera = initialize_components(config)

        # Capture images and generate report
        capture_images(arduino_controller, camera, config)

    finally:
        # Ensure that the Arduino connection is always closed
        arduino_controller.close()