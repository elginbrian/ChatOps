import os
import re
import subprocess
from flask import current_app

def _run_compose_command(command: list) -> tuple[str, str]:
    compose_file_path = os.path.join(current_app.root_path, '..', 'docker-compose.yml') #
    if not os.path.exists(compose_file_path): #
        return "", "Error: docker-compose.yml tidak ditemukan di root proyek." #
    
    cmd_list = ['docker-compose', '-f', compose_file_path] + command #
    
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True, check=True, timeout=120) #
        output = result.stdout.strip() if result.stdout else "(no standard output)" #
        error_output = result.stderr.strip() if result.stderr else "(no standard error)" #
        return f"Output:\n{output}\n\nLogs/Errors:\n{error_output}", "" #
    except subprocess.CalledProcessError as e: #
        return "", f"Error saat menjalankan docker-compose:\n{e.stderr}" #
    except Exception as e: #
        return "", f"Error tak terduga: {str(e)}" #

def compose_up(params: dict) -> tuple[str, str]: #
    service = params.get('service') #
    command = ['up', '-d'] #
    if service: #
        if not re.match(r"^[a-zA-Z0-9_.-]+$", service): #
            return "", "Error: Nama service tidak valid." #
        command.append(service) #
    return _run_compose_command(command) #

def compose_down(params: dict) -> tuple[str, str]: #
    return _run_compose_command(['down']) #