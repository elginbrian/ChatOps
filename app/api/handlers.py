import re
from app.models.commands import COMMAND_GUIDE
from app.core import container_manager, image_manager, compose_manager, volume_manager, network_manager, system_manager, history_manager
from app.core import gemini_client
from flask import current_app

ACTION_HANDLERS = {
    "list_containers": container_manager.list_containers,
    "run_container": container_manager.run_container,
    "start_container": container_manager.start_container,
    "stop_container": container_manager.stop_container,
    "remove_container": container_manager.remove_container,
    "view_logs": container_manager.view_logs,
    "view_stats": container_manager.view_stats,
    "inspect_container": container_manager.inspect_container,
    "pull_image": image_manager.pull_image,
    "list_images": image_manager.list_images,
    "inspect_image": image_manager.inspect_image,
    "list_volumes": volume_manager.list_volumes,
    "remove_volume": volume_manager.remove_volume,
    "inspect_volume": volume_manager.inspect_volume,
    "list_networks": network_manager.list_networks,
    "inspect_network": network_manager.inspect_network,
    "compose_up": compose_manager.compose_up,
    "compose_down": compose_manager.compose_down,
    "prune_system": system_manager.prune_system,
    "clear_history": history_manager.clear_history,
    "restart_container": container_manager.restart_container,
    "remove_image": image_manager.remove_image,
    "system_info": system_manager.system_info,
    "system_version": system_manager.system_version,
    "pause_container": container_manager.pause_container,
    "unpause_container": container_manager.unpause_container,
    "create_volume": volume_manager.create_volume,
    "compose_ps": compose_manager.compose_ps,
    "compose_logs": compose_manager.compose_logs,
    "exec_in_container": container_manager.exec_in_container,
    "rename_container": container_manager.rename_container,
    "remove_network": network_manager.remove_network,
    "compose_restart": compose_manager.compose_restart,
    "compose_build": compose_manager.compose_build,
}

INSPECT_ACTION_MAP = {
    "container": "inspect_container",
    "kontainer": "inspect_container",
    "image": "inspect_image",
    "volume": "inspect_volume",
    "network": "inspect_network",
}

def parse_and_execute_command(user_command_str: str, history: list = None) -> dict:
    normalized_command = user_command_str.lower().strip()
    
    for cmd_def in COMMAND_GUIDE:
        match = re.fullmatch(cmd_def["pattern"], normalized_command)
        if match:
            action = cmd_def["action"]
            params = match.groupdict()

            if action == "inspect_object":
                object_type = params.get("object_type")
                resolved_action = INSPECT_ACTION_MAP.get(object_type)
                if not resolved_action:
                    return {"output": None, "error": f"Error: Tipe objek '{object_type}' tidak dikenal untuk inspect.", "output_type": "text"}
                action = resolved_action

            if action in ACTION_HANDLERS:
                if "params_map" in cmd_def:
                    params.update(cmd_def["params_map"])
                output_data, error_str = ACTION_HANDLERS[action](params)

                output_type = "text"
                if action in ["list_containers", "list_images", "view_stats", "view_logs", "list_volumes", "list_networks"]:
                    output_type = "table"
                elif action in [
                    "run_container", "stop_container", "remove_container", "pull_image", 
                    "compose_up", "compose_down", "start_container", "remove_volume", 
                    "prune_system", "remove_image", "restart_container", "pause_container", 
                    "unpause_container", "create_volume", "rename_container", "remove_network"
                ]:
                    output_type = "action_receipt"
                elif "inspect" in action or action in ["system_info", "system_version"]:
                    output_type = "inspect"
                
                return {"output": output_data, "error": error_str, "output_type": output_type}
            else:
                return {"output": None, "error": f"Error: Aksi '{action}' belum terdefinisi di backend.", "output_type": "text"}

    current_app.logger.info(f"Command '{user_command_str}' not found in guide. Passing to Gemini.")
    return gemini_client.handle_gemini_request(user_command_str, history or [])