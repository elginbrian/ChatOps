from flask import Flask, render_template, g
from config import config
from app.models.commands import COMMAND_GUIDE
import logging

def create_app(config_name: str):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])
    
    app.secret_key = app.config['SECRET_KEY']

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    if not app.config.get('CHATOP_CONTAINER_NAME'):
        app.logger.warning("Environment variable CHATOP_SERVICE_NAME_OR_ID tidak diatur.")
        
    if not app.config.get('CHATOPS_PASSWORD'):
        app.logger.warning("CHATOPS_PASSWORD tidak diatur dari build-arg. Autentikasi akan gagal.")

    from .api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/')

    return app