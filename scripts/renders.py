import bpy
# import pickle
import smplx
import torch
from pathlib import Path
# import trimesh
import os
import numpy as np
import mathutils
from scipy.spatial.transform import Rotation
from mathutils import Vector
import json
import bmesh
# from utils import get_blender_from_cv_rt


# Load configuration from render_config.json - Change to right path if environment changed
config_path = "/netscratch/dongmo/datas/render_config.json" # or "/render_config.json" if Github
with open(config_path, "r") as config_file:
    config = json.load(config_file)

# Extract parameters from the configuration
model_file_path = config["model_file_path"]
smplx_data_path = config["smplx_data_path"]
camera_data_path = config["camera_data_path"]
file_path_segmentation_vert = config["file_path_segmentation_vert"]
base_output_dir = config["base_output_dir"]

camera_parameters = config["camera_parameters"]
img_width = config["image_resolution"]["img_width"]
img_height = config["image_resolution"]["img_height"]
isSegmentation = config["isSegmentation"]

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

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







def load_smplx_model(model_file_path):
    # Load SMPL model
    model = smplx.create(model_file_path, model_type='smplx', gender='neutral', use_face_contour=False, num_betas=10, num_expression_coeffs=10, ext='npz')
    print(model)
    smplx_data = np.load(smplx_data_path, allow_pickle=True).item()

    # Load SMPL data
    body_pose=torch.from_numpy(smplx_data["body_pose"]).to(DEVICE)
    transl=torch.from_numpy(smplx_data["transl"]).to(DEVICE) 
    global_orient=torch.from_numpy(smplx_data["global_orient"]).to(DEVICE) 
    left_hand_pose=torch.from_numpy(smplx_data["left_hand_pose"]).to(DEVICE) 
    right_hand_pose=torch.from_numpy(smplx_data["right_hand_pose"]).to(DEVICE) 
    jaw_pose=torch.from_numpy(smplx_data["jaw_pose"]).to(DEVICE) 
    leye_pose = torch.from_numpy(smplx_data["leye_pose"]).to(DEVICE) 
    reye_pose = torch.from_numpy(smplx_data["reye_pose"]).to(DEVICE)
    num_frames = body_pose.shape[0]
    # print("body_pose",body_pose[0].unsqueeze(0))
    # print("body_pose",body_pose[0].unsqueeze(0).shape)
    # print("body_pose",body_pose.shape)
    # print("transl",transl[0].unsqueeze(0).shape)
    # print("global_orient",global_orient[0].unsqueeze(0).shape)
    # print("left_hand_pose",left_hand_pose[0].unsqueeze(0).shape)
    # print("right_hand_pose",right_hand_pose[0].unsqueeze(0).shape)
    # print("jaw_pose",jaw_pose[0].unsqueeze(0).shape)
    # print("leye_pose",leye_pose[0].unsqueeze(0).shape)
    # print("reye_pose",reye_pose[0].unsqueeze(0).shape)
    return model, body_pose, transl, global_orient, jaw_pose, leye_pose, reye_pose, num_frames


def set_camera(camera_data_path):
    # Camera data
    camera_data = np.load(camera_data_path, allow_pickle=True).item()
    camera_t = camera_data["T_k_cam_np"]
    camera_r = camera_data["R_k_cam_np"]
    camera_K = camera_data["intrinsics"]
    print("camera_t",camera_t.shape, "camera_r",camera_r.shape)

    # Set up the camera
    bpy.context.scene.render.engine = 'CYCLES'
    camera = bpy.data.objects['Camera']
    cam_data = camera.data
    cam_data.type = 'PANO'
    try:
        cam_data.panorama_type = 'FISHEYE_624'
        print("Camera panorama type successfully set to FISHEYE_624.")
    except Exception as e:
        print("An error occurred while setting panorama type:", e)
    # Set Fisheye 624 camera parameters 
    cam_data.fisheye624_cx = camera_parameters["fisheye624_cx"]
    cam_data.fisheye624_cy = camera_parameters["fisheye624_cy"]
    cam_data.fisheye624_f  = camera_parameters["fisheye624_f"]
    cam_data.fisheye624_k0 = camera_parameters["fisheye624_k0"]
    cam_data.fisheye624_k1 = camera_parameters["fisheye624_k1"]
    cam_data.fisheye624_k2 = camera_parameters["fisheye624_k2"]
    cam_data.fisheye624_k3 = camera_parameters["fisheye624_k3"]
    cam_data.fisheye624_k4 = camera_parameters["fisheye624_k4"]
    cam_data.fisheye624_k5 = camera_parameters["fisheye624_k5"]
    cam_data.fisheye624_p0 = camera_parameters["fisheye624_p0"]
    cam_data.fisheye624_p1 = camera_parameters["fisheye624_p1"]
    cam_data.fisheye624_s0 = camera_parameters["fisheye624_s0"]
    cam_data.fisheye624_s1 = camera_parameters["fisheye624_s1"]
    cam_data.fisheye624_s2 = camera_parameters["fisheye624_s2"]
    cam_data.fisheye624_s3 = camera_parameters["fisheye624_s3"]


    print("camData verification", cam_data.fisheye624_cx, cam_data.fisheye624_f, cam_data.type, cam_data.panorama_type)
    # Set image resolution
    bpy.context.scene.render.resolution_x = img_width
    bpy.context.scene.render.resolution_y = img_height
    return camera, camera_t, camera_r, camera_K

