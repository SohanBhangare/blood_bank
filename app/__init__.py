from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.donors import donors_bp
    from app.routes.inventory import inventory_bp
    from app.routes.requests import requests_bp
    from app.routes.reports import reports_bp
    from app.routes.donor_portal import donor_portal_bp
    from app.routes.camps import camps_bp
    from app.routes.hospitals import hospitals_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(donors_bp, url_prefix='/donors')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(requests_bp, url_prefix='/requests')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(donor_portal_bp, url_prefix='/portal')
    app.register_blueprint(camps_bp, url_prefix='/camps')
    app.register_blueprint(hospitals_bp, url_prefix='/hospitals')

    # Register template filters
    @app.template_filter('badge_status')
    def badge_status_filter(status):
        status_colors = {
            'Available': 'bg-emerald-100 text-emerald-800 border-emerald-300',
            'Approved': 'bg-emerald-100 text-emerald-800 border-emerald-300',
            'Passed': 'bg-emerald-100 text-emerald-800 border-emerald-300',
            'Eligible': 'bg-emerald-100 text-emerald-800 border-emerald-300',
            'Dispatched': 'bg-blue-100 text-blue-800 border-blue-300',
            'Reserved': 'bg-amber-100 text-amber-800 border-amber-300',
            'Pending': 'bg-yellow-100 text-yellow-800 border-yellow-300',
            'Deferred': 'bg-orange-100 text-orange-800 border-orange-300',
            'Urgent': 'bg-orange-100 text-orange-800 border-orange-300',
            'Emergency': 'bg-rose-100 text-rose-800 border-rose-300 font-bold animate-pulse',
            'Expired': 'bg-red-100 text-red-800 border-red-300',
            'Rejected': 'bg-red-100 text-red-800 border-red-300',
            'Discarded': 'bg-gray-200 text-gray-800 border-gray-300',
            'Inactive': 'bg-gray-200 text-gray-800 border-gray-300'
        }
        return status_colors.get(status, 'bg-gray-100 text-gray-700 border-gray-200')

    return app
