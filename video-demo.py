# dds cloudapi for DINO-X
from dds_cloudapi_sdk import Config
from dds_cloudapi_sdk import Client
from dds_cloudapi_sdk.tasks.dinox import DinoxTask
from dds_cloudapi_sdk.tasks.detection import DetectionTask
from dds_cloudapi_sdk import TextPrompt
from dds_cloudapi_sdk import DetectionModel
from dds_cloudapi_sdk import DetectionTarget

# using supervision for visualization
import cv2
import numpy as np
import supervision as sv
import os

"""
Hyper Parameters
"""
API_TOKEN = "Your API token"
VIDEO_PATH = "./assets/demo.mp4"
OUTPUT_PATH = "./annotated_demo_video.mp4"
TEXT_PROMPT = "wheel . eye . helmet . mouse . mouth . vehicle . steering wheel . ear . nose" 

def process_video_with_dino_x():
    """
    Process video using DINO-X object detection
    """
    # Step 1: Initialize config and client
    config = Config(API_TOKEN)
    client = Client(config)

    # Prepare class mapping
    classes = [x.strip().lower() for x in TEXT_PROMPT.split('.') if x]
    class_name_to_id = {name: id for id, name in enumerate(classes)}
    
    # Open video
    cap = cv2.VideoCapture(VIDEO_PATH)
    
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    # Initialize video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(OUTPUT_PATH, fourcc, fps, (width, height))
    
    # Temporary frame for upload
    temp_frame_path = "./temp_frame.jpg"
    
    try:
        # Process each frame
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Save current frame temporarily
            cv2.imwrite(temp_frame_path, frame)
            
            # Upload and process frame
            image_url = client.upload_file(temp_frame_path)
            task = DinoxTask(
                image_url=image_url,
                prompts=[TextPrompt(text=TEXT_PROMPT)]
            )
            client.run_task(task)
            predictions = task.result.objects
            
            # Decode prediction results
            boxes = []
            confidences = []
            class_names = []
            class_ids = []
            
            for obj in predictions:
                boxes.append(obj.bbox)
                confidences.append(obj.score)
                cls_name = obj.category.lower().strip()
                class_names.append(cls_name)
                class_ids.append(class_name_to_id[cls_name])
            
            boxes = np.array(boxes)
            class_ids = np.array(class_ids)
            labels = [
                f"{class_name} {confidence:.2f}"
                for class_name, confidence
                in zip(class_names, confidences)
            ]
            
            # Annotate frame
            detections = sv.Detections(
                xyxy=boxes,
                class_id=class_ids
            )
            
            box_annotator = sv.BoxAnnotator()
            annotated_frame = box_annotator.annotate(scene=frame.copy(), detections=detections)
            
            label_annotator = sv.LabelAnnotator()
            annotated_frame = label_annotator.annotate(
                scene=annotated_frame, 
                detections=detections, 
                labels=labels
            )
            
            # Write annotated frame
            out.write(annotated_frame)
    
    except Exception as e:
        print(f"Error processing video: {e}")
    
    finally:
        # Clean up resources
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        
        # Remove temporary frame
        if os.path.exists(temp_frame_path):
            os.remove(temp_frame_path)
    
    print(f"Annotated video saved to {OUTPUT_PATH}")

def main():
    process_video_with_dino_x()

if __name__ == '__main__':
    main()