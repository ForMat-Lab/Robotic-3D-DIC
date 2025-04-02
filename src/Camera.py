import cv2
import time
import threading
from pypylon import pylon
import logging

logger = logging.getLogger(__name__)

class Camera:
    """
    A class to manage one or more Basler cameras via the pypylon library.
    This version continuously grabs frames in a background thread and
    stores the latest frames in a buffer.
    """

    def __init__(self, width=2448, height=2048, exposure_time=5000, timeout=5000, scale_factor=0.5):
        """
        Initialize the camera controller with configurable parameters.

        Args:
            width (int): Desired camera capture width.
            height (int): Desired camera capture height.
            exposure_time (int|float): Initial/manual exposure time (µs).
            timeout (int): Timeout for capturing frames (ms).
            scale_factor (float): Factor to scale frames for display.
        """
        self.width = width
        self.height = height
        self.exposure_time = exposure_time
        self.timeout = timeout
        self.scale_factor = scale_factor
        self.cameras = []
        # Variables for background frame grabbing
        self._running = False
        self._grab_thread = None
        self._latest_frames = []
        self._lock = threading.Lock()

    def initialize_cameras(self):
        """
        Initialize and open all available Basler cameras.
        After opening, set the default width, height, and exposure time.
        """
        devices = pylon.TlFactory.GetInstance().EnumerateDevices()
        self.cameras = [
            pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(device))
            for device in devices
        ]
        for camera in self.cameras:
            camera.Open()
            camera.Width.SetValue(self.width)
            camera.Height.SetValue(self.height)
        logger.info("All cameras initialized, opened, and default settings applied.")

    def start_grabbing(self):
        """
        Start the background thread that continuously pulls frames from all cameras.
        """
        # Start the hardware grabbing for each camera
        for camera in self.cameras:
            if not camera.IsGrabbing():
                camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        # Initialize the frame buffer
        with self._lock:
            self._latest_frames = [None] * len(self.cameras)
        # Start the background thread
        self._running = True
        self._grab_thread = threading.Thread(target=self._grab_loop, daemon=True)
        self._grab_thread.start()
        logger.info("Background frame grabbing thread started.")

    def _grab_loop(self):
        """
        Background loop that continuously grabs frames from each camera.
        """
        while self._running:
            for idx, camera in enumerate(self.cameras):
                if camera.IsGrabbing():
                    try:
                        # Use TimeoutHandling_Return to avoid exceptions on timeout
                        grab_result = camera.RetrieveResult(self.timeout, pylon.TimeoutHandling_Return)
                        if grab_result.GrabSucceeded():
                            # Copy the frame to avoid overwriting issues
                            frame = grab_result.Array.copy()
                            with self._lock:
                                self._latest_frames[idx] = frame
                        grab_result.Release()
                    except Exception as e:
                        logger.error(
                            f"Error grabbing frame from camera {camera.GetDeviceInfo().GetModelName()}: {e}"
                        )
            # Sleep briefly to reduce CPU usage
            time.sleep(0.01)

    def grab_frames(self):
        """
        Retrieve the most recent frames from the buffer.
        
        Returns:
            list of np.ndarray: The latest frames (one per camera).
        """
        with self._lock:
            # Return a copy of the latest frames list
            frames = self._latest_frames.copy()
        return frames

    def set_auto_exposure(self, mode='Once'):
        """
        Enable auto exposure for all initialized cameras.
        
        Args:
            mode (str): 'Once' or 'Continuous' for auto exposure modes.
            
        Returns:
            int or float: The average exposure time set by the cameras.
        """
        if not self.cameras:
            logger.error("No cameras available to set auto exposure.")
            return self.exposure_time

        exposure_times = []
        for camera in self.cameras:
            try:
                camera.ExposureAuto.SetValue(mode)
                logger.info(
                    f"Auto-exposure '{mode}' enabled for camera: "
                    f"{camera.GetDeviceInfo().GetModelName()}"
                )
                exposure_time = camera.ExposureTime.GetValue()
                exposure_times.append(exposure_time)
                logger.debug(
                    f"Camera {camera.GetDeviceInfo().GetModelName()} current exposure: {exposure_time} µs"
                )
            except Exception as e:
                logger.error(
                    f"Failed to enable auto-exposure for camera {camera.GetDeviceInfo().GetModelName()}: {e}"
                )
        if exposure_times:
            average_exp = sum(exposure_times) / len(exposure_times)
            return int(average_exp)
        return self.exposure_time

    def set_manual_exposure(self, exposure_time):
        """
        Disable auto-exposure and set a manual exposure time (µs) for all cameras.
        
        Args:
            exposure_time (int|float): Desired manual exposure time in microseconds.
        """
        if not self.cameras:
            logger.error("No cameras available to set manual exposure.")
            return

        for camera in self.cameras:
            try:
                camera.ExposureAuto.SetValue('Off')
                camera.ExposureTime.SetValue(exposure_time)
                logger.info(
                    f"Manual exposure set to {exposure_time} µs for camera: "
                    f"{camera.GetDeviceInfo().GetModelName()}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to set manual exposure for camera {camera.GetDeviceInfo().GetModelName()}: {e}"
                )

    def close_cameras(self):
        """
        Stop background grabbing, close all cameras, and release any OpenCV windows.
        """
        # Stop the background grabbing thread
        self._running = False
        if self._grab_thread is not None:
            self._grab_thread.join()
        # Stop hardware grabbing and close cameras
        for camera in self.cameras:
            if camera.IsGrabbing():
                camera.StopGrabbing()
            if camera.IsOpen():
                camera.Close()
        cv2.destroyAllWindows()
        logger.info("All cameras closed.")

# Unit test for the Camera class
if __name__ == "__main__":
    import time

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def test_camera_stream():
        """
        A test function to initialize the Camera class, set up the camera, and stream frames.
        """
        try:
            # Initialize the Camera class with some test values
            camera = Camera(exposure_time=10000, scale_factor=0.25)

            # Step 1: Initialize the cameras
            camera.initialize_cameras()

            # Step 2: Set camera settings
            camera.set_camera_settings()

            # Step 3: Set auto exposure
            camera.set_auto_exposure('Once')

            # # OR: Set manual exposure (e.g., 10000 µs)
            # camera.set_manual_exposure(10000)

            # Step 4: Start grabbing frames
            camera.start_grabbing()
            print("Streaming frames. Press 'q' to stop.")
            while True:
                frames = camera.grab_frames()
                if frames:
                    camera.display_frames(frames)

                # Exit on 'q' key press
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            # Step 5: Close the cameras
            camera.close_cameras()

        except Exception as e:
            logging.error(f"An error occurred during the camera test: {e}")

    # Run the test
    test_camera_stream()