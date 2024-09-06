# camera.py

import cv2
from pypylon import pylon
import logging

class Camera:
    def __init__(self, width=2448, height=2048, exposure_time=100000, timeout=5000, scale_factor=0.5):
        """
        Initialize the camera controller.
        :param width: The width resolution of the camera frames.
        :param height: The height resolution of the camera frames.
        :param exposure_time: The exposure time for capturing images (in microseconds).
        :param timeout: The timeout for retrieving frames (in milliseconds).
        :param scale_factor: The scale factor for resizing frames for display.
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
        self.cameras = [pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(device))
                        for device in pylon.TlFactory.GetInstance().EnumerateDevices()]
        for camera in self.cameras:
            camera.Open()
        logging.info("All cameras initialized and opened.")

    def set_camera_settings(self):
        """
        Set the width, height, and exposure time for all cameras.
        """
        for camera in self.cameras:
            camera.Width.SetValue(self.width)
            camera.Height.SetValue(self.height)
            camera.ExposureTime.SetValue(self.exposure_time)
        logging.info(f"Camera settings applied. Width: {self.width}, Height: {self.height}, Exposure Time: {self.exposure_time} µs.")

    def grab_frames(self):
        """
        Grab frames from all the initialized cameras.
        :return: List of frames.
        """
        results = [camera.RetrieveResult(self.timeout, pylon.TimeoutHandling_ThrowException) for camera in self.cameras]
        frames = [result.Array for result in results if result.GrabSucceeded()]

        # Release all results after grabbing frames
        for result in results:
            result.Release()

        return frames

    def save_frames(self, frames, sample_folder, sample_index, visit_count):
        """
        Save captured frames to the specified folder.
        :param frames: The list of frames captured from cameras.
        :param sample_folder: The folder where the frames will be saved.
        :param sample_index: The current sample index.
        :param visit_count: The visit count for the sample.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        for idx, frame in enumerate(frames):
            visit_count_str = f'{visit_count:04}'
            filename = f'sample_{sample_index + 1}_{timestamp}_{visit_count_str}_{idx}.tif'
            filepath = os.path.join(sample_folder, filename)
            cv2.imwrite(filepath, frame, [cv2.IMWRITE_TIFF_COMPRESSION, 1])
            logging.info(f"Image saved: {filename}")

    def display_frames(self, frames):
        """
        Display frames concatenated in a single CV2 window.
        :param frames: The list of frames to display.
        """
        resized_frames = [cv2.resize(frame, (0, 0), fx=self.scale_factor, fy=self.scale_factor) for frame in frames]
        concatenated_frame = cv2.hconcat(resized_frames)
        cv2.imshow('Captured Images', concatenated_frame)

    def close_cameras(self):
        """
        Stop grabbing and close all cameras.
        """
        for camera in self.cameras:
            if camera.IsGrabbing():
                camera.StopGrabbing()
            camera.Close()
        cv2.destroyAllWindows()
        logging.info("All cameras closed.")