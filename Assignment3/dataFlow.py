import os
import torch
import cv2
import numpy as np
import matplotlib.pyplot as plt

# Load YOLOv5 Object Detection Model
yolo_model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

# Load MiDaS Depth Estimation Model
depth = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
depth.eval()

# Load MiDaS Transformations
Img_transform = torch.hub.load("intel-isl/MiDaS", "transforms")
Img_transforms = Img_transform.small_transform

# Output folder for storing images
output_Imgfolder = "./output_images"
os.makedirs(output_Imgfolder, exist_ok=True)


def detect_pedestrians(image_path):
    
    # Loads the input image
    img_input = cv2.imread(image_path)
    img_input_rgb = cv2.cvtColor(img_input, cv2.COLOR_BGR2RGB)

    # Run YOLOv5 object detection on the imagee
    model_results = yolo_model(img_input_rgb, size=1024)
    model_detections = model_results.pandas().xyxy[0]

    # Filter only pedestrians, it checks the person class
    pedestrians = model_detections[model_detections['name'] == 'person']

    # Estimate depth using MiDaS
    input_img = cv2.cvtColor(img_input, cv2.COLOR_BGR2RGB)
    input_img = cv2.resize(input_img, (256, 256))
    input_img = Img_transforms(input_img).to(torch.device('cpu'))

    with torch.no_grad():
        depth_map = depth(input_img)

    # Convert depth map to numpy array and resize to original image size
    depth_map = depth_map.squeeze().cpu().numpy()
    modified_map = cv2.resize(depth_map, (img_input.shape[1], img_input.shape[0]))

    # Extract bounding boxes, confidence scores, and distance 
    boxes = []
    for _, row in pedestrians.iterrows():
        x_min, y_min, x_max, y_max = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
        img_confidence = float(row['confidence'])

        # Get average depth within pedestrian bounding box (without inversion)
        pedestrian_depth = np.mean(modified_map[y_min:y_max, x_min:x_max])

        boxes.append({
            "bbox": [x_min, y_min, x_max, y_max],
            "img_confidence": img_confidence,
            "img_distance": round(pedestrian_depth, 2)
        })

    return boxes

def getting_images(folder_path):
    
    # Loop through all files in the folder
    for file_name in os.listdir(folder_path):
        # Check if the file starts with 'A' or 'C' and is an image
        if (file_name.startswith('A') or file_name.startswith('C')) and file_name.lower().endswith(('.jpg', '.png', '.jpeg')):
            image_path = os.path.join(folder_path, file_name)
            print(f"\nProcessing the image: {file_name}")

            # Detect pedestrians and estimated distance
            model_results = detect_pedestrians(image_path)
            print(f"Results for {file_name}: {model_results}")

            # Draw bounding boxes and distance labels
            img_output = cv2.imread(image_path)
            for person in model_results:
                bbox = person['bbox']
                img_confidence = person['img_confidence']
                img_distance = person['img_distance']

                # Draw rectangle around the pedestrian
                cv2.rectangle(img_output, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)

                # Label with confidence and distance
                label = f"Person {img_confidence:.2f}, {img_distance}m"
                cv2.putText(img_output, label, (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Save the image in output folder
            output_image_path = os.path.join(output_Imgfolder, file_name)
            cv2.imwrite(output_image_path, img_output)
            print(f"Image saved to: {output_image_path}")

            # Display the image using Matplotlib 
            img_display = cv2.cvtColor(img_output, cv2.COLOR_BGR2RGB)
            plt.figure(figsize=(10, 6))
            plt.imshow(img_display)
            plt.title(f"Pedestrian Detection: {file_name}")
            plt.axis('off')
            plt.show()

if __name__ == "__main__":
    # Folder whihc contains the images to test
    image_folder = "./Dataset_Occluded_Pedestrian/"  

    # Process all images in the folder
    getting_images(image_folder)
