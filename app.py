import subprocess
import logging
import re
from flask import Flask, render_template, request, jsonify

DEBUG_MODE = True
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5000
COMMAND_TIMEOUT = 15

app = Flask(__name__)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

COMMAND_GUIDE = [
    {
        "id": "list_all_containers",
        "pattern": r"^(tampilkan|list|lihat)\s+(semua\s+)?container(s)?$",
        "action": "list_containers",
        "params_map": {"all": True},
        "description": "Menampilkan semua kontainer (berjalan dan berhenti).",
        "example": "list containers"
    },
    {
        "id": "list_running_containers",
        "pattern": r"^(tampilkan|list|lihat)\s+container(s)?\s+(sedang\s+|yang\s+)?(jalan|aktif|running)$",
        "action": "list_containers",
        "params_map": {"all": False},
        "description": "Menampilkan hanya kontainer yang sedang berjalan.",
        "example": "list container yang jalan"
    },
    {
        "id": "run_container",
        "pattern": r"^(jalankan|nyalakan|start)\s+(?:kontainer|container|layanan|servis)\s+(?P<name>[a-zA-Z0-9_.-]+)\s+dari\s+image\s+(?P<image>[a-zA-Z0-9/:_.-]+)(?:\s+dengan\s+port\s+(?P<ports>\d{1,5}:\d{1,5}(?:,\d{1,5}:\d{1,5})*))?$",
        "action": "run_container",
        "description": "Menjalankan kontainer baru dari sebuah image. Opsional: 'dengan port HOST:CONTAINER,HOST2:CONTAINER2'.",
        "example": "jalankan webku dari image nginx:latest dengan port 8080:80"
    },
    {
        "id": "stop_container",
        "pattern": r"^(hentikan|matikan|stop)\s+(?:kontainer|container|layanan|servis)\s+(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "stop_container",
        "description": "Menghentikan kontainer yang sedang berjalan berdasarkan namanya.",
        "example": "stop webku"
    },
    {
        "id": "remove_container",
        "pattern": r"^(hapus|buang|remove)\s+(?:kontainer|container|layanan|servis)\s+(?P<name>[a-zA-Z0-9_.-]+)$",
        "action": "remove_container",
        "description": "Menghapus kontainer yang sudah berhenti berdasarkan namanya.",
        "example": "hapus webku"
    },
    {
        "id": "view_logs",
        "pattern": r"^(lihat|tampilkan)\s+log(s)?\s+(?:dari\s+)?(?:kontainer|container|layanan|servis)\s+(?P<name>[a-zA-Z0-9_.-]+)(?:\s+sebanyak\s+(?P<lines>\d+)\s+baris)?$",
        "action": "view_logs",
        "description": "Menampilkan log dari sebuah kontainer. Opsional: 'sebanyak JUMLAH baris'.",
        "example": "lihat log webku sebanyak 50 baris"
    }
]

def execute_shell_command(command_parts: list[str], timeout: int = COMMAND_TIMEOUT) -> tuple[str, str, int]:
    try:
        app.logger.info(f"Mengeksekusi: {' '.join(command_parts)}")
        result = subprocess.run(
            command_parts, capture_output=True, text=True, check=False, timeout=timeout
        )
        stdout_res = result.stdout.strip()
        stderr_res = result.stderr.strip()
        app.logger.info(f"Selesai (kode: {result.returncode}). Stdout: '{stdout_res[:100]}...', Stderr: '{stderr_res[:100]}...'")
        if result.returncode != 0 and not stderr_res:
            stderr_res = f"Perintah selesai dengan kode error {result.returncode} tanpa output error spesifik."
        elif result.returncode != 0 and stderr_res:
             stderr_res = f"Perintah gagal (kode: {result.returncode}): {stderr_res}"
        return stdout_res, stderr_res, result.returncode
    except FileNotFoundError:
        err_msg = f"Error: '{command_parts[0]}' tidak ditemukan. Pastikan terinstal dan ada di PATH."
        app.logger.error(err_msg)
        return "", err_msg, -1
    except subprocess.TimeoutExpired:
        err_msg = f"Error: Perintah '{' '.join(command_parts)}' timeout ({timeout}d)."
        app.logger.error(err_msg)
        return "", err_msg, -2
    except Exception as e:
        err_msg = f"Error tak terduga: {str(e)}"
        app.logger.exception("Error tak terduga saat eksekusi:")
        return "", err_msg, -3

def _handle_list_containers(params: dict) -> tuple[str, str, int]:
    cmd_parts = ["docker", "ps"]
    if params.get("all", False):
        cmd_parts.append("-a")
    return execute_shell_command(cmd_parts)

