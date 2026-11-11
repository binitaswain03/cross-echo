from flask import Blueprint, render_template
from flask_login import current_user, login_required
from models.models import db, NavigationHistory, Settings
from sqlalchemy import func
import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('landing.html', is_logged_in=current_user.is_authenticated)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    user_id = current_user.id
    
    # Calculate stats
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
    
    top_object = f"{top_obj_query.object_name.capitalize()} ({top_obj_query.count})" if top_obj_query else "N/A"
    
    # Object counts for charts
    obj_counts = db.session.query(
        NavigationHistory.object_name, 
        func.count(NavigationHistory.id).label('count')
    ).filter_by(user_id=user_id).group_by(NavigationHistory.object_name).order_by(func.count(NavigationHistory.id).desc()).all()
    
    object_counts = {obj.object_name: obj.count for obj in obj_counts}
    
    stats = {
        'total_detections': total_detections,
        'today_detections': today_detections,
        'top_object': top_object,
        'object_counts': object_counts
    }
    
    recent_detections = NavigationHistory.query.filter_by(user_id=user_id).order_by(NavigationHistory.timestamp.desc()).limit(10).all()
    
    return render_template('dashboard.html', user=current_user, stats=stats, recent_detections=recent_detections)

@main_bp.route('/detection')
@login_required
def detection():
    return render_template('detection.html', user=current_user)
