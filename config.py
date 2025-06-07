import os

class Config:
    SERVER_HOST = '0.0.0.0'
    SERVER_PORT = 5000
    COMMAND_TIMEOUT = 15
    CHATOP_CONTAINER_NAME = 'chatops_service'
    DEBUG_MODE = True
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key') 
    CHATOPS_PASSWORD = os.getenv('CHATOPS_PASSWORD')

config = {
    'default': Config
}