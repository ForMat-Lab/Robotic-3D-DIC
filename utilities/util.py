import numpy as np
import os
import json
from scipy.spatial.transform import Rotation

# Set the working directory to the directory of the script
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)


def import_intrinsic_calib(dir, fn="intrinsic.json"):
    """
    Imports intrinsic calibration data from a JSON file.

    :param dir: Directory where the intrinsic calibration file is located.
    :param fn: Filename of the intrinsic calibration file, default is 'intrinsic.json'.
    :return: A tuple containing the intrinsic matrix and distortion coefficients as numpy arrays.
             Returns (None, None) if the file does not exist.
    """
    file_path = os.path.join(dir, fn)

    if not os.path.isfile(file_path):
        print(f"The file {file_path} does not exist.")
        return None, None

    data = readJSON(file_path)
    intrinsic_matrix = np.array(data.get("intrinsic_matrix", []))
    distortion_coefficients = np.array(data.get("distortion_coefficients", []))

    return np.reshape(intrinsic_matrix, (3, 3)), distortion_coefficients


def deconstructPoses(est_pose, scale=1.0):
    """
    Deconstructs a list of estimated poses into translation vectors and rotation vectors.

    :param est_pose: List of estimated poses (4x4 transformation matrices).
    :param scale: Scaling factor applied to translation vectors, default is 1.0.
    :return: A tuple of lists containing translation vectors and rotation vectors.
    """
    rVec_pose = []
    t_pose = []
    for pose in est_pose:
        t = pose[:3, 3].reshape(-1, 3, 1)
        rVec = Rotation.from_matrix(pose[:3, :3]).as_rotvec()
        rVec_pose.append(rVec)
        t_pose.append(t)

    return t_pose, rVec_pose


def composeH(R, t):
    """
    Composes a 4x4 homogeneous transformation matrix from a rotation matrix and translation vector.

    :param R: Rotation matrix (3x3).
    :param t: Translation vector (3x1).
    :return: Homogeneous transformation matrix (4x4).
    """
    H = np.eye(4)
    H[:3, :3] = np.asarray(R)
    H[:3, 3] = np.asarray(t).ravel()
    return H


def decomposeH(H):
    """
    Decomposes a 4x4 homogeneous transformation matrix into its rotation matrix and translation vector.

    :param H: Homogeneous transformation matrix (4x4).
    :return: A tuple containing the rotation matrix (3x3) and translation vector (3x1).
    """
    R = H[:3, :3]
    t = H[:3, 3]
    return R, t


def writeJSON(data, file_path):
    """
    Writes data to a JSON file.

    :param data: Data to be written to the file.
    :param file_path: Path of the file to write data to.
    """
    print(f"Writing JSON file {file_path} ... ", end='')
    with open(file_path, 'w') as f:
        json.dump(data, f)
    print("Done")


def readJSON(file_path):
    """
    Reads data from a JSON file.

    :param file_path: Path of the file to read data from.
    :return: Data read from the file.
    """
    print(f"Reading JSON file {file_path} ... ", end='')
    with open(file_path, 'r') as f:
        data = json.load(f)
    print("Done")
    return data
