import glob
import re
import ast
import os
import numpy as np
from scipy.spatial.transform import Rotation

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

class TROBParser:
	"""
	A parser class for processing robotic data, specifically for extracting robot trajectories
	and transformations from .mod files and calculating transformations between different frames.
	"""

	def __init__(
		self,
		dir=None,
		extrinsic_dir=None,
		parsing_method='robtarget'
	) -> None:
		"""
		Initializes the TROBParser object with the specified directory, extrinsic calibration data,
		and the parsing method for the .mod files.

		:param dir: Directory where the .mod files and other related data are stored.
		:param extrinsic_dir: Path to the JSON file containing extrinsic calibration data.
		:param parsing_method: Method used for parsing the .mod files. Default is 'robtarget'.
		"""

		self.dir = dir

		self.parsing_method = parsing_method.lower()

		# Load extrinsic calibration data if provided, and print it for verification
		if extrinsic_dir is not None:
			data = readJSON(extrinsic_dir)
			self.extrinsic = np.asarray(data.get('extrinsic')).reshape((4,4))
		else:
			self.extrinsic = np.eye(4)
		print("-------------------")
		print("Extrinsic Calibration:")
		print(self.extrinsic)
		print("-------------------")

	def _find_mod_file(self):
		"""
		Locates the .mod file in the specified directory.

		:return: Path to the .mod file.
		:raises RuntimeError: If more than one or no .mod file is found.
		"""

		dir = os.path.join(self.dir, '*.mod')
		mod_files = glob.glob(dir)
		if len(mod_files) > 1:
			raise RuntimeError("More than 1 .mod files exist!")
		elif len(mod_files) == 0:
			raise RuntimeError("No .mod files exist!")
		else:
			return mod_files[0]

	def _parse_robtarget_line(self, line):
		"""
		Parses a single line from the .mod file for robtarget instructions.

		:param line: A line from the .mod file.
		:return: A tuple (ret, pos, quat) where ret is a boolean indicating if the line contains valid data,
				 pos is the position vector, and quat is the quaternion for orientation.
		"""

		pos = None
		quat = None
		ret = False

		tmp = line.split()

		if len(tmp) > 1 and tmp[1] == "robtarget":
			tmp = tmp[2].split(']')
			tmp = [i.split('[')[-1] for i in tmp]

			pos = tmp[0].split(",")
			pos = [float(i) for i in pos]

			quat = tmp[1].split(",")
			quat = [float(i) for i in quat]
			quat = [quat[1], quat[2], quat[3], quat[0]]

			ret = True
		return ret, pos, quat

	def _parse_moveL_line(self, line):
		"""
		Parses a single line from the .mod file for MoveL instructions, handling variations in spacing
		and formats by normalizing the line and safely evaluating the nested array structures.

		:param line: A line from the .mod file.
		:return: A tuple (ret, pos, quat) where ret is a boolean indicating if the line contains valid data,
				pos is the position vector, and quat is the quaternion for orientation.
		"""
		# Normalize the line by removing all whitespace
		normalized_line = re.sub(r'\s+', '', line)

		pos = None
		quat = None
		ret = False

		# Check if the normalized line starts with "MoveL"
		if normalized_line.startswith("MoveL"):
			try:
				# Extract the content within the first set of square brackets after "MoveL"
				start_index = normalized_line.find('[')
				end_index = normalized_line.rfind(']') + 1
				if start_index != -1 and end_index != -1:
					array_str = normalized_line[start_index:end_index]
					# Replace non-numeric, non-standard elements with a placeholder if necessary
					clean_array_str = re.sub(r'[a-zA-Z]+', '0', array_str)
					array_data = ast.literal_eval(clean_array_str)
					
					# Assuming the first element is position and the second is quaternion
					if len(array_data) >= 2:
						pos = array_data[0]
						quat = array_data[1][:4]  # Ensure quat is the first four elements if more data is present
						quat = [quat[1], quat[2], quat[3], quat[0]]
						ret = True
			except (ValueError, SyntaxError) as e:
				print(f"Error parsing line: {line}\n{e}")

		return ret, pos, quat

	def base_T_tcp(self, export = True):
		"""
		Calculates the transformations from the base to the tool center point (TCP) from the .mod file.

		:return: Arrays of positions, quaternions, rotation matrices, rotation vectors, and homogeneous matrices.
		:raises RuntimeError: If no valid robtarget or MoveL keywords are found.
		"""
		
		mod_path = self._find_mod_file()

		file = open(mod_path, 'r')
		lines = file.readlines()

		L_pos = []
		L_quat = []
		L_rotmat = []
		L_rotvec = []
		L_H = []
		for line in lines:
			if self.parsing_method == 'robtarget':
				ret, pos, quat = self._parse_robtarget_line(line)
			elif self.parsing_method == 'movel':
				ret, pos, quat = self._parse_moveL_line(line)
			else:
				raise RuntimeError(
					'Parsing method is not valid! Only robtarget or movel')
			if ret:
				L_pos.append(pos)
				L_quat.append(quat)

				tmp = Rotation.from_quat(quat)
				L_rotmat.append(tmp.as_matrix().tolist())
				L_rotvec.append(tmp.as_rotvec().tolist())
				L_H.append(composeH(tmp.as_matrix(), pos).tolist())

		if len(L_pos) > 0:
			data = {
				'pos': L_pos,
				'rotvec': L_rotvec,
				'rotmat': L_rotmat,
				'quat': L_quat,
				'H': L_H
			}
			path = os.path.join(self.dir, 'base_T_tcp.json')
			if export:
				writeJSON(data, path)
			return data
		else:
			raise RuntimeError(
				f"No robtarget or MoveL keywords were found in {mod_path}!")

	def base_T_camera(self, export=True):
		"""
		Calculates the transformations from the base to the camera frame.

		:return: Arrays of positions, quaternions, rotation matrices, rotation vectors, and homogeneous matrices.
		:raises RuntimeError: If no extrinsic calibration data is provided.
		"""

		data = self.base_T_tcp()
		Ts = np.asarray(data.get('H')).reshape((-1,4,4))

		L_pos = []
		L_quat = []
		L_rotmat = []
		L_rotvec = []
		L_H = []

		base_T_camera = []
		for T in Ts:
			tmp = T@self.extrinsic
			base_T_camera.append(tmp)

			rotmat, pos = decomposeH(tmp)
			L_pos.append(pos.tolist())
			L_rotmat.append(rotmat.tolist())
			tmp = Rotation.from_matrix(rotmat)

			L_quat.append(tmp.as_quat().tolist())
			L_rotvec.append(tmp.as_rotvec().tolist())
			L_H.append(composeH(tmp.as_matrix(), pos).tolist())

		if len(L_pos) > 0:
			data = {
				'pos': L_pos,
				'rotvec': L_rotvec,
				'rotmat': L_rotmat,
				'quat': L_quat,
				'H': L_H
			}
			path = os.path.join(self.dir, 'base_T_camera.json')
			if export:
				writeJSON(data, path)
			return data
		
	def trajectory(self):
		"""
		Computes and logs the robot's trajectory based on the transformations to the camera frame.

		:return: A list of transformation matrices representing the robot's trajectory.
		"""

		data = self.base_T_camera()
		Ts = np.asarray(data.get('H')).reshape((-1,4,4))
		n = len(Ts)
		result = []

		path = os.path.join(self.dir, 'trajectory.log')
		with open(path, 'w') as f:
			for i in range(n):
				f.write('{} {} {}\n'.format(i-1, i, n))

				T = np.asarray(Ts[i]).reshape((4,4))
				
				T[:3, 3] *= 0.001

				result.append(T)
				s = np.array2string(T)
				s = re.sub('[\[\]]', '', s)

				f.write('{}\n'.format(s))
		return result
