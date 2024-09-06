import os
import time
import cv2
import logging
from datetime import datetime
from pypylon import pylon
from src.util import load_config, generate_pdf_report, get_folder_size
from src.Arduino import ArduinoController
from src.Camera import Camera

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_arduino(config):
    """Initialize Arduino based on the configuration."""
    arduino_controller = ArduinoController()
    trigger_pin = config['arduino_settings']['trigger_pin']
    arduino_controller.setup_digital_input(trigger_pin)
    logger.info("Arduino initialized with trigger pin: %d", trigger_pin)
    return arduino_controller

def initialize_cameras(config):
    """Initialize and configure cameras based on the configuration."""
    camera = Camera(
        width=config['camera_settings']['width'],
        height=config['camera_settings']['height'],
        exposure_time=config['camera_settings']['exposure_time'],
        scale_factor=config['camera_settings'].get('scale_factor', 0.5)
    )
    camera.initialize_cameras()

    # Set camera exposure mode (manual or auto) based on the configuration
    if config['camera_settings'].get('auto_exposure', False):
        camera.set_auto_exposure(config['camera_settings'].get('auto_exposure_mode', 'Once'))
    else:
        camera.set_camera_settings()

    logger.info(f"Cameras initialized and configured with width: {config['camera_settings']['width']}, "
                f"height: {config['camera_settings']['height']}, exposure mode: "
                f"{'Auto' if config['camera_settings'].get('auto_exposure', False) else 'Manual'}")

    return camera

def capture_images(cameras, arduino_controller, config, stream=False):
    """Continuously stream frames, save only when triggered by Arduino."""
    num_samples = config['number_of_samples']
    output_folder = os.path.join(config['output_folder'], datetime.now().strftime('%Y-%m-%d_%H-%M-%S'), config['experiment_name'])
    os.makedirs(output_folder, exist_ok=True)

    visit_counts = [0] * num_samples
    start_time = time.strftime('%Y-%m-%d_%H-%M-%S')
    logger.info(f"Experiment started at {start_time}")

    sample_folders = [os.path.join(output_folder, f'Sample_{i}') for i in range(1, num_samples + 1)]
    for folder in sample_folders:
        os.makedirs(folder, exist_ok=True)

    # Ensure cameras start grabbing frames
    cameras.start_grabbing()

    sample_index = 0
    capture_continues = True

    while capture_continues and sample_index < num_samples:
        frames = cameras.grab_frames()

        # Handle frame grabbing failure
        if not frames:
            logger.error("Error: Camera is not grabbing frames.")
            continue

        # Always stream frames continuously
        if stream:
            stream_frames(frames, cameras.scale_factor)

        # Save images only when triggered by the Arduino
        if arduino_controller.check_rising_edge(config['arduino_settings']['trigger_pin']):
            logger.info(f"Signal received for sample {sample_index + 1}")
            save_images(frames, sample_folders[sample_index], sample_index, visit_counts)
            logger.info(f"Captured and saved images for Sample {sample_index + 1}")
            sample_index += 1

        # Check if 'q' key is pressed to quit
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            capture_continues = False

    cameras.close_cameras()
    end_time = time.strftime('%Y-%m-%d_%H-%M-%S')

    total_filesize = get_folder_size(output_folder)
    generate_pdf_report(config, start_time, end_time, num_samples, visit_counts, output_folder)
    logger.info(f"Experiment ended at {end_time}, total size: {total_filesize / (1024 * 1024):.2f} MB")

def save_images(frames, sample_folder, sample_index, visit_counts):
    """Save the captured frames to the sample folder."""
    visit_counts[sample_index] += 1
    timestamp = time.strftime('%Y%m%d_%H%M%S', time.localtime())
    visit_count_str = f'{visit_counts[sample_index]:04}'

    for idx, frame in enumerate(frames):
        filename = f'sample_{sample_index + 1}_{timestamp}_{visit_count_str}_{idx}.tif'
        cv2.imwrite(os.path.join(sample_folder, filename), frame, [cv2.IMWRITE_TIFF_COMPRESSION, 1])
        logger.info(f"Saved image: {filename}")

def stream_frames(frames, scale_factor=0.25):
    """Display frames in a window using OpenCV."""
    resized_frames = [cv2.resize(frame, (0, 0), fx=scale_factor, fy=scale_factor) for frame in frames]
    concatenated_frame = cv2.hconcat(resized_frames)
    cv2.imshow('Captured Images', concatenated_frame)

if __name__ == "__main__":
    try:
        # Load configuration
        config = load_config()

        # Initialize Arduino and Cameras
        arduino_controller = initialize_arduino(config)
        cameras = initialize_cameras(config)

        # Capture images from each sample and generate PDF report
        capture_images(cameras, arduino_controller, config, stream=True)

    finally:
        # Ensure Arduino is properly closed
        if arduino_controller:
            arduino_controller.close()
        if cameras:
            cameras.close_cameras()
        logger.info("Experiment completed and resources released.")