def transformationMatrix_camera_pose():
    """
    Returns an approximative transformation matrix from Pose 1 representing the pose of the camera in frame 0 in Arctic
    to Pose 2 representing an approximative position of the camera in front of the left eye to match the Aria normal camera postion.

    -- An Improvement should be made to track the exact camera position instead of an approximation--
    """

    # Pose 1
    T = camera_t[0].flatten()
    R = camera_r[0]
    loc1, rot1_euler = get_blender_from_cv_rt(R, T) 
    rot1 = Rotation.from_euler('xyz', rot1_euler).as_matrix()
    T1 = np.eye(4)
    T1[:3, :3] = rot1
    T1[:3, 3] = loc1

    # Pose 2
    loc2 = np.array([0.0286, 0.1945, 1.5075])
    rot2_euler = np.array([0.3038, 0.0151, 3.0752])
    rot2 = Rotation.from_euler('xyz', rot2_euler).as_matrix()
    T2 = np.eye(4)
    T2[:3, :3] = rot2
    T2[:3, 3] = loc2

    # Transformation from Pose 1 to Pose 2
    T1_inv = np.linalg.inv(T1)
    T_1_to_2 = T2 @ T1_inv

    # print("Transformation matrix from Pose 1 to Pose 2:")
    # print(T_1_to_2)
    return T_1_to_2



def transform_pose(location, rotation_euler, transformation_matrix):
    """
    Transforms a pose (location + rotation) using a 4x4 transformation matrix.

    Args:
        location (np.ndarray): (3,) position vector.
        rotation_euler (np.ndarray): (3,) Euler angles (in radians).
        transformation_matrix (np.ndarray): (4,4) transformation matrix.

    Returns:
        transformed_location (np.ndarray): Transformed position vector.
        transformed_rotation_euler (np.ndarray): Transformed rotation in Euler angles.

        -- Every pose of the camera in Arctic is transformed to match the Aria camera position using our approximation --   
    """
    # Build the 4x4 matrix for the input pose
    rot_mat = Rotation.from_euler('xyz', rotation_euler).as_matrix()
    pose_matrix = np.eye(4)
    pose_matrix[:3, :3] = rot_mat
    pose_matrix[:3, 3] = location

    # Apply the transformation
    transformed_pose = transformation_matrix @ pose_matrix
    transformed_location = transformed_pose[:3, 3]
    transformed_rot_mat = transformed_pose[:3, :3]
    transformed_rotation_euler = Rotation.from_matrix(transformed_rot_mat).as_euler('xyz')
    # print("transformed_koc",transformed_location)
    # print("transformed_rotation_euler",transformed_rotation_euler)
    return transformed_location, transformed_rotation_euler

def generate_group_colors(file_path):
    """
    Generates a dictionary of part definitions for coloring the vertices of the human body.
    """
    with open(file_path, "r") as file:
            data = json.load(file)
    # Define the groups and their corresponding parts
    group_colors = {
            "hands": (1.0, 0.0, 0.0, 1.0),  # Red for hands
            "arms": (0.0, 1.0, 0.0, 1.0),  # Green for arms
            "forearms": (0.0, 0.0, 1.0, 1.0),  # Blue for forearms
            # "shoulders": (1.0, 1.0, 0.0, 1.0),  # Yellow for shoulders
        }
    part_groups = {
        "hands": ["rightHand", "leftHand","leftHandIndex1", "rightHandIndex1"],
        "arms": ["leftArm", "rightArm"],
        "forearms": ["leftForeArm", "rightForeArm"],
        # "shoulders": ["leftShoulder", "rightShoulder"],
    }

    # Construct the part_definitions object
    part_definitions = {}
    for group, parts in part_groups.items():
        color = group_colors[group]
        for part in parts:
            if part in data:
                part_definitions[part] = (data[part], color)
    return part_definitions            



