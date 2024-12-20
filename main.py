import os
import time
import cv2
import numpy as np
import logging
import csv
from datetime import datetime, timedelta
from src.util import load_config, validate_config, generate_pdf_report
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
        # Print header
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

        # Load configuration parameters
        self.config = config
        self.exposure_time = config['camera_settings'].get('exposure_time', None)
        # Exposure_mode can be Manual, SetOnce, Continuous
        self.exposure_mode = config['camera_settings'].get('exposure_mode', 'Manual')
        
        # For SetOnce mode, keep a per-sample exposure array
        self.sample_exposures = [None] * config['number_of_samples']
        self.exposure_lookup_path = None
        
        self.scale_factor = config.get('display_scale_factor', 0.5)
        self.display_images = config.get('display_images', True)

        # Pin configurations
        arduino_input_pins = config['arduino_settings']['input_pins']
        arduino_output_pins = config['arduino_settings']['output_pins']
        self.DO_CAPTURE_pin = arduino_input_pins['DO_CAPTURE']
        self.DO_RUN_COMPLETE_pin = arduino_input_pins['DO_RUN_COMPLETE']
        self.DI_RUN_pin = arduino_output_pins['DI_RUN']
        self.DI_CAPTURE_COMPLETE_pin = arduino_output_pins['DI_CAPTURE_COMPLETE']

        # Experiment parameters
        self.num_samples = config['number_of_samples']
        self.interval_minutes = config.get('interval_minutes', 30)
        self.total_runs = config.get('total_runs', -1)  # -1 for infinite
        self.visit_counts = [0] * self.num_samples
        self.start_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.run_count = 0

        self.auto_detect_port = self.config['arduino_settings'].get('auto_detect_port', False)
        self.arduino_port = None if self.auto_detect_port else config['arduino_settings']['port']

        # Initialize Arduino and cameras
        self.arduino = self.initialize_arduino()
        self.cameras = self.initialize_cameras()
        
        # Create output folders for experiment data
        self.output_base_folder = self.setup_output_folder()
        self.create_sample_folders()

        # CSV logging:
        # - One main CSV file for logging captures: <experiment_name>.csv in the experiment folder
        experiment_csv_name = f"{self.config['experiment_name']}.csv"
        self.csv_log_path = os.path.join(self.output_base_folder, experiment_csv_name)

        # For SetOnce mode, an exposure lookup file to remember exposures across runs
        if self.exposure_mode == 'SetOnce':
            self.exposure_lookup_path = os.path.join(self.output_base_folder, "exposure_lookup.csv")
            self.load_exposure_lookup()  # Attempt to load previously known exposures

        # Initialize the CSV file for experiment logging
        self.csv_file = open(self.csv_log_path, 'a', newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.csv_file)
        if os.path.getsize(self.csv_log_path) == 0:
            # Write CSV header if file is empty
            self.csv_writer.writerow(["run_count", "sample_index", "camera_id", "exposure_time", "unix_timestamp", "filename"])
            self.csv_file.flush()

    
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
        try:
            camera = Camera(
                width=self.config['camera_settings']['width'],
                height=self.config['camera_settings']['height'],
                exposure_time=self.exposure_time,
                scale_factor=self.scale_factor
            )
            camera.initialize_cameras()

            if self.exposure_mode == 'Manual':
                # Manual: Fixed exposure from config
                camera.set_manual_exposure(self.exposure_time)
                logger.info(f"Manual mode: Exposure time set to {self.exposure_time} µs.")
            elif self.exposure_mode == 'Continuous':
                # Continuous: auto-exposure continuously adapts
                camera.set_auto_exposure('Continuous')
                logger.info("Continuous mode: Auto-exposure enabled continuously.")
            elif self.exposure_mode == 'SetOnce':
                # SetOnce: exposure determined per sample capture if not known; no action here
                pass
        
            camera.start_grabbing()
            logger.info("Cameras initialized and started grabbing.")
            return camera
        except Exception as e:
            logger.error(f"Failed to initialize cameras: {e}")
            self.cleanup()
            raise

    def setup_output_folder(self):
        """Set up the base output directory for the experiment."""
        output_base_folder = os.path.join(
            self.config['output_folder'],
            self.start_time,
            self.config['experiment_name']
        )
        os.makedirs(output_base_folder, exist_ok=True)
        logger.info(f"Output base folder created at {output_base_folder}")
        return output_base_folder

    def create_sample_folders(self):
        """Create one folder per sample at the start of the experiment."""
        self.sample_folders = [
            os.path.join(self.output_base_folder, f'Sample_{i}')
            for i in range(self.num_samples)
        ]
        for folder in self.sample_folders:
            os.makedirs(folder, exist_ok=True)
            logger.info(f"Sample folder created at {folder}")

    def run(self):
        """Main loop to run the experiment according to the configured parameters."""
        # User confirmation
        while True:
            user_input = input("Type 'start' to begin the experiment or 'quit' to exit: ")
            if user_input.strip().lower() == 'start':
                logger.info("Experiment started. Press Ctrl+C anytime to interrupt.")
                break
            elif user_input.strip().lower() == 'quit':
                logger.info("Experiment aborted by user.")
                self.cleanup()
                return

        try:
            while self.total_runs == -1 or self.run_count < self.total_runs:
                logger.info(f"Starting run {self.run_count}")
                self.execute_run()
                self.run_count += 1
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
        """Perform one complete run of image captures for all samples."""
        # Signal the robot to start the run
        logger.info(f"Run {self.run_count}: Signaling robot to start the run.")
        self.arduino.set_digital(self.DI_RUN_pin, True)

        sample_index = 0
        exposures_updated = False  # Track if we updated any exposures this run (SetOnce mode)

        # Wait for signals from the robot for captures and run completion
        while True:
            print("Waiting for capture signal.", end='\r')
            if self.arduino.check_rising_edge(self.DO_CAPTURE_pin):
                if sample_index >= self.num_samples:
                    logger.warning(f"Run {self.run_count}: Received more capture signals than the number of samples ({self.num_samples}). Ignoring extra signals.")
                    continue
                # Robot ready for capture
                updated = self.handle_capture_signal(sample_index)
                if updated:
                    exposures_updated = True
                sample_index += 1

            if self.arduino.read_digital(self.DO_RUN_COMPLETE_pin):
                # Robot signals run complete
                logger.info(f"Run {self.run_count}: Robot signaled run completion.")
                break

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                logger.info("Experiment interrupted by user.")
                raise KeyboardInterrupt

            time.sleep(0.01)

        # If SetOnce mode and exposures were updated, save them
        if self.exposure_mode == 'SetOnce' and exposures_updated:
            self.save_exposure_lookup()

        # Reset DI_RUN to LOW for next run
        self.arduino.set_digital(self.DI_RUN_pin, False)
        logger.info(f"Run {self.run_count} execution completed, with {sample_index} captures.")

    def handle_capture_signal(self, sample_index, delay=1):
        """Handle the robot's capture signal by capturing and saving images with proper exposure.

        Returns True if any exposure was newly set (in SetOnce mode), False otherwise.
        """
        logger.info(f"Run {self.run_count}, Sample {sample_index}: Capture signal received.")

        exposure_changed = False

        # Set exposure based on exposure_mode
        if self.exposure_mode == 'SetOnce':
            # If exposure unknown for this sample, auto-expose once
            if self.sample_exposures[sample_index] is None:
                logger.info(f"SetOnce mode: Auto-exposing for Sample {sample_index}.")
                detected_exposure = self.cameras.set_auto_exposure('Once')
                self.sample_exposures[sample_index] = detected_exposure
                self.cameras.set_manual_exposure(detected_exposure)
                logger.info(f"SetOnce mode: Exposure for Sample {sample_index} set to {detected_exposure} µs.")
                exposure_changed = True
            else:
                # Use known exposure
                self.cameras.set_manual_exposure(self.sample_exposures[sample_index])

        elif self.exposure_mode == 'Manual':
            # If manual and exposure_time is None, set it now from config
            if self.exposure_time is None:
                self.cameras.set_manual_exposure(self.exposure_time)
                logger.info(f"Manual mode: Exposure time set to {self.exposure_time} µs.")

        elif self.exposure_mode == 'Continuous':
            # Continuous adapts automatically
            pass

        # Capture and save images
        frames = self.cameras.grab_frames()
        if len(frames) > 0:
            filenames = self.save_images(frames, sample_index)
            self.log_capture_info(filenames, sample_index)
            logger.info(f"Run {self.run_count}, Sample {sample_index}: Images captured and logged.")
        else:
            logger.error(f"Run {self.run_count}, Sample {sample_index}: Failed to capture images.")

        # Signal robot that capture is complete
        logger.info("Signaling robot that capture is complete.")
        self.arduino.set_digital(self.DI_CAPTURE_COMPLETE_pin, True)
        time.sleep(delay)
        self.arduino.set_digital(self.DI_CAPTURE_COMPLETE_pin, False)

        return exposure_changed

    def save_images(self, frames, sample_index):
        """Save captured frames to disk and display them."""
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

        self.visit_counts[sample_index] += 1

        # Display images
        if self.display_images:
            self.show_frames(frames)
        
        return filenames

    def show_frames(self, frames, delay=1):
        """Display the captured images side-by-side in a window, scaled down."""
        resized_frames = [
            cv2.resize(frame, (0, 0), fx=self.scale_factor, fy=self.scale_factor)
            for frame in frames
        ]
        combined_image = np.hstack(resized_frames)
        cv2.imshow('Combined Image', combined_image)
        cv2.waitKey(delay)

    def log_capture_info(self, filenames, sample_index):
        """Log capture info (run, sample, camera, exposure, timestamp, filename) into the CSV file."""
        for idx, filename in enumerate(filenames):
            camera_obj = self.cameras.cameras[idx]
            camera_id = idx
            exposure_val = camera_obj.ExposureTime.GetValue()
            unix_timestamp = int(time.time())
            self.csv_writer.writerow([
                self.run_count,
                sample_index,
                camera_id,
                exposure_val,
                unix_timestamp,
                filename
            ])
        self.csv_file.flush()

    def enter_break(self, delay=1):
        """Enter a break period between runs, closing cameras and pausing for interval_minutes."""
        logger.info(f"Entering break period of {self.interval_minutes} minutes.")
        logger.info("Closing cameras and cleaning up signals.")
        self.cameras.close_cameras()
        self.arduino.set_digital(self.DI_RUN_pin, False)  # Ensure DI_START is LOW

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
                time.sleep(delay)
        except KeyboardInterrupt:
            logger.info("Experiment interrupted by user during break.")
            self.terminate_experiment()
            self.cleanup()
            raise

        print('\n')

        # Re-initialize cameras after break
        self.reinitialize_cameras()

    def reinitialize_cameras(self):
        """Re-initialize cameras after break, applying the same exposure mode as before."""
        logger.info("Re-initializing cameras after break.")
        self.cameras.initialize_cameras()

        # Reapply mode settings
        if self.exposure_mode == 'Manual':
            self.cameras.set_manual_exposure(self.exposure_time)
            logger.info(f"Manual mode after break: Exposure time set to {self.exposure_time} µs.")
        elif self.exposure_mode == 'Continuous':
            self.cameras.set_auto_exposure('Continuous')
            logger.info("Continuous mode after break: Auto-exposure re-enabled.")
        elif self.exposure_mode == 'SetOnce':
            # SetOnce exposures will be set at capture time if unknown, or from known values
            pass        
        self.cameras.start_grabbing()
        logger.info("Cameras re-initialized and started grabbing.")

    def terminate_experiment(self):
        """Terminate the experiment, generate a PDF report, and summarize results."""
        end_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        total_samples_collected = sum(self.visit_counts)
        generate_pdf_report(
            self.config, self.start_time, end_time,
            self.run_count, total_samples_collected,
            self.visit_counts, self.output_base_folder
        )
        logger.info("Experiment terminated. Report generated.")

    def cleanup(self):
        """Release all resources (Arduino, Cameras, Windows, Files)."""
        if hasattr(self, 'arduino') and self.arduino:
            self.arduino.close()
            logger.info("Arduino connection closed.")
        if hasattr(self, 'cameras') and self.cameras:
            self.cameras.close_cameras()
            logger.info("Cameras closed.")
        if hasattr(self, 'csv_file') and self.csv_file and not self.csv_file.closed:
            self.csv_file.close()
            logger.info("CSV file closed.")
        cv2.destroyAllWindows()
        logger.info("Resources released. Cleanup complete.")

    def run_experiment(self):
        """Convenience method to start the experiment run loop."""
        self.run()

    def load_exposure_lookup(self):
        """If SetOnce mode: Load previously known exposures from CSV if it exists."""
        if self.exposure_mode != 'SetOnce' or not self.exposure_lookup_path:
            return
        if not os.path.exists(self.exposure_lookup_path):
            logger.info("No existing exposure lookup found. Will determine exposures as needed.")
            return
        try:
            with open(self.exposure_lookup_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    idx = int(row['sample_index'])
                    val = row['exposure_time']
                    self.sample_exposures[idx] = float(val) if val.lower() != "none" else None
            logger.info("Exposure lookup loaded for SetOnce mode.")
        except Exception as e:
            logger.error(f"Failed to load exposure lookup: {e}")

    def save_exposure_lookup(self):
        """Save the current set of exposures to the lookup file for future runs (SetOnce mode)."""
        if self.exposure_mode != 'SetOnce' or not self.exposure_lookup_path:
            return
        with open(self.exposure_lookup_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['sample_index', 'exposure_time'])
            for i, exp in enumerate(self.sample_exposures):
                writer.writerow([i, exp if exp is not None else "None"])
        logger.info("Exposure lookup updated/saved for SetOnce mode.")


def main():
    try:
        # Load configuration
        config = load_config()
        if not config:
            logger.error("Failed to load configuration.")
            return

        # Validate configuration
        validate_config(config)
        logger.info("Configuration validation successful.")

        # Run the experiment
        experiment = Experiment(config)
        experiment.run_experiment()

    except ValueError as ve:
        logger.error(f"Configuration Error: {ve}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        # Ensure cleanup in case of an exception
        if 'experiment' in locals():
            experiment.cleanup()


if __name__ == "__main__":
    main()