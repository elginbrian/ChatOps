import re
from app.models.commands import COMMAND_GUIDE
from app.core import container_manager, image_manager, compose_manager
from flask import current_app

ACTION_HANDLERS = {
    "list_containers": container_manager.list_containers,
    "run_container": container_manager.run_container,
    "start_container": container_manager.start_container,
    "stop_container": container_manager.stop_container,
    "remove_container": container_manager.remove_container,
    "view_logs": container_manager.view_logs,
    "view_stats": container_manager.view_stats,
    
    "pull_image": image_manager.pull_image,
    "list_images": image_manager.list_images,
    
    "compose_up": compose_manager.compose_up,
    "compose_down": compose_manager.compose_down,
}

def parse_and_execute_command(user_command_str: str) -> dict: #
    normalized_command = user_command_str.lower().strip() #
    for cmd_def in COMMAND_GUIDE: #
        match = re.fullmatch(cmd_def["pattern"], normalized_command) #
        if match: #
            action = cmd_def["action"] #
            if action in ACTION_HANDLERS: #
                params = match.groupdict() #
                if "params_map" in cmd_def: #
                    params.update(cmd_def["params_map"]) #
               
                output_data, error_str = ACTION_HANDLERS[action](params) #
                
                output_type = "text" #
                if action in ["list_containers", "list_images", "view_stats", "view_logs"]: #
                    output_type = "table" #
                elif action in ["run_container", "stop_container", "remove_container", "pull_image", "compose_up", "compose_down" , "start_container"]: #
                    output_type = "action_receipt" #
                
                return { #
                    "output": output_data, #
                    "error": error_str, #
                    "output_type": output_type #
                }
            else: #
                return {"output": None, "error": f"Error: Aksi '{action}' belum terdefinisi di backend.", "output_type": "text"} #
                
    return {"output": None, "error": f"Error: Perintah '{user_command_str}' tidak dikenali atau formatnya salah.", "output_type": "text"} #