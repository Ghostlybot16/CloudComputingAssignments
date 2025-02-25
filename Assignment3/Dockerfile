#Use Python base image
FROM python:3.12-slim

#Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

#Install system dependencies for OpenCV, Matplotlib, and Qt support
RUN apt-get update && apt-get install -y \
    build-essential python3-dev libffi-dev libssl-dev \
    libgl1-mesa-glx libglib2.0-0 \
    && apt-get clean
    
    
#Upgrade pip and install dependencies 
RUN pip install --upgrade pip setuptools wheel 
RUN pip install "numpy>=1.22.4,<2.3.0" "scipy==1.13" seaborn


# Install PyTorch, Computer Vision, and Machine Learning dependencies
RUN pip install torch torchvision numpy  opencv-python pandas timm Pillow matplotlib ultralytics
   
#Install Apache Beam and Google Cloud dependencies
RUN pip install apache-beam[gcp] google-cloud-storage google-cloud-pubsub

#Copy the application code into the container
COPY . /app
WORKDIR /app

#Download YOLOv5 and MiDaS models to avoid re-downloading
RUN python -c "import torch; \
               torch.hub.load('ultralytics/yolov5', 'yolov5s', force_reload=True); \
               torch.hub.load('intel-isl/MiDaS', 'MiDaS_small', force_reload=True)"

#Set the entry point to run the script
ENTRYPOINT ["python3", "dataFlow.py"]