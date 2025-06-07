import json
import os
import time
import uuid
from flask import current_app

HISTORY_FILE_PATH = os.path.join(current_app.instance_path, 'chat_history.json')

def _get_or_create_history_file():
    try:
        os.makedirs(current_app.instance_path)
    except OSError:
        pass  
    
    if not os.path.exists(HISTORY_FILE_PATH):
        initial_data = {"conversations": {}, "last_active_id": None}
        with open(HISTORY_FILE_PATH, 'w') as f:
            json.dump(initial_data, f, indent=2)
        return initial_data
    
    try:
        with open(HISTORY_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"conversations": {}, "last_active_id": None}

def _save_history_data(data):
    with open(HISTORY_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_conversations_list():
    data = _get_or_create_history_file()
    last_active_id = data.get('last_active_id')
    
    conv_list = [
        {
            "id": conv_id,
            "title": conv_data.get("title", "Tanpa Judul"),
            "created_at": conv_data.get("created_at"),
            "is_last_active": conv_id == last_active_id
        }
        for conv_id, conv_data in data.get("conversations", {}).items()
    ]
    
    conv_list.sort(key=lambda x: x.get('created_at', 0), reverse=True)
    
    return conv_list

def get_conversation_messages(conv_id):
    data = _get_or_create_history_file()
    return data.get("conversations", {}).get(conv_id, {}).get("messages", [])

def set_last_active(conv_id):
    data = _get_or_create_history_file()
    if conv_id in data['conversations']:
        data['last_active_id'] = conv_id
        _save_history_data(data)

def create_new_conversation(user_command, bot_response):
    data = _get_or_create_history_file()
    
    conv_id = str(uuid.uuid4())
    title = user_command[:50] + '...' if len(user_command) > 50 else user_command
    
    new_conv = {
        "id": conv_id,
        "title": title,
        "created_at": time.time(),
        "messages": [
            {
                "user_command": user_command,
                "bot_response": bot_response
            }
        ]
    }
    
    data["conversations"][conv_id] = new_conv
    _save_history_data(data)
    
    return conv_id

def add_message_to_conversation(conv_id, user_command, bot_response):
    data = _get_or_create_history_file()
    
    if conv_id in data.get("conversations", {}):
        data["conversations"][conv_id]["messages"].append({
            "user_command": user_command,
            "bot_response": bot_response
        })
        _save_history_data(data)

def delete_conversation(conv_id):
    data = _get_or_create_history_file()
    
    if conv_id in data.get("conversations", {}):
        del data["conversations"][conv_id]
        if data.get('last_active_id') == conv_id:
            data['last_active_id'] = None
        _save_history_data(data)
        return True
    return False