import os
import time
import cv2
import numpy as np
import logging
from datetime import datetime, timedelta
from src.util import load_config, generate_pdf_report, get_folder_size
from src.Arduino import ArduinoController
from src.Camera import Camera

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Experiment:
    def __init__(self, config):

        self._header = r'''
8""8""8                   8"""8                     eeee  8""""8      8""""8 8  8""""8 
8  8  8 e    e eeee eeeee 8   8  eeeee eeeee  eeeee    8  8    8      8    8 8  8    " 
8e 8  8 8    8 8  8 8  88 8eee8e 8  88 8   8  8  88    8  8e   8      8e   8 8e 8e     
88 8  8 8eeee8 8e   8   8 88   8 8   8 8eee8e 8   8 eee8  88   8 eeee 88   8 88 88     
88 8  8   88   88   8   8 88   8 8   8 88   8 8   8    88 88   8      88   8 88 88   e 
88 8  8   88   88e8 8eee8 88   8 8eee8 88eee8 8eee8 eee88 88eee8      88eee8 88 88eee8                                                                               

    MycoRobo3d-DIC: Automated Imaging Acquisition System

    Author: Özgüç B. Çapunaman
    Maintainers: Özgüç B. Çapunaman, Alale Mohseni
    Institution: ForMatLab @ Penn State University
    Year: 2024
    Github: https://github.com/ForMat-Lab/MycoRobo3D-DIC
'''
        print(self._header)

        self.config = config
        self.exposure_time = config['camera_settings']['exposure_time']
        self.auto_exposure = config['camera_settings'].get('auto_exposure', False)
        self.exposure_set = False  # Flag to indicate if exposure has been set after auto-exposure

        # Pin configurations
        arduino_input_pins = config['arduino_settings']['input_pins']
        arduino_output_pins = config['arduino_settings']['output_pins']
        self.DO_CAPTURE_pin = arduino_input_pins['DO_CAPTURE']
        self.DO_RUN_COMPLETE_pin = arduino_input_pins['DO_RUN_COMPLETE']  # New pin for run completion signal
        self.DI_START_pin = arduino_output_pins['DI_START']
        self.DI_CAPTURE_COMPLETE_pin = arduino_output_pins['DI_CAPTURE_COMPLETE']

        # Experiment parameters
        self.num_samples = config['number_of_samples']
        self.interval_minutes = config.get('interval_minutes', 30)
        self.total_runs = config.get('total_runs', -1)  # -1 for infinite runs
        self.scale_factor = config.get('scale_factor', 0.5)
        self.visit_counts = [0] * self.config['number_of_samples']
        self.start_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.run_count = 0

        self.auto_detect_port = self.config['arduino_settings'].get('auto_detect_port', False)
        self.arduino_port = None if self.auto_detect_port else config['arduino_settings']['port']

        self.arduino = self.initialize_arduino()
        self.cameras = self.initialize_cameras()
        
        # Create sample folders at the beginning
        self.output_base_folder = self.setup_output_folder()
        self.create_sample_folders()


    def initialize_arduino(self):
        """Initialize Arduino based on the configuration."""
        arduino_controller = ArduinoController(port=self.arduino_port)

        # Set up input pins
        input_pins = self.config['arduino_settings']['input_pins']
        for name, pin in input_pins.items():
            arduino_controller.setup_digital_input(pin)
            logger.info(f"Arduino input pin set up: {name} on pin {pin}")

        # Set up output pins
        output_pins = self.config['arduino_settings']['output_pins']
        for name, pin in output_pins.items():
            arduino_controller.setup_digital_output(pin)
            logger.info(f"Arduino output pin set up: {name} on pin {pin}")

        return arduino_controller

    def initialize_cameras(self):
        """Initialize and configure cameras based on the configuration."""
        camera = Camera(
            width=self.config['camera_settings']['width'],
            height=self.config['camera_settings']['height'],
            exposure_time=self.exposure_time,
            scale_factor=self.scale_factor
        )
        camera.initialize_cameras()
        camera.start_grabbing()
        logger.info("Cameras initialized and started grabbing.")

        # Set exposure time based on auto_exposure flag
        if not self.auto_exposure:
            # If auto_exposure is False, set the exposure time from config
            camera.set_manual_exposure(self.exposure_time)
            logger.info(f"Exposure time set to {self.exposure_time} µs.")

        return camera

    def setup_output_folder(self):
        """Set up the base output folder for the experiment."""
        output_base_folder = os.path.join(
            self.config['output_folder'],
            self.start_time,
            self.config['experiment_name']
        )
        os.makedirs(output_base_folder, exist_ok=True)
        logger.info(f"Output base folder created at {output_base_folder}")
        return output_base_folder

    def create_sample_folders(self):
        """Create sample folders at the beginning of the experiment."""
        self.sample_folders = [
            os.path.join(self.output_base_folder, f'Sample_{i}')
            for i in range(self.num_samples)
        ]
        for folder in self.sample_folders:
            os.makedirs(folder, exist_ok=True)
            logger.info(f"Sample folder created at {folder}")

    def run(self):
        """Run the experiment."""
        # User confirmation before starting the experiment
        while True:
            user_input = input("Type 'start' to begin the experiment or 'quit' to exit: ")
            if user_input.strip().lower() == 'start':
                logger.info("Experiment started.")
                logger.info("You can exit the experiment at any time by pressing Ctrl+C.")
                break
            elif user_input.strip().lower() == 'quit':
                logger.info("Experiment aborted by user.")
                self.cleanup()
                return
        try:
            while self.total_runs == -1 or self.run_count < self.total_runs:
                logger.info(f"Starting run {self.run_count}")
                self.execute_run()
                self.run_count += 1  # Increment actual run count
                if self.total_runs != -1 and self.run_count >= self.total_runs:
                    break
                self.enter_break()
            self.terminate_experiment()
        except KeyboardInterrupt:
            logger.info("Experiment interrupted by user.")
            self.terminate_experiment()
        except Exception as e:
            logger.error(f"An error occurred during the experiment: {e}")
            self.terminate_experiment()
        finally:
            self.cleanup()

    def execute_run(self):
        """Execute the image capture for the current run."""
        # Signal the robot to start
        logger.info(f"Run {self.run_count}: Signaling robot to start the run.")
        self.arduino.set_digital(self.DI_START_pin, True)

        sample_index = 0
        # Wait for the robot to signal run completion
        while True:
            print("Waiting for capture signal.", end='\r')
            if self.arduino.check_rising_edge(self.DO_CAPTURE_pin):
                # Robot signals it's ready to capture
                self.handle_capture_signal(sample_index)
                sample_index += 1
            if self.arduino.read_digital(self.DO_RUN_COMPLETE_pin):
                # Robot signals the run is complete
                logger.info(f"Run {self.run_count}: Robot has signaled run completion.")
                break

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                logger.info("Experiment interrupted by user.")
                raise KeyboardInterrupt

            time.sleep(0.01)  # Small delay to prevent high CPU usage

        # Reset DI_START to LOW to prepare for next run
        self.arduino.set_digital(self.DI_START_pin, False)
        logger.info(f"Run {self.run_count} execution completed, with {sample_index} captures.")

    def handle_capture_signal(self, sample_index):
        """Handle the capture signal from the robot."""

        logger.info(f"Run {self.run_count}, Sample {sample_index}: Capture signal received.")

        # Set exposure on first capture if not already set
        if not self.exposure_set:
            self.set_exposure()

        # Capture images
        self.capture_images(sample_index)

        # Signal robot that capture is complete
        logger.info("Signaling robot that capture is complete.")
        self.arduino.set_digital(self.DI_CAPTURE_COMPLETE_pin, True)

        # Wait briefly to ensure robot receives the signal
        time.sleep(1)

        # Reset DI_CAPTURE_COMPLETE to LOW
        self.arduino.set_digital(self.DI_CAPTURE_COMPLETE_pin, False)

    def set_exposure(self):
        """Set the exposure for cameras based on configuration or auto-detection."""
        if self.auto_exposure:
            # Perform auto-exposure
            logger.info("Performing auto-exposure.")
            self.exposure_time = self.cameras.set_auto_exposure('Once')
            logger.info(f"Auto-detected exposure time: {self.exposure_time} µs")
            # Set manual exposure to the detected value
            self.cameras.set_manual_exposure(self.exposure_time)
        else:
            # Use the user-set exposure time from config
            self.cameras.set_manual_exposure(self.exposure_time)
        self.exposure_set = True  # Exposure has been set

    def capture_images(self, sample_index):
        """Capture images for the current sample."""
        frames = self.cameras.grab_frames()
        if frames:
            self.save_images(frames, sample_index)
            logger.info(f"Run {self.run_count}, Sample {sample_index}: Images captured.")
        else:
            logger.error(f"Run {self.run_count}, Sample {sample_index}: Failed to capture images.")

    def save_images(self, frames, sample_index):
        """Save the captured frames to the sample folder."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        visit_count_str = f'{self.visit_counts[sample_index]:04}'

        sample_folder = self.sample_folders[sample_index]
        filenames = []

        for idx, frame in enumerate(frames):
            filename = f'sample_{sample_index}_{timestamp}_{visit_count_str}_{idx}.tif'
            filepath = os.path.join(sample_folder, filename)
            cv2.imwrite(filepath, frame, [cv2.IMWRITE_TIFF_COMPRESSION, 1])
            filenames.append(filepath)
            logger.info(f"Run {self.run_count}, Sample {sample_index}: Saved image {filename}")

        self.visit_counts[sample_index] += 1  # Increment visit count

        # Display images
        self.display_images(frames)

    def display_images(self, frames):
        """Display the images side by side after scaling down."""
        resized_frames = [
            cv2.resize(frame, (0, 0), fx=self.scale_factor, fy=self.scale_factor)
            for frame in frames
        ]
        combined_image = np.hstack(resized_frames)
        cv2.imshow('Combined Image', combined_image)
        cv2.waitKey(1)  # Display the image briefly

    def enter_break(self):
        """Enter a break period between runs."""
        logger.info(f"Entering break period of {self.interval_minutes} minutes.")
        logger.info(f"Closing cameras and cleaning up signals.")
        self.cameras.close_cameras()
        self.arduino.set_digital(self.DI_START_pin, False)  # Ensure DI_START is LOW

        # Calculate when the break will resume
        resume_time = datetime.now() + timedelta(minutes=self.interval_minutes)
        logger.info(f"Break will resume at {resume_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("You can exit the experiment during the break by pressing Ctrl+C.")

        t0 = time.time()
        total_break_seconds = self.interval_minutes * 60

        try:
            while True:
                elapsed = time.time() - t0
                remaining = total_break_seconds - elapsed
                if remaining <= 0:
                    break
                mins, secs = divmod(int(remaining), 60)
                time_format = f'{mins:02d}:{secs:02d}'
                print(f'Break time remaining: {time_format}', end='\r')
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Experiment interrupted by user during break.")
            raise

        print('\n')  # Move to next line after break

        # Re-initialize cameras after break
        self.reinitialize_cameras()

    def reinitialize_cameras(self):
        """Re-initialize cameras after a break, ensuring exposure time remains the same."""
        logger.info("Re-initializing cameras after break.")
        self.cameras.initialize_cameras()
        self.cameras.start_grabbing()
        logger.info("Cameras re-initialized and started grabbing.")

        # Set exposure time based on previously saved exposure_time
        self.cameras.set_manual_exposure(self.exposure_time)
        logger.info(f"Exposure time set to {self.exposure_time} µs after break.")

    def terminate_experiment(self):
        """Terminate the experiment and generate the report."""
        end_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        total_samples_collected = sum(self.visit_counts)
        generate_pdf_report(
            self.config, self.start_time, end_time,
            self.run_count, total_samples_collected,
            self.visit_counts, self.output_base_folder
        )

    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'arduino') and self.arduino:
            self.arduino.close()
            logger.info("Arduino connection closed.")
        if hasattr(self, 'cameras') and self.cameras:
            self.cameras.close_cameras()
            logger.info("Cameras closed.")
        cv2.destroyAllWindows()
        logger.info("Resources released.")

    def run_experiment(self):
        """Main method to run the experiment."""
        self.run()


def main():
    try:
        # Load configuration
        config = load_config()
        if not config:
            logger.error("Failed to load configuration.")
            return

        # Run the experiment
        experiment = Experiment(config)
        experiment.run_experiment()

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        # Ensure cleanup in case of an exception
        if 'experiment' in locals():
            experiment.cleanup()


if __name__ == "__main__":
    main()