def _handle_run_container(params: dict) -> tuple[str, str, int]:
    name = params.get("name")
    image = params.get("image")
    ports_str = params.get("ports")

    if not name or not image:
        return "", "Error: Nama kontainer dan nama image dibutuhkan untuk menjalankan kontainer.", -1
    if not re.match(r"^[a-zA-Z0-9_.-]+$", name) or \
       not re.match(r"^[a-zA-Z0-9/:_.-]+$", image):
        return "", "Error: Nama kontainer/image mengandung karakter tidak valid.", -1

    cmd_parts = ["docker", "run", "-d", "--name", name]
    if ports_str:
        if not re.match(r"^\d{1,5}:\d{1,5}(?:,\d{1,5}:\d{1,5})*$", ports_str):
             return "", "Error: Format port tidak valid. Gunakan HOST:CONTAINER atau HOST:CONTAINER,HOST2:CONTAINER2", -1
        port_mappings = ports_str.split(',')
        for p_map in port_mappings:
            cmd_parts.extend(["-p", p_map.strip()])
    cmd_parts.append(image)
    return execute_shell_command(cmd_parts)

def _handle_stop_container(params: dict) -> tuple[str, str, int]:
    name = params.get("name")
    if not name:
        return "", "Error: Nama kontainer dibutuhkan untuk menghentikan kontainer.", -1
    if not re.match(r"^[a-zA-Z0-9_.-]+$", name):
        return "", "Error: Nama kontainer mengandung karakter tidak valid.", -1
    cmd_parts = ["docker", "stop", name]
    return execute_shell_command(cmd_parts)

def _handle_remove_container(params: dict) -> tuple[str, str, int]:
    name = params.get("name")
    if not name:
        return "", "Error: Nama kontainer dibutuhkan untuk menghapus kontainer.", -1
    if not re.match(r"^[a-zA-Z0-9_.-]+$", name):
        return "", "Error: Nama kontainer mengandung karakter tidak valid.", -1
    cmd_parts = ["docker", "rm", name]
    return execute_shell_command(cmd_parts)

def _handle_view_logs(params: dict) -> tuple[str, str, int]:
    name = params.get("name")
    lines = params.get("lines", "50") 

    if not name:
        return "", "Error: Nama kontainer dibutuhkan untuk melihat log.", -1
    if not re.match(r"^[a-zA-Z0-9_.-]+$", name):
        return "", "Error: Nama kontainer mengandung karakter tidak valid.", -1
    if lines and not re.match(r"^\d+$", lines):
        return "", "Error: Jumlah baris harus berupa angka.", -1
        
    cmd_parts = ["docker", "logs", "--tail", str(lines), name]
    return execute_shell_command(cmd_parts)

ACTION_HANDLERS = {
    "list_containers": _handle_list_containers,
    "run_container": _handle_run_container,
    "stop_container": _handle_stop_container,
    "remove_container": _handle_remove_container,
    "view_logs": _handle_view_logs,
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
                
                output, error, return_code = ACTION_HANDLERS[action](params)
                
                if return_code == 0 and not output and not error:
                    output = f"Perintah '{cmd_def['id']}' berhasil dieksekusi tanpa output spesifik."
                return output, error
            else:
                return "", f"Error: Aksi '{action}' belum diimplementasikan di backend."
    return "", f"Error: Perintah '{user_command_str}' tidak dikenali atau formatnya salah."


@app.route('/')
def index():
    app.logger.info(f"Permintaan ke '/' dari {request.remote_addr}")
    return render_template('index.html', command_guide=COMMAND_GUIDE)


@app.route('/api/command', methods=['POST'])
def handle_command_route():
    try:
        data = request.get_json()
        if not data or 'command' not in data or not isinstance(data['command'], str):
            app.logger.warning(f"Permintaan buruk dari {request.remote_addr}")
            return jsonify({'error': "Permintaan buruk: Field 'command' (string) dibutuhkan.", 'output': '', 'received_command': str(data.get('command', '')) if data else ''}), 400
        
        user_command_str = data.get('command', '').strip()
        app.logger.info(f"Menerima perintah dari {request.remote_addr}: '{user_command_str}'")

        output_str, error_str = parse_and_execute_command(user_command_str)

        response_data = {
            'output': output_str,
            'error': error_str,
            'received_command': user_command_str
        }
        return jsonify(response_data)

    except Exception as e:
        app.logger.exception(f"Error internal server saat memproses /api/command dari {request.remote_addr}:")
        internal_error_msg = "Terjadi kesalahan internal pada server." if not DEBUG_MODE else str(e)
        return jsonify({'error': internal_error_msg, 'output': '', 'received_command': data.get('command', '') if 'data' in locals() and data else '' }), 500

if __name__ == '__main__':
    app.logger.info(f"Memulai server Flask pada {SERVER_HOST}:{SERVER_PORT} dengan mode debug: {DEBUG_MODE}")
    app.run(debug=DEBUG_MODE, host=SERVER_HOST, port=SERVER_PORT)