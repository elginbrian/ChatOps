def build_response(action: str, output_data: any, error_str: str, received_command: str) -> dict:
    if error_str:
        return build_error_response(error_str, received_command)

    output_type = _get_output_type_for_action(action)
    
    if output_type == "table" and not output_data:
        output_data = []

    return {
        "output": output_data,
        "error": None,
        "output_type": output_type,
        "received_command": received_command,
    }


def build_error_response(error_message: str, received_command: str) -> dict:
    return {
        "output": None,
        "error": error_message,
        "output_type": "text",
        "received_command": received_command,
    }


def _get_output_type_for_action(action: str) -> str:
    if action in ["list_containers", "list_images", "view_stats", "view_logs"]:
        return "table"
    elif action in ["run_container", "stop_container", "remove_container", "pull_image", "compose_up", "compose_down", "start_container"]:
        return "action_receipt"
    else:
        return "text"