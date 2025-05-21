import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from typing import Optional, Tuple, List

class CameraPoseVisualizer:
    """
    Visualizer for 3D camera poses.
    
    This class provides methods to visualize camera poses as pyramids in 3D space. 
    Each camera is represented as a pyramid with its apex at the camera center and 
    its base corresponding to the image plane. Axis limits can be provided manually, 
    or they will be computed dynamically based on the plotted data.
    
    The class also supports optional drawing of the camera trajectory (connecting 
    camera centers), numbering (annotating each camera center with its index), and 
    drawing the XYZ axes at the origin using RGB colors.
    
    Attributes:
        fig (plt.Figure): The matplotlib figure object.
        ax (mpl_toolkits.mplot3d.Axes3D): The 3D axes object for plotting.
        xlim (Optional[Tuple[float, float]]): Limits for the x-axis. If None, computed later.
        ylim (Optional[Tuple[float, float]]): Limits for the y-axis. If None, computed later.
        zlim (Optional[Tuple[float, float]]): Limits for the z-axis. If None, computed later.
        all_vertices (List[List[float]]): List of all vertices from plotted pyramids.
        trajectory (List[List[float]]): List of camera center positions.
        draw_trajectory (bool): Flag to draw the trajectory connecting camera centers.
        draw_numbers (bool): Flag to annotate camera centers with their index.
        xyz_axes_length (float): If greater than 0, draw the XYZ axes at the origin with this length.
    """
    def __init__(self, 
                 xlim: Optional[Tuple[float, float]] = None, 
                 ylim: Optional[Tuple[float, float]] = None, 
                 zlim: Optional[Tuple[float, float]] = None, 
                 figsize: Tuple[int, int] = (12, 6),
                 draw_trajectory: bool = True,
                 draw_numbers: bool = True,
                 xyz_axes_length: float = 0.0):
        """
        Initializes the CameraPoseVisualizer.
        
        Args:
            xlim (Optional[Tuple[float, float]]): Tuple (min, max) for x-axis limits. Defaults to None.
            ylim (Optional[Tuple[float, float]]): Tuple (min, max) for y-axis limits. Defaults to None.
            zlim (Optional[Tuple[float, float]]): Tuple (min, max) for z-axis limits. Defaults to None.
            figsize (Tuple[int, int]): Size of the figure. Defaults to (12, 6).
            draw_trajectory (bool): Flag to draw trajectory connecting camera centers. Defaults to True.
            draw_numbers (bool): Flag to annotate camera centers with their index. Defaults to True.
            xyz_axes_length (float): If greater than 0, the length of the XYZ axes to be drawn at the origin.
                                      Defaults to 0.0 (no axes drawn).
        """
        self.fig = plt.figure(figsize=figsize)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        
        # Store axis limits; if any is None, they will be computed later.
        self.xlim = xlim
        self.ylim = ylim
        self.zlim = zlim
        
        # Set provided axis limits immediately if available.
        if self.xlim is not None:
            self.ax.set_xlim(self.xlim)
        if self.ylim is not None:
            self.ax.set_ylim(self.ylim)
        if self.zlim is not None:
            self.ax.set_zlim(self.zlim)
            
        # Lists to accumulate data for auto-scaling and trajectory drawing.
        self.all_vertices: List[List[float]] = []  # All vertices for axis scaling.
        self.trajectory: List[List[float]] = []      # Camera centers for trajectory.
        
        # Flags and parameters for additional features.
        self.draw_trajectory = draw_trajectory
        self.draw_numbers = draw_numbers
        self.xyz_axes_length = xyz_axes_length
        
        print('Initialized CameraPoseVisualizer')

    def extrinsic2pyramid(self, 
                          extrinsic: np.ndarray, 
                          color: str = 'r', 
                          focal_len_scaled: float = 5, 
                          aspect_ratio: float = 0.3) -> None:
        """
        Converts an extrinsic camera pose into a pyramid representation and adds it to the plot.
        
        The pyramid is constructed from a standard set of vertices defined in homogeneous coordinates.
        The extrinsic matrix (4x4) is applied to these vertices, and the resulting 3D points (after dropping
        the homogeneous coordinate) are used to draw the pyramid.
        
        Additionally, the camera center is stored for trajectory drawing, and annotated with an index if 
        drawing numbers is enabled.
        
        Args:
            extrinsic (np.ndarray): A 4x4 transformation matrix representing the camera pose.
            color (str): Color of the pyramid. Defaults to 'r'.
            focal_len_scaled (float): Scaled focal length to determine pyramid size. Defaults to 5.
            aspect_ratio (float): Aspect ratio for the pyramid base. Defaults to 0.3.
        """
        # Standard vertices for the camera pyramid in homogeneous coordinates (5 vertices)
        vertex_std = np.array([
            [0, 0, 0, 1],  # Camera center (apex)
            [ focal_len_scaled * aspect_ratio, -focal_len_scaled * aspect_ratio, focal_len_scaled, 1],
            [ focal_len_scaled * aspect_ratio,  focal_len_scaled * aspect_ratio, focal_len_scaled, 1],
            [-focal_len_scaled * aspect_ratio,  focal_len_scaled * aspect_ratio, focal_len_scaled, 1],
            [-focal_len_scaled * aspect_ratio, -focal_len_scaled * aspect_ratio, focal_len_scaled, 1]
        ])
        
        # Transform standard vertices by the extrinsic matrix.
        vertex_transformed = vertex_std @ extrinsic.T
        # Convert homogeneous coordinates to 3D.
        verts = vertex_transformed[:, :3]
        
        # Append the vertices for auto-scaling.
        self.all_vertices.extend(verts.tolist())
        
        # Save the camera center (first vertex) for trajectory drawing.
        cam_center = verts[0].tolist()
        self.trajectory.append(cam_center)
        
        # Optionally annotate the camera center with its index.
        if self.draw_numbers:
            idx = len(self.trajectory) - 1
            self.ax.text(cam_center[0], cam_center[1], cam_center[2], f'{idx}', 
                         color='black', fontsize=10)
        
        # Define the pyramid faces (each face is a list of vertices).
        meshes = [
            [verts[0], verts[1], verts[2]],         # Side face 1
            [verts[0], verts[2], verts[3]],         # Side face 2
            [verts[0], verts[3], verts[4]],         # Side face 3
            [verts[0], verts[4], verts[1]],         # Side face 4
            [verts[1], verts[2], verts[3], verts[4]]  # Base (image plane)
        ]
        # Create and add the 3D polygon collection to the axes.
        poly_collection = Poly3DCollection(meshes, facecolors=color, linewidths=0.3, 
                                             edgecolors=color, alpha=0.35)
        self.ax.add_collection3d(poly_collection)

    def customize_legend(self, labels: List[str]) -> None:
        """
        Customizes the plot legend using the provided labels.
        
        Each label is assigned a unique color from the 'rainbow' colormap.
        
        Args:
            labels (List[str]): List of label strings for the legend.
        """
        handles = []
        for idx, label in enumerate(labels):
            # Get a distinct color for each label.
            color = plt.cm.rainbow(idx / len(labels))
            patch = Patch(color=color, label=label)
            handles.append(patch)
        self.ax.legend(handles=handles, loc='upper right')

    def add_colorbar(self, max_value: float, label: str = 'Frame Number') -> None:
        """
        Adds a colorbar to the figure.
        
        The colorbar is based on a scalar mappable using the 'rainbow' colormap.
        
        Args:
            max_value (float): The maximum value for normalization.
            label (str): Label for the colorbar. Defaults to 'Frame Number'.
        """
        cmap = mpl.cm.rainbow
        norm = mpl.colors.Normalize(vmin=0, vmax=max_value)
        mappable = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
        mappable.set_array([])
        self.fig.colorbar(mappable, ax=self.ax, orientation='vertical', label=label)

    def draw_trajectory_line(self) -> None:
        """
        Draws the trajectory line connecting the camera centers.
        
        This method is called in the show() method if the draw_trajectory flag is enabled.
        """
        if len(self.trajectory) >= 2:
            # Convert list of centers to a numpy array for plotting.
            traj = np.array(self.trajectory)
            self.ax.plot(traj[:, 0], traj[:, 1], traj[:, 2], 
                         color='blue', linestyle='-', marker='o', 
                         linewidth=2, markersize=4)

    def _draw_xyz_axes(self, length: float) -> None:
        """
        Draws the XYZ axes at the origin (as defined by np.eye(4)) using RGB colors.
        
        Args:
            length (float): Length of the axes to be drawn.
        """
        origin = np.array([0, 0, 0])
        # Draw X-axis in red.
        self.ax.quiver(origin[0], origin[1], origin[2], length, 0, 0, color='r', arrow_length_ratio=0.1)
        self.ax.text(length, 0, 0, 'X', color='r')
        # Draw Y-axis in green.
        self.ax.quiver(origin[0], origin[1], origin[2], 0, length, 0, color='g', arrow_length_ratio=0.1)
        self.ax.text(0, length, 0, 'Y', color='g')
        # Draw Z-axis in blue.
        self.ax.quiver(origin[0], origin[1], origin[2], 0, 0, length, color='b', arrow_length_ratio=0.1)
        self.ax.text(0, 0, length, 'Z', color='b')

    def show(self, title: str = 'Camera Poses') -> None:
        """
        Displays the 3D plot.
        
        If any of the axis limits (x, y, or z) were not provided during initialization, they are 
        automatically computed based on the plotted camera pyramid vertices, with a small margin.
        
        Additionally, if the draw_trajectory flag is enabled, the trajectory connecting camera centers 
        is drawn. If xyz_axes_length is greater than 0, the XYZ axes at the origin are drawn.
        
        Args:
            title (str): Title of the plot. Defaults to 'Camera Poses'.
        """
        # Auto-scale axes if limits were not provided.
        if self.all_vertices:
            all_points = np.array(self.all_vertices)
            
            # Compute and set x-axis limits if not provided.
            if self.xlim is None:
                x_min, x_max = np.min(all_points[:, 0]), np.max(all_points[:, 0])
                margin = (x_max - x_min) * 0.1 if (x_max - x_min) != 0 else 1.0
                self.ax.set_xlim(x_min - margin, x_max + margin)
            
            # Compute and set y-axis limits if not provided.
            if self.ylim is None:
                y_min, y_max = np.min(all_points[:, 1]), np.max(all_points[:, 1])
                margin = (y_max - y_min) * 0.1 if (y_max - y_min) != 0 else 1.0
                self.ax.set_ylim(y_min - margin, y_max + margin)
            
            # Compute and set z-axis limits if not provided.
            if self.zlim is None:
                z_min, z_max = np.min(all_points[:, 2]), np.max(all_points[:, 2])
                margin = (z_max - z_min) * 0.1 if (z_max - z_min) != 0 else 1.0
                self.ax.set_zlim(z_min - margin, z_max + margin)
        
        # Draw trajectory line if enabled.
        if self.draw_trajectory:
            self.draw_trajectory_line()
        
        # Draw the XYZ axes at the origin if xyz_axes_length is greater than 0.
        if self.xyz_axes_length > 0:
            self._draw_xyz_axes(self.xyz_axes_length)
        
        plt.title(title)
        plt.show()