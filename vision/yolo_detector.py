import torch
from ultralytics import YOLO

# Monkeypatch torch.load for PyTorch compatibility with YOLOv8 weights loading
original_load = torch.load
def patched_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return original_load(*args, **kwargs)
torch.load = patched_load

# Friendly normalization for COCO classes (e.g. 'couch' -> 'sofa', 'cell phone' -> 'mobile phone')
CLASS_NAME_MAPPING = {
    'cell phone': 'mobile phone',
    'couch': 'sofa',
    'dining table': 'table',
    'potted plant': 'plant',
    'tv': 'tv',
    'wine glass': 'glass'
}

class YoloDetector:
    def __init__(self, model_path="yolov8n.pt"):
        print(f"Loading YOLOv8 model from {model_path}...")
        try:
            self.model = YOLO(model_path)
            print("YOLOv8 model loaded successfully with all 80 COCO classes active.")
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            self.model = None

    def detect(self, frame, conf_threshold=0.25, iou_threshold=0.45):
        """
        Runs YOLOv8 object detection across ALL 80 classes including mobile phones,
        sofas, chairs, laptops, tables, persons, doors, bottles, etc.
        - conf_threshold: confidence cutoff (optimized to 0.25 to detect handheld mobiles & sofas)
        - iou_threshold: non-maximum suppression overlap threshold (default 0.45)
        """
        if not self.model or frame is None:
            return []

        h, w = frame.shape[:2]

        # Use responsive threshold (allow 0.20 for small objects like mobile phones)
        effective_conf = max(0.18, float(conf_threshold))

        # Run inference across all classes
        results = self.model(frame, stream=False, verbose=False, conf=effective_conf, iou=iou_threshold)
        detections = []
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                
                # Retrieve raw class name from YOLO model
                raw_label = self.model.names.get(cls_id, f"object_{cls_id}")
                # Apply user-friendly naming ('cell phone' -> 'mobile phone', 'couch' -> 'sofa')
                label = CLASS_NAME_MAPPING.get(raw_label.lower(), raw_label.lower())
                
                # Check confidence threshold
                if conf >= effective_conf:
                    xyxy = box.xyxy[0].tolist()
                    x1, y1, x2, y2 = [int(val) for val in xyxy]
                    
                    # Ensure coordinates are within frame boundaries
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(w, x2), min(h, y2)
                    
                    box_w = x2 - x1
                    box_h = y2 - y1
                    
                    # Keep valid boxes (minimum 10px so small handheld phones are preserved)
                    if box_w < 10 or box_h < 10:
                        continue
                    
                    center_x = int((x1 + x2) / 2.0)
                    center_y = int((y1 + y2) / 2.0)
                    
                    detections.append({
                        'label': label,
                        'raw_label': raw_label,
                        'confidence': round(conf, 2),
                        'box': [x1, y1, x2, y2],
                        'center': [center_x, center_y],
                        'dimensions': [box_w, box_h]
                    })

        return detections
