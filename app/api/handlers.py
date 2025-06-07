import re
from app.models.commands import COMMAND_GUIDE
from app.core import docker_service
from flask import current_app

ACTION_HANDLERS = {
    "list_containers": docker_service.list_containers,
    "run_container": docker_service.run_container,
    "stop_container": docker_service.stop_container,
    "remove_container": docker_service.remove_container,
    "view_logs": docker_service.view_logs,
    "view_stats": docker_service.view_stats,
    "pull_image": docker_service.pull_image,
    "list_images": docker_service.list_images,
    "compose_up": docker_service.compose_up,
    "compose_down": docker_service.compose_down,
}

def parse_and_execute_command(user_command_str: str) -> tuple[str, str]:
    normalized_command = user_command_str.lower().strip()
    for cmd_def in COMMAND_GUIDE:
        match = re.fullmatch(cmd_def["pattern"], normalized_command)
        if match:
            action = cmd_def["action"]
            if action in ACTION_HANDLERS:
                params = match.groupdict()
                if "params_map" in cmd_def: 
                    params.update(cmd_def["params_map"])
                
                output, error = ACTION_HANDLERS[action](params)
                
                if not error and not output: 
                    output = f"Perintah '{cmd_def.get('id', action)}' berhasil dieksekusi."
                return output, error
            else:
                return "", f"Error: Aksi '{action}' belum terdefinisi di backend."
    return "", f"Error: Perintah '{user_command_str}' tidak dikenali atau formatnya salah."