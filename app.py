import logging
import re
import docker 
from flask import Flask, render_template, request, jsonify

DEBUG_MODE = True
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5000
COMMAND_TIMEOUT = 15

app = Flask(__name__)
docker_client = None

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
    },
    {
        "id": "pull_image",
        "pattern": r"^(tarik|pull)\s+image\s+(?P<image>[a-zA-Z0-9/:_.-]+)$",
        "action": "pull_image",
        "description": "Menarik (pull) image dari registry.",
        "example": "pull image alpine:latest"
    },
    {
        "id": "list_images",
        "pattern": r"^(tampilkan|list|lihat)\s+image(s)?$",
        "action": "list_images",
        "description": "Menampilkan semua image Docker yang ada di lokal.",
        "example": "list images"
    }
]

def get_docker_client():
    global docker_client
    if docker_client is None:
        try:
            docker_client = docker.from_env()
            docker_client.ping() 
            app.logger.info("Koneksi Docker SDK berhasil.")
        except docker.errors.DockerException as e:
            app.logger.error(f"Gagal terkoneksi ke Docker daemon via SDK: {e}")
            docker_client = "ERROR" 
    return docker_client if docker_client != "ERROR" else None


def _format_container_list(containers):
    if not containers:
        return "Tidak ada kontainer."
    output = "CONTAINER ID\tIMAGE\t\tCOMMAND\t\tCREATED\t\tSTATUS\t\tPORTS\t\tNAMES\n"
    output += "----------------------------------------------------------------------------------------------------------------------\n"
    for container in containers:
        name = container.name
        image = container.attrs['Config']['Image']
        command = container.attrs['Config']['Cmd']
        command_str = ' '.join(command) if command else ''
        created = container.attrs['Created'][:19].replace('T', ' ') # Format datetime
        status = container.status
        ports = container.ports
        ports_str = []
        if ports:
            for internal_port, host_ports_list in ports.items():
                if host_ports_list:
                    for host_port_info in host_ports_list:
                        ports_str.append(f"{host_port_info['HostIp']}:{host_port_info['HostPort']}->{internal_port}")
        
        output += f"{container.short_id}\t{image[:20]}\t{command_str[:20]}\t{created}\t{status[:20]}\t{', '.join(ports_str)[:20]}\t{name}\n"
    return output

def _handle_list_containers(params: dict) -> tuple[str, str]:
    client = get_docker_client()
    if not client:
        return "", "Error: Tidak dapat terhubung ke Docker daemon."
    try:
        all_containers = params.get("all", False)
        containers = client.containers.list(all=all_containers)
        return _format_container_list(containers), ""
    except docker.errors.APIError as e:
        app.logger.error(f"Docker API Error saat list containers: {e}")
        return "", f"Error Docker API: {e.explanation or str(e)}"
    except Exception as e:
        app.logger.exception("Error tak terduga saat list containers:")
        return "", f"Error tak terduga: {str(e)}"

def _handle_run_container(params: dict) -> tuple[str, str]:
    client = get_docker_client()
    if not client:
        return "", "Error: Tidak dapat terhubung ke Docker daemon."

    name = params.get("name")
    image = params.get("image")
    ports_str = params.get("ports")

    if not name or not image:
        return "", "Error: Nama kontainer dan nama image dibutuhkan."
    if not re.match(r"^[a-zA-Z0-9_.-]+$", name) or \
       not re.match(r"^[a-zA-Z0-9/:_.-]+$", image):
        return "", "Error: Nama kontainer/image mengandung karakter tidak valid."

    ports_dict = {}
    if ports_str:
        if not re.match(r"^\d{1,5}:\d{1,5}(?:,\d{1,5}:\d{1,5})*$", ports_str):
             return "", "Error: Format port tidak valid. Gunakan HOST:CONTAINER atau HOST:CONTAINER,HOST2:CONTAINER2"
        try:
            for p_map_str in ports_str.split(','):
                host_port, container_port = p_map_str.strip().split(':')
                ports_dict[f"{container_port.strip()}/tcp"] = int(host_port.strip()) 
        except ValueError:
            return "", "Error: Format port tidak valid (pastikan angka)."


    try:
        app.logger.info(f"Mencoba menjalankan image '{image}' sebagai kontainer '{name}' dengan port {ports_dict if ports_dict else 'tidak ada'}")
        container = client.containers.run(image, detach=True, name=name, ports=ports_dict if ports_dict else None)
        return f"Kontainer '{container.name}' (ID: {container.short_id}) berhasil dijalankan dari image '{image}'.", ""
    except docker.errors.ImageNotFound:
        app.logger.warning(f"Image '{image}' tidak ditemukan saat mencoba run.")
        return "", f"Error: Image '{image}' tidak ditemukan. Anda mungkin perlu melakukan 'pull image {image}' terlebih dahulu."
    except docker.errors.APIError as e:
        app.logger.error(f"Docker API Error saat run container: {e}")
        return "", f"Error Docker API: {e.explanation or str(e)}"
    except Exception as e:
        app.logger.exception("Error tak terduga saat run container:")
        return "", f"Error tak terduga: {str(e)}"


def _handle_stop_container(params: dict) -> tuple[str, str]:
    client = get_docker_client()
    if not client: return "", "Error: Tidak dapat terhubung ke Docker daemon."
    name = params.get("name")
    if not name: return "", "Error: Nama kontainer dibutuhkan."
    if not re.match(r"^[a-zA-Z0-9_.-]+$", name): return "", "Error: Nama kontainer mengandung karakter tidak valid."
    try:
        container = client.containers.get(name)
        container.stop()
        return f"Kontainer '{name}' berhasil dihentikan.", ""
    except docker.errors.NotFound:
        return "", f"Error: Kontainer '{name}' tidak ditemukan."
    except docker.errors.APIError as e:
        return "", f"Error Docker API: {e.explanation or str(e)}"
    except Exception as e: return "", f"Error tak terduga: {str(e)}"

