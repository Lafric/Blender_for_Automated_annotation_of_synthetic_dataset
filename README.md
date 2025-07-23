# Synthesis of Hand/Arm annotation from 3D Rendering for Fisheye624 camera model from Aria glasses

This script (renders.py) automates the rendering of human body motion data (in SMPL-X format) within Blender, using camera parameters, pose data, and optional segmentation-based coloring. It's based on the integration of the Fisheye624 camera model in Blender. I achieved the integration of this camera model by modifing the Open Code Source at [here](https://github.com/blender/blender)

## Motivation
- Synthetic datasets are used in many dataset dealing with 3D human model to overcome the challenges of real-world data collection. 
- The need of automated annotation methods are more crucial as the save time to researches.
- No synthetic dataset using Fisheye624 Camera model



## Method

<img width="1115" height="526" alt="image" src="https://github.com/user-attachments/assets/16521efa-25d2-465e-8e53-44b09c35cdfc" />


## Requirements
- The build Blender application: The modified code is provided in the folder blender.
- SMPLX model (model path) from [here](https://smpl-x.is.tue.mpg.de/)
- Raw sequences of the Motion capture data from Arctic. [here](https://github.com/zc-alexfan/arctic)
- SMPLX vertices segmentation .json file from [here](https://github.com/Meshcapade/wiki/blob/main/assets/SMPL_body_segmentation/smplx/smplx_vert_segmentation.json)
- Modify all file path, camera intrinsics, image resolution and set wether or not there should be segmentation with the flag isSegmentation.

## Built Blender

By following the instructions in [Build Blender](https://developer.blender.org/docs/handbook/building_blender/linux/)

## Output 

- Renders are saved as .jpg images, under base_output_dir/<sequence>/<action>/<segmentation_mode>/.
- If isSegmentation is true, specific body parts are colored based on the segmentation JSON.

Example an image with is annotation: 
<img width="363" height="323" alt="image" src="https://github.com/user-attachments/assets/9cd5241d-5e37-43b2-88b9-152c5986a50c" />
<img width="364" height="324" alt="image" src="https://github.com/user-attachments/assets/8f8a8afe-206a-478e-b07a-6c79232b4dac" />



## How to run
Assuming being in the folder containing the built blender App executable run: 
<pre><code>./blender -b &lt;Path to the template.blend containing the smplx templatemesh&gt; -P &lt;Path of the renders.py </code></pre>

For our example in the cluster we have:
<pre><code>./blender -b template_bmesh.blend -P /netscratch/dongmo/scripts/renders.py</code></pre>

## Make sure that:

- template_bmesh.blend contains a mesh object named "CustomObject" and a camera named "Camera". If using another one make changes in code accordingly.

## Permissions for the cluster
I've given my supervisor the Permission to see the computed images on the cluster. The script can be directly run from there.
In the folder <pre><code>/netscratch/dongmo/blender-Own/build_linux/bin</code></pre> containing the build app run <pre><code>./blender -b template_bmesh.blend -P /netscratch/dongmo/scripts/renders.py</code></pre>
To test with other sequence change the config_render.json file.




