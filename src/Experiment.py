"""
Experiment module for the MycoRobo3d-DIC Automated Imaging Acquisition System.

Author: Özgüç B. Çapunaman
Maintainers: Özgüç B. Çapunaman, Alale Mohseni
Institution: ForMatLab @ Penn State University
Year: 2025
Github: https://github.com/ForMat-Lab/MycoRobo3D-DIC
"""

import os
import time
import csv
import logging
import cv2
import numpy as np
from datetime import datetime, timedelta

from src.Arduino import ArduinoController
from src.Camera import Camera
from src.util import generate_pdf_report

logger = logging.getLogger(__name__)

class Experiment:
    """
    A class to handle the MycoRobo3d-DIC automated imaging acquisition system.

    This class coordinates the experiment flow, handling Arduino signals for robot
    movement, camera captures, exposure settings, image saving, and logging.
    """

    def __init__(self, config):
        """
        Initialize the Experiment instance.

        Args:
            config (dict): Configuration dictionary with user-defined parameters.
        """
        self._header = r'''
8""8""8                   8"""8                     eeee  8""""8      8""""8 8  8""""8 
8  8  8 e    e eeee eeeee 8   8  eeeee eeeee  eeeee    8  8    8      8    8 8  8    " 
8e 8  8 8    8 8  8 8  88 8eee8e 8  88 8   8  8  88    8  8e   8      8e   8 8e 8e     
88 8  8 8eeee8 8e   8   8 88   8 8   8 8eee8e 8   8 eee8  88   8 eeee 88   8 88 88     
88 8  8   88   88   8   8 88   8 8   8 88   8 8   8    88 88   8      88   8 88 88   e 
88 8  8   88   88e8 8eee8 88   8 8eee8 88eee8 8eee8 eee88 88eee8      88eee8 88 88eee8                                                                               

    MycoRobo3d-DIC: Automated Image Acquisition System

    Author: Özgüç B. Çapunaman
    Maintainers: Özgüç B. Çapunaman, Alale Mohseni
    Institution: ForMatLab @ Penn State University
    Year: 2024
    Github: https://github.com/ForMat-Lab/MycoRobo3D-DIC
'''
        print(self._header)

        # Configuration
        self.config = config
        self.exposure_time = config['camera_settings'].get('exposure_time')
        self.exposure_mode = config['camera_settings'].get('exposure_mode', 'Manual')
        
        self.sample_exposures = None
        self.exposure_table_path = None
        
        self.scale_factor = config.get('display_scale_factor', 0.5)
        self.display_images = config.get('display_images', True)

        # Arduino pins
        arduino_input_pins = config['arduino_settings']['input_pins']
        arduino_output_pins = config['arduino_settings']['output_pins']
        self.DO_CAPTURE_pin = arduino_input_pins['DO_CAPTURE']
        self.DO_RUN_COMPLETE_pin = arduino_input_pins['DO_RUN_COMPLETE']
        self.DI_RUN_pin = arduino_output_pins['DI_RUN']
        self.DI_CAPTURE_COMPLETE_pin = arduino_output_pins['DI_CAPTURE_COMPLETE']

        # Arduino port
        self.auto_detect_port = config['arduino_settings'].get('auto_detect_port', False)
        self.arduino_port = None if self.auto_detect_port else config['arduino_settings']['port']

        # Experiment parameters
        self.turn_off_cameras_between_runs = config.get("turn_off_cameras_between_runs", True)
        self.num_samples = config['number_of_samples']
        self.interval_minutes = config.get('interval_minutes', 30)
        self.interval_calculation_mode = config.get("interval_calculation_mode", "constant_interval")
        self.total_runs = config.get('total_runs', -1)  # -1 => infinite
        self.visit_counts = [0] * self.num_samples
        self.start_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.run_start_time = None
        self.next_run_start_time = None
        self.run_count = 0

        # Initialize Arduino and cameras
        self.arduino = self.initialize_arduino()
        self.cameras = self.initialize_cameras()
        
        # Create output folders for experiment data
        self.output_base_folder = self.setup_output_folder()
        self.create_sample_folders()

        # CSV logging
        experiment_csv_name = f"{self.config['experiment_name']}.csv"
        self.csv_log_path = os.path.join(self.output_base_folder, experiment_csv_name)

        # 'SetOnce' -> load existing exposure table if available
        if self.exposure_mode == 'SetOnce':
            self.exposure_table_path = os.path.join(self.output_base_folder, "exposure_table.csv")
            self.load_exposure_table()

        # Initialize the CSV file
        self.csv_file = open(self.csv_log_path, 'a', newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.csv_file)
        if os.path.getsize(self.csv_log_path) == 0:
            # Write header if the file is new
            self.csv_writer.writerow([
                "run_count",
                "sample_index",
                "camera_id",
                "exposure_time",
                "unix_timestamp",
                "datetime",
                "filename"
            ])
            self.csv_file.flush()

    def initialize_arduino(self):
        """
        Initialize the Arduino microcontroller with the desired input/output pin settings.

        Returns:
            ArduinoController: Configured Arduino controller instance.
        """
        arduino_controller = ArduinoController(port=self.arduino_port)

        # Configure input pins
        input_pins = self.config['arduino_settings']['input_pins']
        for name, pin in input_pins.items():
            logger.info(f"Arduino input pin set up: {name} on pin {pin}")
            arduino_controller.setup_digital_input(pin)

        # Configure output pins
        output_pins = self.config['arduino_settings']['output_pins']
        for name, pin in output_pins.items():
            logger.info(f"Arduino output pin set up: {name} on pin {pin}")
            arduino_controller.setup_digital_output(pin)

        return arduino_controller

    def initialize_cameras(self):
        """
        Initialize and configure the camera(s) based on the user-defined settings.

        Returns:
            Camera: A Camera instance for image acquisition.
        """
        try:
            camera = Camera(
                width=self.config['camera_settings']['width'],
                height=self.config['camera_settings']['height'],
                exposure_time=self.exposure_time,
                scale_factor=self.scale_factor
            )
            camera.initialize_cameras()

            # Configure exposure mode
            if self.exposure_mode == 'Manual':
                logger.info(f"Manual mode: Setting exposure time to {self.exposure_time} µs.")
                camera.set_manual_exposure(self.exposure_time)
            elif self.exposure_mode == 'Continuous':
                logger.info("Continuous mode: Auto-exposure enabled continuously.")
                camera.set_auto_exposure('Continuous')
            elif self.exposure_mode == 'SetOnce':
                # For 'SetOnce', we set exposure per-sample capture if unknown
                pass

            camera.start_grabbing()
            logger.info("Cameras initialized and started grabbing.")
            return camera
        except Exception as e:
            logger.error(f"Failed to initialize cameras: {e}")
            self.cleanup()
            raise

    def setup_output_folder(self):
        """
        Create the base output folder for this experiment.

        Returns:
            str: Path to the created (or existing) base output directory.
        """
        output_base = os.path.join(
            self.config['output_folder'],
            self.start_time,
            self.config['experiment_name']
        )
        os.makedirs(output_base, exist_ok=True)
        logger.info(f"Output base folder created at {output_base}")
        return output_base

    def create_sample_folders(self):
        """
        Create one folder per sample inside the base output directory.
        """
        self.sample_folders = []
        for i in range(self.num_samples):
            folder_path = os.path.join(self.output_base_folder, f'Sample_{i}')
            os.makedirs(folder_path, exist_ok=True)
            self.sample_folders.append(folder_path)
            logger.info(f"Sample folder created at {folder_path}")

    def run(self):
        """
        Main loop to execute the experiment.

        Prompts the user to start or quit. After starting, it iterates through
        the specified number of runs (or indefinitely if total_runs = -1).
        """
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
            # Main run loop
            while self.total_runs == -1 or self.run_count < self.total_runs:
                logger.info(f"Starting run {self.run_count}")
                self.execute_run()
                self.run_count += 1

                if self.total_runs != -1 and self.run_count >= self.total_runs:
                    break  # finished all runs
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
        """
        Perform one complete run of the experiment.

        Signals the robot to start, then waits for capture signals to take images
        of each sample. Logs the images and sets exposure time if in 'SetOnce' mode.
        """
        logger.info(f"Run {self.run_count}: Signaling robot to start the run.")
        self.arduino.set_digital(self.DI_RUN_pin, True)
        self.run_start_time = time.time()
        # For "constant_interval" mode, calculate next_run_start_time at the beginning of the run.
        if self.interval_calculation_mode == "constant_interval":
            self.next_run_start_time = self.run_start_time + self.interval_minutes * 60

        new_exposure_table = False
        if self.exposure_mode == 'SetOnce' and self.sample_exposures is None:
            new_exposure_table = True
            self.sample_exposures = [None] * self.num_samples

        sample_index = 0
        while True:
            print("Waiting for capture signal.", end='\r')

            # Check capture signal
            if self.arduino.check_rising_edge(self.DO_CAPTURE_pin):
                if sample_index >= self.num_samples:
                    logger.warning(
                        f"Run {self.run_count}: Received more capture signals than samples. Ignoring extras."
                    )
                    continue
                self.handle_capture_signal(sample_index)
                sample_index += 1

            # Check run completion signal
            if self.arduino.read_digital(self.DO_RUN_COMPLETE_pin):
                logger.info(f"Run {self.run_count}: Robot signaled run completion.")
                break

            # Allow user interruption via 'q'
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                logger.info("Experiment interrupted by user.")
                raise KeyboardInterrupt

            time.sleep(0.01)

        # If we created a new exposure table for 'SetOnce', save it
        if self.exposure_mode == 'SetOnce' and new_exposure_table:
            self.save_exposure_table()

        # Reset DI_RUN pin
        self.arduino.set_digital(self.DI_RUN_pin, False)
        logger.info(f"Run {self.run_count} completed with {sample_index} captures.")

    def handle_capture_signal(self, sample_index, delay=1):
        """
        Handle actions upon receiving a capture signal from the Arduino.

        Includes setting exposure (depending on mode), capturing frames, saving them, and logging.
        """
        logger.info(f"Run {self.run_count}, Sample {sample_index}: Capture signal received.")

        # SetOnce mode logic
        if self.exposure_mode == 'SetOnce':
            if self.sample_exposures[sample_index] is None:
                logger.info(f"SetOnce mode: Auto-exposing for Sample {sample_index}.")
                detected_exposure = self.cameras.set_auto_exposure('Once')
                self.sample_exposures[sample_index] = detected_exposure
                self.cameras.set_manual_exposure(detected_exposure)
                logger.info(f"SetOnce: Exposure for Sample {sample_index} set to {detected_exposure} µs.")
            else:
                # Use previously learned exposure time
                self.cameras.set_manual_exposure(self.sample_exposures[sample_index])

        # Capture frames
        t0 = datetime.now()
        frames = self.cameras.grab_frames()
        if frames:
            filenames = self.save_images(frames, sample_index)
            self.log_capture_info(filenames, sample_index, t0)
            logger.info(f"Run {self.run_count}, Sample {sample_index}: Images captured and logged.")
        else:
            logger.error(f"Run {self.run_count}, Sample {sample_index}: No frames captured.")

        # Signal capture completion
        logger.info(f"Run {self.run_count}: Signaling robot that capture is complete.")
        self.arduino.set_digital(self.DI_CAPTURE_COMPLETE_pin, True)
        time.sleep(delay)
        self.arduino.set_digital(self.DI_CAPTURE_COMPLETE_pin, False)

    def save_images(self, frames, sample_index):
        """
        Save the captured frames as TIFF images to the appropriate sample folder.

        Args:
            frames (list of np.ndarray): Frames from each camera.
            sample_index (int): Index of the current sample.

        Returns:
            list of str: List of paths to the saved TIFF files.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        visit_count_str = f'{self.visit_counts[sample_index]:04}'
        sample_folder = self.sample_folders[sample_index]
        filenames = []

        for idx, frame in enumerate(frames):
            filename = f"sample_{sample_index}_{timestamp}_{visit_count_str}_{idx}.tif"
            filepath = os.path.join(sample_folder, filename)
            cv2.imwrite(filepath, frame, [cv2.IMWRITE_TIFF_COMPRESSION, 1])
            filenames.append(filepath)
            logger.info(f"Run {self.run_count}, Sample {sample_index}: Saved image {filename}")

        self.visit_counts[sample_index] += 1

        # Optionally display the images
        if self.display_images:
            self.show_frames(frames)

        return filenames

    def show_frames(self, frames, delay=1):
        """
        Display the captured frames side-by-side in a single OpenCV window.

        Args:
            frames (list of np.ndarray): The frames to display.
            delay (int): Delay in ms for cv2.waitKey (default=1).
        """
        resized_frames = [
            cv2.resize(frame, (0, 0), fx=self.scale_factor, fy=self.scale_factor)
            for frame in frames
        ]
        combined_image = np.hstack(resized_frames)
        cv2.imshow('Combined Image', combined_image)
        cv2.waitKey(delay)

    def log_capture_info(self, filenames, sample_index, timestamp):
        """
        Log the capture info for each frame to a CSV file.

        Args:
            filenames (list of str): File paths of saved images.
            sample_index (int): Which sample was captured.
            timestamp (datetime): Timestamp of the capture event.
        """
        for idx, filename in enumerate(filenames):
            camera_obj = self.cameras.cameras[idx]
            camera_id = idx
            exposure_val = camera_obj.ExposureTime.GetValue()

            unix_timestamp = timestamp.timestamp()
            datetime_str = timestamp.astimezone().strftime('%Y-%m-%d %H:%M:%S.%f')

            self.csv_writer.writerow([
                self.run_count,
                sample_index,
                camera_id,
                exposure_val,
                unix_timestamp,
                datetime_str,
                filename
            ])
        self.csv_file.flush()

    def enter_break(self, delay=1, reinit_threshold=30):
        """
        Pause between runs for a specified break interval.
        Optionally closes the cameras between runs based on configuration.

        Args:
            delay (int): Delay in seconds between each loop iteration during the break.
            reinit_threshold (int): Time in seconds before the end of the break to reinitialize cameras.
        """
        logger.info(f"Entering break period of {self.interval_minutes} minutes.")

        if self.turn_off_cameras_between_runs:
            logger.info("Turning cameras off between runs as per configuration.")
            self.cameras.close_cameras()
        else:
            logger.info("Keeping cameras on during break as per configuration.")

        # For "constant_break" mode, calculate next_run_start_time at the beginning of the break.
        if self.interval_calculation_mode == "constant_break":
            self.next_run_start_time = time.time() + self.interval_minutes * 60

        # Calculate how much time is left until the scheduled next run start
        remaining = self.next_run_start_time - time.time()

        if remaining <= 0:
            logger.warning(
                f"No break time left! Scheduled next run start was "
                f"{remaining:.2f} seconds ago. Continuing immediately..."
            )
            return
        
        resume_dt = datetime.fromtimestamp(self.next_run_start_time)
        logger.info(f"Break will end at {resume_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("Press Ctrl+C to exit the experiment during the break.")

        cameras_reinitialized = False  # Flag to ensure cameras are reinitialized only once

        try:
            while True:
                remaining = self.next_run_start_time - time.time()

                if remaining <= 0:
                    logger.info("Break time has ended. Proceeding to the next run.")
                    break

                # Only reinitialize cameras if they were turned off
                if self.turn_off_cameras_between_runs and not cameras_reinitialized and remaining <= reinit_threshold:
                    logger.info(
                        f"Remaining break time ({remaining:.2f} seconds) is below the "
                        f"reinitialization threshold of {reinit_threshold} seconds. "
                        "Reinitializing cameras now."
                    )
                    self.reinitialize_cameras()
                    cameras_reinitialized = True

                # Display remaining break time
                mins, secs = divmod(int(remaining), 60)
                print(f"Break time remaining: {mins:02d}:{secs:02d}", end='\r')

                time.sleep(delay)
        except KeyboardInterrupt:
            logger.info("Break interrupted by user.")
            self.terminate_experiment()
            self.cleanup()
            raise
        finally:
            print()

    def reinitialize_cameras(self):
        """
        Re-initialize cameras after the break, applying the chosen exposure mode again.
        """
        logger.info("Re-initializing cameras after break.")
        self.cameras.initialize_cameras()

        if self.exposure_mode == 'Manual':
            self.cameras.set_manual_exposure(self.exposure_time)
            logger.info(f"Manual exposure reset to {self.exposure_time} µs.")
        elif self.exposure_mode == 'Continuous':
            self.cameras.set_auto_exposure('Continuous')
            logger.info("Continuous auto-exposure re-enabled.")
        # For 'SetOnce', exposures are handled at capture time

        self.cameras.start_grabbing()
        logger.info("Cameras re-initialized and started grabbing.")

    def terminate_experiment(self):
        """
        Terminate the experiment gracefully. Generates a PDF report with results.
        """
        end_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        total_samples = sum(self.visit_counts)

        generate_pdf_report(
            self.config,
            self.start_time,
            end_time,
            self.run_count,
            total_samples,
            self.visit_counts,
            self.output_base_folder
        )
        logger.info("Experiment terminated. PDF report generated.")

    def cleanup(self):
        """
        Release resources (Arduino, cameras, open files) and close OpenCV windows.
        """
        if hasattr(self, 'arduino') and self.arduino:
            self.arduino.close()
        if hasattr(self, 'cameras') and self.cameras:
            self.cameras.close_cameras()
        if hasattr(self, 'csv_file') and self.csv_file and not self.csv_file.closed:
            self.csv_file.close()
            logger.info("CSV file closed.")
        cv2.destroyAllWindows()
        logger.info("Cleanup complete.")

    def load_exposure_table(self):
        """
        If in 'SetOnce' mode, load previously stored sample exposures from CSV if available.
        """
        if self.exposure_mode != 'SetOnce' or not self.exposure_table_path:
            return

        if not os.path.exists(self.exposure_table_path):
            logger.info("No existing exposure table found; will create new on first run.")
            return

        try:
            with open(self.exposure_table_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                self.sample_exposures = [None] * self.num_samples
                for row in reader:
                    idx = int(row['sample_index'])
                    val = row['exposure_time'].strip()
                    if val.isnumeric():
                        self.sample_exposures[idx] = float(val)
                    else:
                        self.sample_exposures[idx] = None
            logger.info("Exposure table loaded for 'SetOnce' mode.")
        except Exception as e:
            logger.error(f"Failed to load exposure table: {e}")

    def save_exposure_table(self):
        """
        If in 'SetOnce' mode, save current sample exposures to CSV for future runs.
        """
        if self.exposure_mode != 'SetOnce' or not self.exposure_table_path:
            return

        try:
            with open(self.exposure_table_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['sample_index', 'exposure_time'])
                for i, exp in enumerate(self.sample_exposures):
                    writer.writerow([i, exp if exp is not None else "None"])
            logger.info("Exposure table saved for 'SetOnce' mode.")
        except Exception as e:
            logger.error(f"Failed to save exposure table: {e}")