from flask import Flask
from models.models import db, User
from flask_login import LoginManager
import os
import threading

# Import AI modules
from vision.yolo_detector import YoloDetector
from depth.midas_estimator import MidasEstimator
from vision.direction_analyzer import DirectionAnalyzer
from tts.priority_engine import PriorityEngine
from tts.audio_guide import AudioGuide

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'crossecho_secret_key_123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Initialize Database
    with app.app_context():
        db.create_all()

    # Initialize AI Pipeline globally inside the API routes
    from routes.api_routes import pipeline
    
    # To prevent blocking the main thread during startup, we load heavy models in a background thread
    def load_models():
        print("Starting AI Model initialization pipeline...")
        pipeline['detector'] = YoloDetector("yolov8n.pt")
        pipeline['depth_estimator'] = MidasEstimator("MiDaS_small")
        pipeline['direction_analyzer'] = DirectionAnalyzer()
        pipeline['priority_engine'] = PriorityEngine()
        pipeline['audio_guide'] = AudioGuide()
        print("AI Pipeline fully loaded and ready.")
        
    threading.Thread(target=load_models, daemon=True).start()

    # Register Blueprints
    from auth.auth_routes import auth_bp
    from routes.main_routes import main_bp
    from routes.api_routes import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app

if __name__ == '__main__':
    app = create_app()
    # Reverted to standard HTTP. Access via http://127.0.0.1:5000 for secure context.
    # use_reloader=False prevents watchdog reloads when torch hub models are initialized
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
