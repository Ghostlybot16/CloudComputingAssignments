import argparse
import io
import json
import logging
import os
import base64
import apache_beam as beam
import torch
import cv2
import numpy as np
from PIL import Image
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions


# Load YOLOv5 and MiDaS Models Once (Singleton Pattern)
class Model:
    def __init__(self):
        # Load YOLOv5 Object Detection Model
        self.yolo_model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        
        # Load MiDaS Depth Estimation Model
        self.depth = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
        self.depth.eval()
        
        # Load MiDaS Transformations
        Img_transform = torch.hub.load("intel-isl/MiDaS", "transforms")
        self.Img_transforms = Img_transform.small_transform
        
        # Ensure GPU usage if available
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.depth.to(self.device)

# Instantiate the model loader once
model_load = Model()


# Detect Pedestrians and Estimate Depth
def detect_pedestrians(image_bytes):
    # Decode base64 image
    image_data = base64.b64decode(image_bytes)
    img_input = Image.open(io.BytesIO(image_data))
    img_input = img_input.convert('RGB')
    img_input_array = np.array(img_input)
    
    # Run YOLOv5 object detection
    model_results = model_load.yolo_model(img_input_array, size=1024)
    model_detections = model_results.pandas().xyxy[0]

    # Filter only pedestrians
    pedestrians = model_detections[model_detections['name'] == 'person']

    # Estimate depth using MiDaS
    input_img = cv2.cvtColor(img_input_array, cv2.COLOR_RGB2BGR)
    input_img = cv2.resize(input_img, (256, 256))
    input_img = model_load.Img_transforms(input_img).to(model_load.device)

    with torch.no_grad():
        depth_map = model_load.depth(input_img)

    # Convert depth map to numpy array and resize to original image size
    depth_map = depth_map.squeeze().cpu().numpy()
    modified_map = cv2.resize(depth_map, (img_input_array.shape[1], img_input_array.shape[0]))

    # Extract bounding boxes, confidence scores, and distances
    boxes = []
    for _, row in pedestrians.iterrows():
        x_min, y_min, x_max, y_max = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
        img_confidence = float(row['confidence'])

        # Get average depth within pedestrian bounding box
        pedestrian_depth = np.mean(modified_map[y_min:y_max, x_min:x_max])

        boxes.append({
            "bbox": [x_min, y_min, x_max, y_max],
            "img_confidence": img_confidence,
            "img_distance": round(pedestrian_depth, 2)
        })

    return boxes


# Apache Beam DoFn for Prediction
class PredictDoFn(beam.DoFn):
    def process(self, element):
        image_bytes = element['Image']
        results = detect_pedestrians(image_bytes)
        
        output = {
            'ID': element['ID'],
            'Detections': results
        }
        
        yield json.dumps(output).encode('utf8')


# Dataflow Pipeline Definition
def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', dest='input', required=True,
                        help='Input Pub/Sub topic to read from.')
    parser.add_argument('--output', dest='output', required=True,
                        help='Output Pub/Sub topic to write results to.')
    known_args, pipeline_args = parser.parse_known_args(argv)

    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = True

    with beam.Pipeline(options=pipeline_options) as p:
        images = (
            p
            | "Read from Pub/Sub" >> beam.io.ReadFromPubSub(topic=known_args.input)
            | "Parse JSON" >> beam.Map(lambda x: json.loads(x.decode('utf-8')))
        )
        
        predictions = (
            images
            | 'Predict Pedestrian Distance' >> beam.ParDo(PredictDoFn())
        )
        
        predictions | 'Encode to Byte' >> beam.Map(lambda x: json.dumps(x).encode('utf8')) \
                    | 'Write to Pub/Sub' >> beam.io.WriteToPubSub(topic=known_args.output)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
