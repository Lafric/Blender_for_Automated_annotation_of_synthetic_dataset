import numpy as np
from scipy.spatial.transform import Rotation

def get_blender_from_cv_rt(R_world2cv, T_world2cv):
    # bcam stands for blender camera
    R_bcam2cv = np.array(
        [[1, 0, 0],
         [0, -1, 0],
         [0, 0, -1]])

    R_bcam2cv_inv = np.linalg.inv(R_bcam2cv)

    R_world2bcam = R_bcam2cv_inv.dot(R_world2cv)
    T_world2bcam = R_bcam2cv_inv.dot(T_world2cv)

    location = np.linalg.inv(-1 * R_world2bcam).dot(T_world2bcam)
    rotation = Rotation.from_matrix(R_world2bcam.T).as_euler('xyz', degrees=False)

    return location, rotation

def bcam_intrinsics (K, image_width, sensor_width, image_height):
    fx = K[0][0]
    fy = K[1][1]
    cx = K[0][2]
    cy = K[1][2]
    focal_lenght_bcam = (fx * sensor_width) / image_width
    shift_x = (cx - image_width / 2) / image_width
    shift_y = ((image_height / 2) - cy) / image_height
    return focal_lenght_bcam, shift_x, shift_y





