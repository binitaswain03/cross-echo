from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from models.models import db, NavigationHistory
import base64
import numpy as np
import cv2

api_bp = Blueprint('api', __name__)

# Global instances of ML models (initialized in app.py)
# We will inject these from app.py or use a registry pattern.
# For simplicity in Flask, we can store them in current_app, but a direct import is easier if they are singleton-like.
# We'll create a globally accessible config object or just import them.
import sys
pipeline = {
    'detector': None,
    'depth_estimator': None,
    'direction_analyzer': None,
    'priority_engine': None,
    'audio_guide': None
}

@api_bp.route('/detect', methods=['POST'])
@login_required
def detect():
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'error': 'No image data provided.'}), 400
        
    try:
        # Decode base64 image
        image_data = data['image']
        if ',' in image_data:
            _, image_data = image_data.split(',', 1)
            
        img_bytes = base64.b64decode(image_data)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': 'Invalid image format.'}), 400
            
        # Get frame dimensions
        h, w, _ = frame.shape
        
        # Client language preference: 'en' (default), 'hi', 'or'
        client_lang = data.get('language', 'en')
        if client_lang not in ('en', 'hi', 'or'):
            client_lang = 'en'

        # 1. Run YOLO Object Detection with client or default threshold
        conf_threshold = float(data.get('conf_threshold', 0.35))
        detections = pipeline['detector'].detect(frame, conf_threshold=conf_threshold) if pipeline['detector'] else []
        
        # 2. Run Depth Estimation (Optional/Heavy)
        depth_map = None
        if detections and pipeline['depth_estimator']:
            depth_map = pipeline['depth_estimator'].estimate_depth(frame)
            
        processed_detections = []
        for det in detections:
            # 3. Physically Grounded Metric Distance Estimation
            distance = -1.0
            if pipeline['depth_estimator']:
                distance = pipeline['depth_estimator'].get_object_distance(
                    depth_map, 
                    det['box'], 
                    label=det['label'], 
                    frame_shape=(h, w)
                )
            det['distance'] = distance
            
            # 4. Granular Direction & Angle Analysis
            dir_data = {
                'direction': 'Ahead', 'direction_en': 'Ahead', 'direction_hi': 'सामने', 
                'direction_or': 'ସାମ୍ନାରେ', 'direction_or_phonetic': 'samnare',
                'angle': 0.0, 'angle_str': '0° Center', 'clock': '12 o\'clock', 'pan': 0.0
            }
            if pipeline['direction_analyzer']:
                dir_data = pipeline['direction_analyzer'].analyze(w, det['box'])
                
            det['direction'] = dir_data['direction']
            det['direction_en'] = dir_data['direction_en']
            det['direction_hi'] = dir_data['direction_hi']
            det['direction_or'] = dir_data['direction_or']
            det['direction_or_phonetic'] = dir_data['direction_or_phonetic']
            det['angle'] = dir_data['angle']
            det['angle_str'] = dir_data['angle_str']
            det['clock'] = dir_data['clock']
            det['pan'] = dir_data['pan']
            det['direction_info'] = dir_data
            
            processed_detections.append(det)
            
        # 5. Multilingual Priority & Auditory Alerts
        alerts = []
        if pipeline['priority_engine']:
            alerts = pipeline['priority_engine'].process_detections(processed_detections, lang=client_lang)
            if pipeline['audio_guide']:
                for alert in alerts:
                    pipeline['audio_guide'].speak(alert)
                
        # 6. Log to Database with smart in-memory cooldown to keep SQLite snappy
        import time
        if not hasattr(detect, 'db_log_cooldown'):
            detect.db_log_cooldown = {}
        now_ts = time.time()
        
        for det in processed_detections:
            cache_k = (current_user.id, det['label'])
            last_logged = detect.db_log_cooldown.get(cache_k, 0)
            if now_ts - last_logged >= 3.5: # 3.5 second debounce per object
                dir_display = f"{det['direction']} ({det['clock']})"
                new_log = NavigationHistory(
                    user_id=current_user.id,
                    object_name=det['label'],
                    confidence=det['confidence'],
                    distance=det['distance'],
                    direction=dir_display
                )
                db.session.add(new_log)
                detect.db_log_cooldown[cache_k] = now_ts
        db.session.commit()
        
        return jsonify({
            'success': True,
            'detections': processed_detections,
            'count': len(processed_detections),
            'alerts': alerts,
            'language': client_lang
        })
        
    except Exception as e:
        print(f"Error in /api/detect: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """Returns live navigation stats and recent detections for the dashboard."""
    try:
        from sqlalchemy import func
        import datetime
        user_id = current_user.id
        
        total_detections = NavigationHistory.query.filter_by(user_id=user_id).count()
        
        today = datetime.datetime.utcnow().date()
        today_detections = NavigationHistory.query.filter(
            NavigationHistory.user_id == user_id,
            func.date(NavigationHistory.timestamp) == today
        ).count()
        
        # Top object
        top_obj_query = db.session.query(
            NavigationHistory.object_name, 
            func.count(NavigationHistory.id).label('count')
        ).filter_by(user_id=user_id).group_by(NavigationHistory.object_name).order_by(func.count(NavigationHistory.id).desc()).first()
        
        top_object = f"{top_obj_query.object_name.capitalize()} ({top_obj_query.count})" if top_obj_query else "None"
        
        # Object counts for charts
        obj_counts = db.session.query(
            NavigationHistory.object_name, 
            func.count(NavigationHistory.id).label('count')
        ).filter_by(user_id=user_id).group_by(NavigationHistory.object_name).order_by(func.count(NavigationHistory.id).desc()).all()
        
        object_counts = {obj.object_name: obj.count for obj in obj_counts}
        
        recent_rows = NavigationHistory.query.filter_by(user_id=user_id).order_by(NavigationHistory.timestamp.desc()).limit(10).all()
        recent_list = []
        for r in recent_rows:
            recent_list.append({
                'id': r.id,
                'object_name': r.object_name,
                'confidence': r.confidence,
                'distance': r.distance,
                'direction': r.direction,
                'timestamp': r.timestamp.strftime('%H:%M:%S') if r.timestamp else ''
            })
            
        return jsonify({
            'success': True,
            'stats': {
                'total_detections': total_detections,
                'today_detections': today_detections,
                'top_object': top_object,
                'object_counts': object_counts
            },
            'recent': recent_list
        })
    except Exception as e:
        print(f"Error in /api/stats: {e}")
        return jsonify({'error': str(e)}), 500

