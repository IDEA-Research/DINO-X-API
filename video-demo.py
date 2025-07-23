# dds cloudapi for DINO-X
from dds_cloudapi_sdk import Config
from dds_cloudapi_sdk import Client
from dds_cloudapi_sdk.image_resizer import image_to_base64
from dds_cloudapi_sdk.tasks.v2_task import V2Task

# using supervision for visualization
import cv2
import numpy as np
import supervision as sv
import os
from pycocotools import mask as mask_utils

"""
Hyper Parameters
"""
API_TOKEN = "Your API token"
VIDEO_PATH = "./assets/demo.mp4"
OUTPUT_PATH = "./annotated_demo_video.mp4"
TEXT_PROMPT = "wheel . eye . helmet . mouse . mouth . vehicle . steering wheel . ear . nose"

def process_video_with_dino_x():
    """
    Process video using DINO-X object detection with V2 API
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
    
    # Temporary frame for processing
    temp_frame_path = "./temp_frame.jpg"
    
    try:
        frame_count = 0
        # Process each frame
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            print(f"Processing frame {frame_count}...")
            
            # Save current frame temporarily
            cv2.imwrite(temp_frame_path, frame)
            
            # Convert frame to base64
            image = image_to_base64(temp_frame_path)
            
            # Prepare API body using V2 API format
            api_path = "/v2/task/dinox/detection"
            api_body = {
                "model": "DINO-X-1.0",
                "image": image,
                "prompt": {
                    "type": "text",
                    "text": TEXT_PROMPT
                },
                "mask_format": "coco_rle",
                "targets": ["bbox", "mask"],
                "bbox_threshold": 0.25,
                "iou_threshold": 0.8
            }
            
            # Create and run V2 task
            task = V2Task(
                api_path=api_path,
                api_body=api_body
            )
            
            client.run_task(task)
            result = task.result
            objects = result["objects"]
            
            # Decode prediction results
            boxes = []
            masks = []
            confidences = []
            class_names = []
            class_ids = []
            
            for obj in objects:
                boxes.append(obj["bbox"])
                masks.append(mask_utils.decode(obj["mask"]))
                confidences.append(obj["score"])
                cls_name = obj["category"].lower().strip()
                class_names.append(cls_name)
                class_ids.append(class_name_to_id[cls_name])
            
            boxes = np.array(boxes)
            masks = np.array(masks)
            class_ids = np.array(class_ids)
            labels = [
                f"{class_name} {confidence:.2f}"
                for class_name, confidence
                in zip(class_names, confidences)
            ]
            
            # Annotate frame
            detections = sv.Detections(
                xyxy=boxes,
                mask=masks.astype(bool),
                class_id=class_ids
            )
            
            # Apply annotations
            box_annotator = sv.BoxAnnotator()
            annotated_frame = box_annotator.annotate(scene=frame.copy(), detections=detections)
            
            label_annotator = sv.LabelAnnotator()
            annotated_frame = label_annotator.annotate(
                scene=annotated_frame, 
                detections=detections, 
                labels=labels
            )
            
            mask_annotator = sv.MaskAnnotator()
            annotated_frame = mask_annotator.annotate(scene=annotated_frame, detections=detections)
            
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