def color_vertices(human_body, file_path):
    # === 1. Setup Object & Vertex Colors ===
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = human_body
    human_body.select_set(True)

    mesh = human_body.data

    # Ensure vertex color layer
    if not mesh.vertex_colors:
        mesh.vertex_colors.new()
    color_layer = mesh.vertex_colors.active

    # Build lookup from vertex index to loop index

    part_definitions = generate_group_colors(file_path)
    vertex_to_loops = {}
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vert_index = mesh.loops[loop_index].vertex_index
            vertex_to_loops.setdefault(vert_index, []).append(loop_index)

    #  Paint each part with its color ===
    for part_name, (verts, color) in part_definitions.items():
        for v_idx in verts:
            loop_indices = vertex_to_loops.get(v_idx, [])
            for loop_idx in loop_indices:
                color_layer.data[loop_idx].color = color

    # === 2. Set up material to use vertex color ===
    if not human_body.data.materials:
        mat = bpy.data.materials.new(name="VertexColor_Material")
        human_body.data.materials.append(mat)
    else:
        mat = human_body.data.materials[0]

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear and recreate basic shader
    nodes.clear()
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)

    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)

    vcol = nodes.new(type='ShaderNodeVertexColor')
    vcol.location = (-300, 0)
    vcol.layer_name = color_layer.name


    # Connect nodes
    links.new(vcol.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])



def update_frame(frame, isSegmentation):
    """
    Updates the frame of the scene with the given frame number.
    Give the corresponding pose to the SMPLX model and update the vertices of the human body.
    Give the corresponding camera pose.
    Colors the vertices of the human body if isSegmentation is True.
    Renders the scene and saves the image to the output directory.
    """
    print("Updating frame:", frame)
    output = model(body_pose=body_pose[frame].unsqueeze(0),
               transl= transl[frame].unsqueeze(0), 
               global_orient= global_orient[frame].unsqueeze(0), 
               jaw_pose= jaw_pose[frame].unsqueeze(0), 
               leye_pose = leye_pose[frame].unsqueeze(0), 
               reye_pose = reye_pose[frame].unsqueeze(0),
               )

    # vertices 
    vertices = output.vertices.detach().cpu().numpy().squeeze()
    print("vertices",vertices.shape)

    # Update the smpl_body object in blender with the new vertices and joints
    human_body = bpy.data.objects['CustomObject']
    body_vertices = human_body.data.vertices
    for i, (vert, new_vert) in enumerate(zip(body_vertices, vertices)):
        vert.co = new_vert

    # Update the camera location and rotation
    T = camera_t[frame].flatten()
    R = camera_r[frame]

    print("T",T, "R",R)
    print("T",T.shape, "R",R.shape)

    T, R = get_blender_from_cv_rt(R, T) 
    location, rotation = transform_pose(T, R, transformationMatrix_camera_pose())
    camera.rotation_euler = rotation
    camera.location = location    
    print("camera.location",camera.location, "camera.rotation_euler",camera.rotation_euler)
    # # Update the scene
    # dg = bpy.context.evaluated_depsgraph_get()
    # dg.update()
    if(isSegmentation):
        color_vertices(human_body, file_path_segmentation_vert)
    
    sequence_name = os.path.basename(os.path.dirname(smplx_data_path))  
    action_name = os.path.basename(smplx_data_path).split('.')[0]  
    output_dir = os.path.join(base_output_dir, sequence_name, action_name, "color_segmentation") if isSegmentation else os.path.join(base_output_dir, sequence_name, action_name, "no_segmentation")
    print("Generated output_dir:", output_dir)

 
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{action_name}_{frame}.jpg")
    bpy.context.scene.render.filepath = output_file 
    bpy.ops.render.render(write_still=True)
    print(f"Step {frame} done; Render complete. Image saved to {output_file}") 




model, body_pose, transl, global_orient, jaw_pose, leye_pose, reye_pose, num_frames = load_smplx_model(model_file_path)
camera, camera_t, camera_r, camera_K = set_camera(camera_data_path)
for frame in range(157, num_frames + 1):
    update_frame(frame, isSegmentation)


