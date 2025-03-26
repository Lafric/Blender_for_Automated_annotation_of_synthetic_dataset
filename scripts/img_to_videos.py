import cv2
import os
import re

def convert_images_to_video(img_folder, output_file, fps):
    # image files in the input folder
    image_files = sorted(
    [f for f in os.listdir(img_folder) if f.endswith('.jpg') or f.endswith('.png')],
    key=lambda x: int(re.search(r'_(\d+)\.', x).group(1))
    )
    print("len",len(image_files))

    # Read the first image to get its dimensions
    first_image = cv2.imread(os.path.join(img_folder, image_files[0]))
    height, width, _ = first_image.shape

    # Create a VideoWriter object to save the video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Specify the codec for the output video file
    video = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

    # Iterate over each image and write it to the video
    for image_file in image_files:
        print(image_file)
        image_path = os.path.join(img_folder, image_file)
        frame = cv2.imread(image_path)
        video.write(frame)

    # Release the video writer and close the video file
    video.release()
    cv2.destroyAllWindows()

# Provide the path to the input image folder, output video file, and desired FPS
img_folder = "/netscratch/dongmo/blender-renders"
output_file = img_folder + "\\output.mp4"
fps = 4  # Frames per second

# Call the function to convert the images to video
convert_images_to_video(img_folder, output_file, fps)
