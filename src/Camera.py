import cv2
from pypylon import pylon
import logging

logger = logging.getLogger(__name__)

class Camera:
    """
    A class to manage one or more Basler cameras via the pypylon library.
    Handles configuration of exposure times, image grabbing, etc.
    """

    def __init__(
        self, width=2448, height=2048, exposure_time=5000,
        timeout=5000, scale_factor=0.5
    ):
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
        Start grabbing for all initialized cameras using the LatestImageOnly strategy.
        """
        for camera in self.cameras:
            if not camera.IsGrabbing():
                camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        logger.info("All cameras started grabbing.")

    def set_auto_exposure(self, mode='Once'):
        """
        Enable auto exposure for all initialized cameras.
        Typically used with 'Once' or 'Continuous'.

        Args:
            mode (str): 'Once' or 'Continuous' for auto exposure modes.

        Returns:
            int or float: The average exposure time set by the cameras, 
                          or the manual exposure if auto fails.
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
                # The actual exposure time might not instantly match, but let's read it
                exposure_time = camera.ExposureTime.GetValue()
                exposure_times.append(exposure_time)
                logger.debug(
                    f"Camera {camera.GetDeviceInfo().GetModelName()} current exposure: {exposure_time} µs"
                )
            except Exception as e:
                logger.error(
                    f"Failed to enable auto-exposure for camera "
                    f"{camera.GetDeviceInfo().GetModelName()}: {e}"
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
                    f"Failed to set manual exposure for camera "
                    f"{camera.GetDeviceInfo().GetModelName()}: {e}"
                )

    def grab_frames(self):
        """
        Grab frames from all the initialized cameras.

        Returns:
            list of np.ndarray: The captured frames (one per camera).
        """
        frames = []
        if not self.cameras:
            logger.warning("No cameras available to grab frames.")
            return frames

        for camera in self.cameras:
            if camera.IsGrabbing():
                try:
                    grab_result = camera.RetrieveResult(
                        self.timeout, pylon.TimeoutHandling_ThrowException
                    )
                    if grab_result.GrabSucceeded():
                        frames.append(grab_result.Array)
                    else:
                        logger.error(
                            f"Failed to grab frame from camera: "
                            f"{camera.GetDeviceInfo().GetModelName()}"
                        )
                    grab_result.Release()
                except Exception as e:
                    logger.error(
                        f"Exception while grabbing frame from camera "
                        f"{camera.GetDeviceInfo().GetModelName()}: {e}"
                    )
            else:
                logger.error(
                    f"Camera {camera.GetDeviceInfo().GetModelName()} "
                    "is not grabbing."
                )
        return frames

    def close_cameras(self):
        """
        Stop grabbing and close all cameras, then release any OpenCV windows.
        """
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