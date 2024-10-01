import cv2
from pypylon import pylon
import logging

class Camera:
    def __init__(
        self, width=2448, height=2048, exposure_time=5000,
        timeout=5000, scale_factor=0.5
    ):
        """
        Initialize the camera controller with configurable parameters.
        """
        self.width = width
        self.height = height
        self.exposure_time = exposure_time
        self.timeout = timeout
        self.scale_factor = scale_factor
        self.cameras = []

    def initialize_cameras(self):
        """
        Initialize and open all available cameras.
        """
        self.cameras = [
            pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(device))
            for device in pylon.TlFactory.GetInstance().EnumerateDevices()
        ]
        for camera in self.cameras:
            camera.Open()
        logging.info("All cameras initialized and opened.")

    def start_grabbing(self):
        """
        Start grabbing for all initialized cameras.
        """
        for camera in self.cameras:
            if not camera.IsGrabbing():
                camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        logging.info("All cameras started grabbing.")

    def set_camera_settings(self):
        """
        Set the width, height, and exposure time for all cameras.
        """
        for camera in self.cameras:
            camera.Width.SetValue(self.width)
            camera.Height.SetValue(self.height)
            camera.ExposureTime.SetValue(self.exposure_time)
        logging.info(
            f"Camera settings applied. Width: {self.width}, "
            f"Height: {self.height}, Exposure Time: {self.exposure_time} µs."
        )

    def set_auto_exposure(self, mode='Once'):
        """
        Enable auto exposure for all initialized cameras.
        """
        exposure_times = []
        for camera in self.cameras:
            try:
                camera.ExposureAuto.SetValue(mode)  # Set the auto-exposure mode
                logging.info(
                    f"Auto-exposure {mode} enabled for camera: "
                    f"{camera.GetDeviceInfo().GetModelName()}"
                )
                exposure_time = camera.ExposureTime.GetValue()
                exposure_times.append(exposure_time)
                logging.info(f"Current exposure time: {exposure_time} µs")
            except Exception as e:
                logging.error(
                    f"Failed to enable auto-exposure for camera "
                    f"{camera.GetDeviceInfo().GetModelName()}: {e}"
                )
        return sum(exposure_times) // len(exposure_times)
    def set_manual_exposure(self, exposure_time):
        """
        Set a manual exposure time for all initialized cameras.
        """
        for camera in self.cameras:
            try:
                camera.ExposureAuto.SetValue('Off')  # Turn off auto-exposure
                camera.ExposureTime.SetValue(exposure_time)  # Set manual exposure time
                logging.info(
                    f"Manual exposure time set to {exposure_time} µs for camera: "
                    f"{camera.GetDeviceInfo().GetModelName()}"
                )
            except Exception as e:
                logging.error(
                    f"Failed to set manual exposure for camera "
                    f"{camera.GetDeviceInfo().GetModelName()}: {e}"
                )

    def grab_frames(self):
        """
        Grab frames from all the initialized cameras.
        :return: List of frames.
        """
        frames = []
        for camera in self.cameras:
            if camera.IsGrabbing():
                grab_result = camera.RetrieveResult(
                    self.timeout, pylon.TimeoutHandling_ThrowException
                )
                if grab_result.GrabSucceeded():
                    frames.append(grab_result.Array)
                else:
                    logging.error(
                        f"Failed to grab frame from camera: "
                        f"{camera.GetDeviceInfo().GetModelName()}"
                    )
                grab_result.Release()
            else:
                logging.error("Camera is not grabbing frames.")
        return frames

    def close_cameras(self):
        """
        Stop grabbing and close all cameras.
        """
        for camera in self.cameras:
            if camera.IsGrabbing():
                camera.StopGrabbing()
            if camera.IsOpen():
                camera.Close()
        cv2.destroyAllWindows()
        logging.info("All cameras closed.")

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