def _handle_remove_container(params: dict) -> tuple[str, str]:
    client = get_docker_client()
    if not client: return "", "Error: Tidak dapat terhubung ke Docker daemon."
    name = params.get("name")
    if not name: return "", "Error: Nama kontainer dibutuhkan."
    if not re.match(r"^[a-zA-Z0-9_.-]+$", name): return "", "Error: Nama kontainer mengandung karakter tidak valid."
    try:
        container = client.containers.get(name)
        if container.status == "running":
            return "", f"Error: Kontainer '{name}' sedang berjalan. Hentikan terlebih dahulu."
        container.remove()
        return f"Kontainer '{name}' berhasil dihapus.", ""
    except docker.errors.NotFound:
        return "", f"Error: Kontainer '{name}' tidak ditemukan."
    except docker.errors.APIError as e:
        return "", f"Error Docker API: {e.explanation or str(e)}"
    except Exception as e: return "", f"Error tak terduga: {str(e)}"

def _handle_view_logs(params: dict) -> tuple[str, str]:
    client = get_docker_client()
    if not client: return "", "Error: Tidak dapat terhubung ke Docker daemon."
    name = params.get("name")
    lines_str = params.get("lines", "50")
    if not name: return "", "Error: Nama kontainer dibutuhkan."
    if not re.match(r"^[a-zA-Z0-9_.-]+$", name): return "", "Error: Nama kontainer mengandung karakter tidak valid."
    try:
        lines = int(lines_str)
        if lines <=0: lines = 50
    except ValueError:
        return "", "Error: Jumlah baris harus berupa angka positif."
    try:
        container = client.containers.get(name)
        logs = container.logs(tail=lines).decode('utf-8').strip()
        return logs if logs else "(Tidak ada log untuk ditampilkan)", ""
    except docker.errors.NotFound:
        return "", f"Error: Kontainer '{name}' tidak ditemukan."
    except docker.errors.APIError as e:
        return "", f"Error Docker API: {e.explanation or str(e)}"
    except Exception as e: return "", f"Error tak terduga: {str(e)}"

def _handle_pull_image(params: dict) -> tuple[str, str]:
    client = get_docker_client()
    if not client: return "", "Error: Tidak dapat terhubung ke Docker daemon."
    image_name = params.get("image")
    if not image_name: return "", "Error: Nama image dibutuhkan."
    if not re.match(r"^[a-zA-Z0-9/:_.-]+$", image_name): return "", "Error: Nama image mengandung karakter tidak valid."
    try:
        app.logger.info(f"Menarik image: {image_name}")
        image_obj = client.images.pull(image_name)
        app.logger.info(f"Selesai pull image: {image_name}")
        return f"Image '{image_obj.tags[0] if image_obj.tags else image_name}' berhasil ditarik.", ""
    except docker.errors.APIError as e:
        app.logger.error(f"Docker API Error saat pull image '{image_name}': {e}")
        return "", f"Error Docker API saat pull '{image_name}': {e.explanation or str(e)}"
    except Exception as e:
        app.logger.exception(f"Error tak terduga saat pull image '{image_name}':")
        return "", f"Error tak terduga saat pull '{image_name}': {str(e)}"

def _format_image_list(images):
    if not images:
        return "Tidak ada image."
    output = "REPOSITORY\tTAG\t\tIMAGE ID\tCREATED\t\tSIZE\n"
    output += "-------------------------------------------------------------------------------------------\n"
    for img in images:
        repo_tags = img.tags
        if not repo_tags:
            repo = "<none>"
            tag = "<none>"
        else:
            parts = repo_tags[0].rsplit(':', 1)
            repo = parts[0]
            tag = parts[1] if len(parts) > 1 else "<none>"
        
        created_at = img.attrs['Created'][:19].replace('T', ' ')
        size_mb = round(img.attrs['Size'] / (1024 * 1024), 2)
        output += f"{repo[:25]}\t{tag[:15]}\t{img.short_id[7:]}\t{created_at}\t{size_mb}MB\n"
    return output

def _handle_list_images(params: dict) -> tuple[str, str]:
    client = get_docker_client()
    if not client: return "", "Error: Tidak dapat terhubung ke Docker daemon."
    try:
        images = client.images.list()
        return _format_image_list(images), ""
    except docker.errors.APIError as e:
        return "", f"Error Docker API: {e.explanation or str(e)}"
    except Exception as e: return "", f"Error tak terduga: {str(e)}"


ACTION_HANDLERS = {
    "list_containers": _handle_list_containers,
    "run_container": _handle_run_container,
    "stop_container": _handle_stop_container,
    "remove_container": _handle_remove_container,
    "view_logs": _handle_view_logs,
    "pull_image": _handle_pull_image,
    "list_images": _handle_list_images,
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


@app.route('/')
def index():
    app.logger.info(f"Permintaan ke '/' dari {request.remote_addr}")
    client_status = get_docker_client() 
    if client_status is None and docker_client == "ERROR":
        app.logger.error("Docker client tidak bisa diinisialisasi pada startup.")
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
    get_docker_client() #
    app.logger.info(f"Memulai server Flask pada {SERVER_HOST}:{SERVER_PORT} dengan mode debug: {DEBUG_MODE}")
    app.run(debug=DEBUG_MODE, host=SERVER_HOST, port=SERVER_PORT)