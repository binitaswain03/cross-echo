import cv2
import numpy as np
import csv
import os
import time
from datetime import datetime
import uuid

# Import custom modules
from vision.yolo_detector import YoloDetector
from depth.midas_estimator import MidasEstimator
from vision.direction_analyzer import DirectionAnalyzer

def get_depth_category(distance):
    if distance < 0:
        return "Unknown"
    elif distance < 1.5:
        return "Close"
    elif distance < 3.0:
        return "Medium"
    else:
        return "Far"

def calculate_angle(center_x, frame_width, fov=60):
    """
    Rough estimation of angle from center (assuming 60 degree horizontal FOV)
    -30 degrees is far left, +30 degrees is far right
    """
    offset = center_x - (frame_width / 2.0)
    angle = (offset / (frame_width / 2.0)) * (fov / 2.0)
    return round(angle, 2)

def calculate_mse(imageA, imageB):
    """
    Mean Squared Error between two images.
    Used for checking visual similarity to avoid duplicates.
    """
    err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
    err /= float(imageA.shape[0] * imageA.shape[1])
    return err

def main():
    print("Initializing Data Collection Module...")
    
    # Initialize models
    detector = YoloDetector("yolov8n.pt")
    depth_estimator = MidasEstimator("MiDaS_small")
    direction_analyzer = DirectionAnalyzer()
    
    # Setup directories
    dataset_dir = "dataset"
    images_dir = os.path.join(dataset_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    csv_file = os.path.join(dataset_dir, "records.csv")
    file_exists = os.path.isfile(csv_file)
    
    # Setup webcam
    print("Starting webcam...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return
        
    print("Webcam initialized. Starting data collection...")
    print("Move objects around or move the camera to collect diverse data.")
    print("Press 'q' in the video window to quit.")
    
    # State tracking for duplicates
    # Store the last cropped image (resized) for each label to check similarity
    last_seen_objects = {}
    MSE_THRESHOLD = 800.0 # Threshold for similarity (lower means more similar)
    MIN_DISTANCE_CHANGE = 0.5 # Wait for distance to change by 0.5m
    
    collected_count = 0
    
    # Open CSV file in append mode
    with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
        fieldnames = [
            'Record ID', 'Object Name', 'Position', 'Angle', 'Distance', 
            'Depth Category', 'Confidence Score', 'Timestamp', 'Image Path'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
            
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame.")
                break
                
            h, w, _ = frame.shape
            
            # 1. Detect objects
            detections = detector.detect(frame)
            
            # 2. Estimate Depth (only if detections exist to save compute)
            depth_map = None
            if detections:
                depth_map = depth_estimator.estimate_depth(frame)
                
            for det in detections:
                label = det['label']
                conf = det['confidence']
                box = det['box']
                x1, y1, x2, y2 = box
                
                # 3. Distance Estimation
                distance = depth_estimator.get_object_distance(depth_map, box) if depth_map is not None else -1.0
                
                # 4. Position Analysis
                position = direction_analyzer.analyze(w, box)
                
                # 5. Angle Calculation
                center_x = (x1 + x2) / 2.0
                angle = calculate_angle(center_x, w)
                
                # 6. Similarity Checking to prevent duplicates
                # Crop image for similarity checking (ensure coordinates within bounds)
                crop_x1, crop_x2 = max(0, x1), min(w, x2)
                crop_y1, crop_y2 = max(0, y1), min(h, y2)
                
                if crop_x2 <= crop_x1 or crop_y2 <= crop_y1:
                    continue
                    
                crop = frame[crop_y1:crop_y2, crop_x1:crop_x2]
                
                try:
                    resized_crop = cv2.resize(crop, (100, 100))
                    gray_crop = cv2.cvtColor(resized_crop, cv2.COLOR_BGR2GRAY)
                except Exception as e:
                    continue
                
                is_duplicate = False
                current_time = time.time()
                if label in last_seen_objects:
                    last_time = last_seen_objects[label]
                    if current_time - last_time < 0.5: # Save 2 frames per second per object
                        is_duplicate = True
                        
                if not is_duplicate:
                    # Update tracking
                    last_seen_objects[label] = current_time
                    
                    # Generate record data
                    record_id = str(uuid.uuid4())
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    depth_category = get_depth_category(distance)
                    
                    # Save clean full-frame image
                    image_filename = f"{label}_{record_id[:8]}.jpg"
                    image_path = os.path.join(images_dir, image_filename)
                    cv2.imwrite(image_path, frame)
                    
                    # Write to CSV
                    row = {
                        'Record ID': record_id,
                        'Object Name': label,
                        'Position': position,
                        'Angle': angle,
                        'Distance': distance,
                        'Depth Category': depth_category,
                        'Confidence Score': round(conf, 2),
                        'Timestamp': timestamp,
                        'Image Path': image_path
                    }
                    writer.writerow(row)
                    f.flush()
                    
                    collected_count += 1
                    print(f"[{collected_count}] Logged: {label} | Dist: {distance}m | Pos: {position} | Angle: {angle}°")
                
                # Draw bounding box for visualization
                color = (0, 255, 0) if not is_duplicate else (0, 165, 255) # Green if saved, Orange if duplicate
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{label} {round(conf,2)}", (x1, max(y1 - 10, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Display info text
            cv2.putText(frame, f"Collected: {collected_count} (Goal: 500)", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.putText(frame, "Press 'q' to quit", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.imshow("CrossEcho - Data Collection Module", frame)
            
            # Break loop on 'q' press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Stopping data collection...")
                break
                
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print(f"Data collection finished. Total records collected in this session: {collected_count}")
    print(f"Dataset stored in '{dataset_dir}' directory.")

if __name__ == "__main__":
    main()
