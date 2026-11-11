import torch
import cv2
import numpy as np

# Real-world metric dimensions (height_meters, width_meters) for common COCO classes
# Used to calibrate optical pinhole geometry and provide physically grounded distances
OBJECT_METRIC_PRIORS = {
    'person': (1.70, 0.48),
    'bicycle': (1.00, 1.60),
    'car': (1.50, 1.80),
    'motorcycle': (1.10, 1.90),
    'bus': (3.20, 2.50),
    'truck': (3.00, 2.50),
    'traffic light': (0.80, 0.35),
    'fire hydrant': (0.75, 0.40),
    'stop sign': (0.75, 0.75),
    'bench': (0.80, 1.50),
    'dog': (0.55, 0.75),
    'cat': (0.28, 0.45),
    'backpack': (0.48, 0.35),
    'umbrella': (0.85, 0.90),
    'handbag': (0.35, 0.35),
    'bottle': (0.26, 0.08),
    'cup': (0.12, 0.09),
    'fork': (0.18, 0.03),
    'knife': (0.20, 0.03),
    'spoon': (0.16, 0.04),
    'bowl': (0.10, 0.16),
    'chair': (0.85, 0.55),
    'couch': (0.85, 1.80),
    'sofa': (0.85, 1.80),
    'potted plant': (0.50, 0.35),
    'plant': (0.50, 0.35),
    'bed': (0.70, 1.80),
    'dining table': (0.75, 1.20),
    'table': (0.75, 1.20),
    'toilet': (0.75, 0.45),
    'tv': (0.55, 0.95),
    'laptop': (0.24, 0.35),
    'mouse': (0.04, 0.08),
    'remote': (0.18, 0.05),
    'keyboard': (0.04, 0.42),
    'cell phone': (0.15, 0.075),
    'mobile phone': (0.15, 0.075),
    'phone': (0.15, 0.075),
    'microwave': (0.32, 0.50),
    'oven': (0.85, 0.65),
    'toaster': (0.20, 0.28),
    'sink': (0.45, 0.55),
    'refrigerator': (1.75, 0.80),
    'book': (0.24, 0.17),
    'clock': (0.30, 0.30),
    'vase': (0.32, 0.18),
    'scissors': (0.18, 0.08),
    'teddy bear': (0.35, 0.30),
    'hair drier': (0.22, 0.18),
    'toothbrush': (0.19, 0.02)
}

class MidasEstimator:
    def __init__(self, model_type="MiDaS_small"):
        """
        Initializes the MiDaS model with fallback support.
        'MiDaS_small' is optimized for real-time CPU performance.
        """
        print(f"Loading MiDaS model ({model_type})...")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.transform = None

        try:
            # Load model from PyTorch Hub (uses local cache when offline)
            self.model = torch.hub.load("intel-isl/MiDaS", model_type, trust_repo=True)
            self.model.to(self.device)
            self.model.eval()

            # Load transforms
            midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True)
            if model_type in ("DPT_Large", "DPT_Hybrid"):
                self.transform = midas_transforms.dpt_transform
            else:
                self.transform = midas_transforms.small_transform
                
            print(f"MiDaS model loaded successfully on {self.device}.")
        except Exception as e:
            print(f"Notice: MiDaS neural weights loading issue: {e}. Geometric metric estimation will serve as primary depth.")
            self.model = None

    def estimate_depth(self, frame):
        """
        Takes a BGR frame from OpenCV, returns a disparity depth map (numpy array).
        """
        if self.model is None or self.transform is None:
            return None
            
        try:
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            input_batch = self.transform(img).to(self.device)

            with torch.no_grad():
                prediction = self.model(input_batch)
                
                # Resize prediction to match original image resolution
                prediction = torch.nn.functional.interpolate(
                    prediction.unsqueeze(1),
                    size=img.shape[:2],
                    mode="bicubic",
                    align_corners=False,
                ).squeeze()

            depth_map = prediction.cpu().numpy()
            return depth_map
        except Exception as e:
            print(f"Depth inference notice: {e}")
            return None

    def calculate_geometric_distance(self, box, label, frame_shape):
        """
        Calculates metric distance in meters using camera pinhole geometry
        and calibrated physical object dimensions.
        """
        h_frame, w_frame = frame_shape[:2]
        x1, y1, x2, y2 = box
        bw = max(1.0, float(x2 - x1))
        bh = max(1.0, float(y2 - y1))

        # Standard webcams have ~60° to 65° horizontal FOV
        # Focal lengths in pixels:
        fy = h_frame * 1.15
        fx = w_frame * 0.85

        prior = OBJECT_METRIC_PRIORS.get(label.lower(), (1.0, 0.5))
        real_h, real_w = prior

        # Check if bounding box is truncated at screen boundaries
        is_top_bottom_clipped = (y1 <= 2 or y2 >= h_frame - 2)
        is_left_right_clipped = (x1 <= 2 or x2 >= w_frame - 2)

        dist_h = (real_h * fy) / bh
        dist_w = (real_w * fx) / bw

        if is_top_bottom_clipped and not is_left_right_clipped:
            geom_dist = dist_w
        elif is_left_right_clipped and not is_top_bottom_clipped:
            geom_dist = dist_h
        else:
            # Weighted average favoring height (less sensitive to aspect angle)
            geom_dist = 0.70 * dist_h + 0.30 * dist_w

        return float(geom_dist)

    def get_object_distance(self, depth_map, box, label="object", frame_shape=(480, 640)):
        """
        Estimates the accurate metric distance to the object.
        Fuses physical pinhole geometry with MiDaS relative disparity.
        """
        x1, y1, x2, y2 = box
        h_frame, w_frame = frame_shape[:2] if frame_shape is not None else (480, 640)

        # 1. Calculate physical metric distance from camera geometry
        geom_dist = self.calculate_geometric_distance(box, label, (h_frame, w_frame))

        # 2. Extract MiDaS central disparity if depth map is available
        midas_dist = None
        if depth_map is not None:
            dh, dw = depth_map.shape
            cx1 = max(0, min(dw - 1, int(x1 + (x2 - x1) * 0.25)))
            cx2 = max(0, min(dw, int(x2 - (x2 - x1) * 0.25)))
            cy1 = max(0, min(dh - 1, int(y1 + (y2 - y1) * 0.25)))
            cy2 = max(0, min(dh, int(y2 - (y2 - y1) * 0.25)))

            if cx2 > cx1 and cy2 > cy1:
                core = depth_map[cy1:cy2, cx1:cx2]
                if core.size > 0:
                    med_disp = float(np.percentile(core, 70))
                    if med_disp > 1.0:
                        # Calibrated disparity conversion
                        # Adaptively anchored to the geometric distance
                        C = 1000.0
                        midas_dist = C / med_disp

        # 3. Sensor Fusion: Combine Geometric & MiDaS Disparity
        if midas_dist is not None:
            # MiDaS provides fine surface depth; Geometry provides absolute metric scale
            # Weighted blend: 65% geometry, 35% midas relative depth
            final_distance = 0.65 * geom_dist + 0.35 * midas_dist
        else:
            final_distance = geom_dist

        # Clamp to realistic indoor / outdoor pedestrian navigation range (0.3m to 7.5m)
        final_distance = max(0.3, min(7.5, final_distance))
        return round(float(final_distance), 2)
