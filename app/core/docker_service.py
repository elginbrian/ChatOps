import docker
import re
import os
import subprocess
from flask import current_app

docker_client = None

def get_docker_client():
    global docker_client
    if docker_client is None:
        try:
            docker_client = docker.from_env(timeout=5)
            docker_client.ping()
            current_app.logger.info("Koneksi Docker SDK berhasil.")
        except docker.errors.DockerException as e:
            current_app.logger.error(f"Gagal terkoneksi ke Docker daemon via SDK: {e}")
            docker_client = "ERROR_CONNECTION"
    return docker_client if docker_client != "ERROR_CONNECTION" else None

def is_self_target(target_name: str) -> bool:
    CHATOP_CONTAINER_NAME = current_app.config.get('CHATOP_CONTAINER_NAME')
    if not CHATOP_CONTAINER_NAME or not target_name:
        return False
    
    client = get_docker_client()
    if not client:
        return False 

    try:
        target_container = client.containers.get(target_name)
        target_id = target_container.id
        target_actual_name = target_container.name
        if target_name == CHATOP_CONTAINER_NAME:
            return True
        
        if target_actual_name == CHATOP_CONTAINER_NAME:
             return True
    
        if target_id == CHATOP_CONTAINER_NAME or target_container.short_id == CHATOP_CONTAINER_NAME:
            return True

    except docker.errors.NotFound:
        return False 
    except Exception as e:
        current_app.logger.error(f"Error saat memeriksa identitas diri kontainer: {e}")
        return False 
    return False

def format_container_list(containers):
    if not containers:
        return "Tidak ada kontainer."
    CHATOP_CONTAINER_NAME = current_app.config.get('CHATOP_CONTAINER_NAME')
    
    header = [
        ("CONTAINER ID", 14), ("IMAGE", 25), ("STATUS", 20), ("PORTS", 25), ("NAMES", 30)
    ]
   
    output = ""
    for name, width in header:
        output += f"{name:<{width}}"
    output += "\n"
    output += "-" * (sum(w for _, w in header)) + "\n"

    for container in containers:
        if CHATOP_CONTAINER_NAME and (container.name == CHATOP_CONTAINER_NAME or container.short_id == CHATOP_CONTAINER_NAME or container.id == CHATOP_CONTAINER_NAME):
            name_display = f"{container.name} (Aplikasi Ini)"
        else:
            name_display = container.name
        
        image_tags = container.image.tags
        image_display = image_tags[0] if image_tags else container.attrs['Config']['Image']
        status = container.status
        ports = container.ports
        ports_str_list = []
        if ports:
            for _internal_port, host_ports_list in ports.items():
                if host_ports_list:
                    for host_port_info in host_ports_list:
                        host_ip = host_port_info.get('HostIp', '0.0.0.0')
                        host_port = host_port_info.get('HostPort', '')
                        if host_ip == '::': host_ip = '[::]'
                        ports_str_list.append(f"{host_ip}:{host_port}->{_internal_port}")
        
        row_data = {
            "CONTAINER ID": container.short_id,
            "IMAGE": image_display,
            "STATUS": status,
            "PORTS": ', '.join(ports_str_list),
            "NAMES": name_display
        }

        for name, width in header:
            val = row_data.get(name, "")
            output += f"{val[:width-1]:<{width}}"
        output += "\n"

    return output.strip()

def list_containers(params: dict) -> tuple[str, str]:
    client = get_docker_client()
    if not client:
        return "", "Error: Tidak dapat terhubung ke Docker daemon."
    try:
        all_containers = params.get("all", False)
        containers = client.containers.list(all=all_containers)
        return format_container_list(containers), ""
    except docker.errors.APIError as e:
        current_app.logger.error(f"Docker API Error saat list containers: {e}")
        return "", f"Error Docker API: {e.explanation or str(e)}"
    except Exception as e:
        current_app.logger.exception("Error tak terduga saat list containers:")
        return "", f"Error tak terduga: {str(e)}"

