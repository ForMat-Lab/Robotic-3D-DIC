import cv2
import numpy as np

def check_opencv():
    # Check OpenCV version
    print(f"OpenCV version: {cv2.__version__}")

    # Create a black image and display it
    img = np.zeros((512, 512, 3), np.uint8)
    cv2.imshow('Black Image', img)
    cv2.waitKey(1000)  # Display the image for 1 second
    cv2.destroyAllWindows()

if __name__ == "__main__":
    check_opencv()