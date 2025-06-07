import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SERVER_HOST = os.environ.get('SERVER_HOST', '0.0.0.0')
    SERVER_PORT = int(os.environ.get('SERVER_PORT', 5000))
    COMMAND_TIMEOUT = int(os.environ.get('COMMAND_TIMEOUT', 15))
    CHATOP_CONTAINER_NAME = os.environ.get('CHATOP_SERVICE_NAME_OR_ID')
    DEBUG_MODE = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')

config = {
    'default': Config
}