def run_container(params: dict) -> tuple[str, str]:
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
    
    CHATOP_CONTAINER_NAME = current_app.config.get('CHATOP_CONTAINER_NAME')
    if CHATOP_CONTAINER_NAME and name == CHATOP_CONTAINER_NAME:
        return "", f"Error: Tidak dapat menjalankan kontainer dengan nama yang sama dengan layanan ChatOps ('{CHATOP_CONTAINER_NAME}')."

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
        current_app.logger.info(f"Mencoba menjalankan image '{image}' sebagai kontainer '{name}' dengan port {ports_dict if ports_dict else 'tidak ada'}")
        pulled_image = None
        try:
            client.images.get(image)
        except docker.errors.ImageNotFound:
            current_app.logger.info(f"Image '{image}' tidak ditemukan lokal, mencoba pull...")
            try:
                pulled_image = client.images.pull(image)
                current_app.logger.info(f"Image '{image}' berhasil di-pull.")
            except docker.errors.APIError as pull_error:
                current_app.logger.error(f"Gagal pull image '{image}': {pull_error}")
                return "", f"Error: Gagal pull image '{image}'. {pull_error.explanation or str(pull_error)}"

        container = client.containers.run(image, detach=True, name=name, ports=ports_dict if ports_dict else None)
        pull_msg = f" (Image '{image}' di-pull terlebih dahulu)" if pulled_image else ""
        return f"Kontainer '{container.name}' (ID: {container.short_id}) berhasil dijalankan dari image '{image}'.{pull_msg}", ""
    except docker.errors.ImageNotFound:
        current_app.logger.warning(f"Image '{image}' tidak ditemukan saat mencoba run (setelah cek pull).")
        return "", f"Error: Image '{image}' tidak ditemukan."
    except docker.errors.APIError as e:
        current_app.logger.error(f"Docker API Error saat run container: {e}")
        return "", f"Error Docker API: {e.explanation or str(e)}"
    except Exception as e:
        current_app.logger.exception("Error tak terduga saat run container:")
        return "", f"Error tak terduga: {str(e)}"

def stop_container(params: dict) -> tuple[str, str]:
    client = get_docker_client()
    if not client: return "", "Error: Tidak dapat terhubung ke Docker daemon."
    name = params.get("name")
    if not name: return "", "Error: Nama kontainer dibutuhkan."
    if not re.match(r"^[a-zA-Z0-9_.-]+$", name): return "", "Error: Nama kontainer mengandung karakter tidak valid."
    
    CHATOP_CONTAINER_NAME = current_app.config.get('CHATOP_CONTAINER_NAME')
    if is_self_target(name):
        return "", f"Error: Tidak diizinkan menghentikan kontainer ChatOps ('{CHATOP_CONTAINER_NAME}') sendiri."
    
    try:
        container = client.containers.get(name)
        container.stop(timeout=5)
        return f"Kontainer '{name}' berhasil dihentikan.", ""
    except docker.errors.NotFound:
        return "", f"Error: Kontainer '{name}' tidak ditemukan."
    except docker.errors.APIError as e:
        return "", f"Error Docker API: {e.explanation or str(e)}"
    except Exception as e: return "", f"Error tak terduga: {str(e)}"

def remove_container(params: dict) -> tuple[str, str]:
    client = get_docker_client()
    if not client: return "", "Error: Tidak dapat terhubung ke Docker daemon."
    name = params.get("name")
    if not name: return "", "Error: Nama kontainer dibutuhkan."
    if not re.match(r"^[a-zA-Z0-9_.-]+$", name): return "", "Error: Nama kontainer mengandung karakter tidak valid."

    CHATOP_CONTAINER_NAME = current_app.config.get('CHATOP_CONTAINER_NAME')
    if is_self_target(name):
        return "", f"Error: Tidak diizinkan menghapus kontainer ChatOps ('{CHATOP_CONTAINER_NAME}') sendiri."

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

def view_logs(params: dict) -> tuple[str, str]:
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
        logs = container.logs(tail=lines, timestamps=True).decode('utf-8').strip()
        return logs if logs else "(Tidak ada log untuk ditampilkan)", ""
    except docker.errors.NotFound:
        return "", f"Error: Kontainer '{name}' tidak ditemukan."
    except docker.errors.APIError as e:
        return "", f"Error Docker API: {e.explanation or str(e)}"
    except Exception as e: return "", f"Error tak terduga: {str(e)}"

def view_stats(params: dict) -> tuple[str, str]:
    client = get_docker_client()
    if not client:
        return "", "Error: Tidak dapat terhubung ke Docker daemon."
    name = params.get("name")
    if not name: return "", "Error: Nama kontainer dibutuhkan."
    try:
        container = client.containers.get(name)
        if container.status != "running":
            return "", f"Error: Kontainer '{name}' tidak sedang berjalan."
        stats = container.stats(stream=False)
        cpu_usage = stats['cpu_stats']['cpu_usage']['total_usage']
        system_cpu_usage = stats['cpu_stats']['system_cpu_usage']
        mem_usage = stats['memory_stats']['usage'] / (1024*1024)
        mem_limit = stats['memory_stats']['limit'] / (1024*1024)
        cpu_delta = cpu_usage - stats.get('precpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0)
        system_delta = system_cpu_usage - stats.get('precpu_stats', {}).get('system_cpu_usage', 0)
        
        cpu_percent = 0.0
        if system_delta > 0.0 and cpu_delta > 0.0:
            cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage'] or [1]) * 100.0

        output = (
            f"Statistik untuk Kontainer: {container.name}\n"
            f"---------------------------------\n"
            f"CPU Usage: {cpu_percent:.2f}%\n"
            f"Memory Usage: {mem_usage:.2f} MB / {mem_limit:.2f} MB"
        )
        return output, ""
    except docker.errors.NotFound:
        return "", f"Error: Kontainer '{name}' tidak ditemukan."
    except Exception as e:
        current_app.logger.error(f"Error saat mengambil statistik: {e}")
        return "", f"Error tak terduga: {str(e)}"


def pull_image(params: dict) -> tuple[str, str]:
    client = get_docker_client()
    if not client: return "", "Error: Tidak dapat terhubung ke Docker daemon."
    image_name = params.get("image")
    if not image_name: return "", "Error: Nama image dibutuhkan."
    if not re.match(r"^[a-zA-Z0-9/:_.-]+$", image_name): return "", "Error: Nama image mengandung karakter tidak valid."
    try:
        current_app.logger.info(f"Menarik image: {image_name}")
        image_obj = client.images.pull(image_name)
        current_app.logger.info(f"Selesai pull image: {image_name}")
        return f"Image '{image_obj.tags[0] if image_obj.tags else image_name}' berhasil ditarik.", ""
    except docker.errors.APIError as e:
        current_app.logger.error(f"Docker API Error saat pull image '{image_name}': {e}")
        return "", f"Error Docker API saat pull '{image_name}': {e.explanation or str(e)}"
    except Exception as e:
        current_app.logger.exception(f"Error tak terduga saat pull image '{image_name}':")
        return "", f"Error tak terduga saat pull '{image_name}': {str(e)}"

def format_image_list(images):
    if not images:
        return "Tidak ada image."
    header = [
        ("REPOSITORY", 30), ("TAG", 20), ("IMAGE ID", 15), ("CREATED", 25), ("SIZE (MB)", 10)
    ]
    output = ""
    for name, width in header:
        output += f"{name:<{width}}"
    output += "\n"
    output += "-" * (sum(w for _, w in header)) + "\n"

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
        
        row_data = {
            "REPOSITORY": repo,
            "TAG": tag,
            "IMAGE ID": img.short_id[7:],
            "CREATED": created_at,
            "SIZE (MB)": str(size_mb)
        }
        for name, width in header:
            val = row_data.get(name, "")
            output += f"{val[:width-1]:<{width}}"
        output += "\n"
        
    return output.strip()

def list_images(params: dict) -> tuple[str, str]:
    client = get_docker_client()
    if not client: return "", "Error: Tidak dapat terhubung ke Docker daemon."
    try:
        images = client.images.list()
        return format_image_list(images), ""
    except docker.errors.APIError as e:
        return "", f"Error Docker API: {e.explanation or str(e)}"
    except Exception as e: return "", f"Error tak terduga: {str(e)}"

def _run_compose_command(command: list) -> tuple[str, str]:
    compose_file_path = os.path.join(current_app.root_path, '..', 'docker-compose.yml')
    if not os.path.exists(compose_file_path):
        return "", "Error: docker-compose.yml tidak ditemukan di root proyek."
    
    cmd_list = ['docker-compose', '-f', compose_file_path] + command
    
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True, check=True, timeout=120)
        output = result.stdout.strip() if result.stdout else "(no standard output)"
        error_output = result.stderr.strip() if result.stderr else "(no standard error)"
        return f"Output:\n{output}\n\nLogs/Errors:\n{error_output}", ""
    except subprocess.CalledProcessError as e:
        return "", f"Error saat menjalankan docker-compose:\n{e.stderr}"
    except Exception as e:
        return "", f"Error tak terduga: {str(e)}"

def compose_up(params: dict) -> tuple[str, str]:
    service = params.get('service')
    command = ['up', '-d']
    if service:
        if not re.match(r"^[a-zA-Z0-9_.-]+$", service):
            return "", "Error: Nama service tidak valid."
        command.append(service)
    return _run_compose_command(command)

def compose_down(params: dict) -> tuple[str, str]:
    return _run_compose_command(['down'])