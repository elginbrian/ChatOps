import docker
import re
from flask import current_app
from .docker_client import get_docker_client
import json

def is_self_target(target_name: str) -> bool: #
    CHATOP_CONTAINER_NAME = current_app.config.get('CHATOP_CONTAINER_NAME') #
    if not CHATOP_CONTAINER_NAME or not target_name: #
        return False #
    
    client = get_docker_client() #
    if not client: #
        return False #

    try:
        target_container = client.containers.get(target_name) #
        target_id = target_container.id #
        target_actual_name = target_container.name #
        if target_name == CHATOP_CONTAINER_NAME: #
            return True #
        
        if target_actual_name == CHATOP_CONTAINER_NAME: #
             return True #
    
        if target_id == CHATOP_CONTAINER_NAME or target_container.short_id == CHATOP_CONTAINER_NAME: #
            return True #

    except docker.errors.NotFound: #
        return False #
    except Exception as e: #
        current_app.logger.error(f"Error saat memeriksa identitas diri kontainer: {e}") #
        return False #
    return False #

def list_containers(params: dict) -> tuple[list, str]: #
    client = get_docker_client() #
    if not client: #
        return None, "Error: Tidak dapat terhubung ke Docker daemon." #
    try:
        all_containers = params.get("all", False) #
        containers = client.containers.list(all=all_containers) #
        
        container_list = [] #
        CHATOP_CONTAINER_NAME = current_app.config.get('CHATOP_CONTAINER_NAME') #

        for container in containers: #
            is_self = CHATOP_CONTAINER_NAME and (container.name == CHATOP_CONTAINER_NAME or container.short_id == CHATOP_CONTAINER_NAME or container.id == CHATOP_CONTAINER_NAME) #
            
            image_tags = container.image.tags #
            image_display = image_tags[0] if image_tags else container.attrs['Config']['Image'] #
            
            ports_str_list = [] #
            if container.ports: #
                for _internal_port, host_ports_list in container.ports.items(): #
                    if host_ports_list: #
                        for host_port_info in host_ports_list: #
                            host_ip = host_port_info.get('HostIp', '0.0.0.0') #
                            host_port = host_port_info.get('HostPort', '') #
                            if host_ip == '::': host_ip = '[::]' #
                            ports_str_list.append(f"{host_ip}:{host_port}->{_internal_port}") #

            container_list.append({ #
                "id": container.short_id, #
                "name": container.name, #
                "image": image_display, #
                "status": container.status, #
                "ports": ', '.join(ports_str_list), #
                "is_self": is_self #
            })
            
        return container_list, "" #
    except docker.errors.APIError as e: #
        current_app.logger.error(f"Docker API Error saat list containers: {e}") #
        return None, f"Error Docker API: {e.explanation or str(e)}" #
    except Exception as e: #
        current_app.logger.exception("Error tak terduga saat list containers:") #
        return None, f"Error tak terduga: {str(e)}" #

def run_container(params: dict) -> tuple[dict, str]: #
    client = get_docker_client() #
    if not client: #
        return None, "Error: Tidak dapat terhubung ke Docker daemon." #

    name = params.get("name") #
    image = params.get("image") #
    ports_str = params.get("ports") #

    if not name or not image: #
        return None, "Error: Nama kontainer dan nama image dibutuhkan." #
    if not re.match(r"^[a-zA-Z0-9_.-]+$", name) or \
       not re.match(r"^[a-zA-Z0-9/:_.-]+$", image): #
        return None, "Error: Nama kontainer/image mengandung karakter tidak valid." #
    
    CHATOP_CONTAINER_NAME = current_app.config.get('CHATOP_CONTAINER_NAME') #
    if CHATOP_CONTAINER_NAME and name == CHATOP_CONTAINER_NAME: #
        return None, f"Error: Tidak dapat menjalankan kontainer dengan nama yang sama dengan layanan ChatOps ('{CHATOP_CONTAINER_NAME}')." #

    ports_dict = {} #
    if ports_str: #
        if not re.match(r"^\d{1,5}:\d{1,5}(?:,\d{1,5}:\d{1,5})*$", ports_str): #
             return None, "Error: Format port tidak valid. Gunakan HOST:CONTAINER atau HOST:CONTAINER,HOST2:CONTAINER2" #
        try:
            for p_map_str in ports_str.split(','): #
                host_port, container_port = p_map_str.strip().split(':') #
                ports_dict[f"{container_port.strip()}/tcp"] = int(host_port.strip()) #
        except ValueError: #
            return None, "Error: Format port tidak valid (pastikan angka)." #

    try:
        current_app.logger.info(f"Mencoba menjalankan image '{image}' sebagai kontainer '{name}' dengan port {ports_dict if ports_dict else 'tidak ada'}") #
        pulled_image = False #
        try:
            client.images.get(image) #
        except docker.errors.ImageNotFound: #
            current_app.logger.info(f"Image '{image}' tidak ditemukan lokal, mencoba pull...") #
            try:
                client.images.pull(image) #
                pulled_image = True #
                current_app.logger.info(f"Image '{image}' berhasil di-pull.") #
            except docker.errors.APIError as pull_error: #
                current_app.logger.error(f"Gagal pull image '{image}': {pull_error}") #
                return None, f"Error: Gagal pull image '{image}'. {pull_error.explanation or str(pull_error)}" #

        container = client.containers.run(image, detach=True, name=name, ports=ports_dict if ports_dict else None) #
        
        output = { #
            "action": "Run", #
            "status": "Berhasil Dijalankan", #
            "resource_type": "Kontainer", #
            "resource_name": container.name, #
            "details": [ #
                {"key": "ID", "value": container.short_id}, #
                {"key": "Image", "value": image} #
            ]
        }
        if pulled_image: #
            output["details"].append({"key": "Info", "value": "Image di-pull terlebih dahulu"}) #
            
        return output, "" #
    except docker.errors.ImageNotFound: #
        current_app.logger.warning(f"Image '{image}' tidak ditemukan saat mencoba run (setelah cek pull).") #
        return None, f"Error: Image '{image}' tidak ditemukan." #
    except docker.errors.APIError as e: #
        current_app.logger.error(f"Docker API Error saat run container: {e}") #
        return None, f"Error Docker API: {e.explanation or str(e)}" #
    except Exception as e: #
        current_app.logger.exception("Error tak terduga saat run container:") #
        return None, f"Error tak terduga: {str(e)}" #
    
def start_container(params: dict) -> tuple[dict, str]: #
    client = get_docker_client() #
    if not client: #
        return None, "Error: Tidak dapat terhubung ke Docker daemon." #
        
    name = params.get("name") #
    if not name: #
        return None, "Error: Nama kontainer dibutuhkan." #
    if not re.match(r"^[a-zA-Z0-9_.-]+$", name): #
        return None, "Error: Nama kontainer mengandung karakter tidak valid." #

    try:
        container = client.containers.get(name) #
        if container.status == "running": #
            return None, f"Error: Kontainer '{name}' sudah dalam keadaan berjalan." #
            
        container.start() #
        
        output = { #
            "action": "Start", #
            "status": "Berhasil Dihidupkan", #
            "resource_type": "Kontainer", #
            "resource_name": container.name #
        }
        return output, "" #
        
    except docker.errors.NotFound: #
        return None, f"Error: Kontainer '{name}' tidak ditemukan." #
    except docker.errors.APIError as e: #
        current_app.logger.error(f"Docker API Error saat start container: {e}") #
        return None, f"Error Docker API: {e.explanation or str(e)}" #
    except Exception as e: #
        current_app.logger.exception("Error tak terduga saat start container:") #
        return None, f"Error tak terduga: {str(e)}" #

def stop_container(params: dict) -> tuple[dict, str]: #
    client = get_docker_client() #
    if not client: return None, "Error: Tidak dapat terhubung ke Docker daemon." #
    name = params.get("name") #
    if not name: return None, "Error: Nama kontainer dibutuhkan." #
    if not re.match(r"^[a-zA-Z0-9_.-]+$", name): return None, "Error: Nama kontainer mengandung karakter tidak valid." #
    
    if is_self_target(name): #
        return None, f"Error: Tidak diizinkan menghentikan kontainer ChatOps sendiri." #
    
    try:
        container = client.containers.get(name) #
        container.stop(timeout=5) #
        output = { #
            "action": "Stop", #
            "status": "Berhasil Dihentikan", #
            "resource_type": "Kontainer", #
            "resource_name": name #
        }
        return output, "" #
    except docker.errors.NotFound: #
        return None, f"Error: Kontainer '{name}' tidak ditemukan." #
    except docker.errors.APIError as e: #
        return None, f"Error Docker API: {e.explanation or str(e)}" #
    except Exception as e: return None, f"Error tak terduga: {str(e)}" #

def remove_container(params: dict) -> tuple[dict, str]: #
    client = get_docker_client() #
    if not client: return None, "Error: Tidak dapat terhubung ke Docker daemon." #
    name = params.get("name") #
    if not name: return None, "Error: Nama kontainer dibutuhkan." #
    if not re.match(r"^[a-zA-Z0-9_.-]+$", name): return None, "Error: Nama kontainer mengandung karakter tidak valid." #

    if is_self_target(name): #
        return None, f"Error: Tidak diizinkan menghapus kontainer ChatOps sendiri." #

    try:
        container = client.containers.get(name) #
        if container.status == "running": #
            return None, f"Error: Kontainer '{name}' sedang berjalan. Hentikan terlebih dahulu." #
        container.remove() #
        output = { #
            "action": "Remove", #
            "status": "Berhasil Dihapus", #
            "resource_type": "Kontainer", #
            "resource_name": name #
        }
        return output, "" #
    except docker.errors.NotFound: #
        return None, f"Error: Kontainer '{name}' tidak ditemukan." #
    except docker.errors.APIError as e: #
        return None, f"Error Docker API: {e.explanation or str(e)}" #
    except Exception as e: return None, f"Error tak terduga: {str(e)}" #

def view_logs(params: dict) -> tuple[list, str]: #
    client = get_docker_client() #
    if not client: return [], "Error: Tidak dapat terhubung ke Docker daemon." #
    name = params.get("name") #
    lines_str = params.get("lines") or "50" #
    if not name: return [], "Error: Nama kontainer dibutuhkan." #
    if not re.match(r"^[a-zA-Z0-9_.-]+$", name): return [], "Error: Nama kontainer mengandung karakter tidak valid." #
    
    try:
        lines = int(lines_str) #
        if lines <=0: lines = 50 #
    except ValueError: #
        return [], "Error: Jumlah baris harus berupa angka positif." #
    try:
        container = client.containers.get(name) #
        logs_raw = container.logs(tail=lines, timestamps=True).decode('utf-8').strip() #
        if not logs_raw: #
            return [], "" #

        log_list = [] #
        for line in logs_raw.split('\n'): #
            if 'Z ' in line: #
                parts = line.split('Z ', 1) #
                timestamp = parts[0] + 'Z' #
                entry = parts[1] #
                log_list.append({"timestamp": timestamp, "log_entry": entry}) #
            else: #
                log_list.append({"timestamp": "-", "log_entry": line}) #
        return log_list, "" #
    except docker.errors.NotFound: #
        return [], f"Error: Kontainer '{name}' tidak ditemukan." #
    except docker.errors.APIError as e: #
        return [], f"Error Docker API: {e.explanation or str(e)}" #
    except Exception as e: return [], f"Error tak terduga: {str(e)}" #

def view_stats(params: dict) -> tuple[list, str]: #
    client = get_docker_client() #
    if not client: #
        return [], "Error: Tidak dapat terhubung ke Docker daemon." #
    name = params.get("name") #
    if not name: return [], "Error: Nama kontainer dibutuhkan." #
    try:
        container = client.containers.get(name) #
        if container.status != "running": #
            return [], f"Error: Kontainer '{name}' tidak sedang berjalan." #
        stats = container.stats(stream=False) #
        cpu_usage = stats['cpu_stats']['cpu_usage']['total_usage'] #
        system_cpu_usage = stats['cpu_stats']['system_cpu_usage'] #
        mem_usage = stats['memory_stats']['usage'] / (1024*1024) #
        mem_limit = stats['memory_stats']['limit'] / (1024*1024) #
        cpu_delta = cpu_usage - stats.get('precpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0) #
        system_delta = system_cpu_usage - stats.get('precpu_stats', {}).get('system_cpu_usage', 0) #
        
        cpu_percent = 0.0 #
        if system_delta > 0.0 and cpu_delta > 0.0: #
            number_cpus = stats.get('cpu_stats', {}).get('online_cpus') #
            if number_cpus is None: #
                per_cpu_usage_list = stats.get('cpu_stats', {}).get('cpu_usage', {}).get('percpu_usage') #
                if per_cpu_usage_list: #
                    number_cpus = len(per_cpu_usage_list) #
                else: #
                    number_cpus = 1 #
            
            cpu_percent = (cpu_delta / system_delta) * number_cpus * 100.0 #

        stats_data = [{ #
            "container_name": container.name, #
            "cpu_usage": f"{cpu_percent:.2f}%", #
            "mem_usage": f"{mem_usage:.2f} MB / {mem_limit:.2f} MB" #
        }]
        return stats_data, "" #
    except docker.errors.NotFound: #
        return [], f"Error: Kontainer '{name}' tidak ditemukan." #
    except Exception as e: #
        current_app.logger.error(f"Error saat mengambil statistik: {e}") #
        return [], f"Error tak terduga: {str(e)}" #
    
def inspect_container(params: dict) -> tuple[str, str]:
    client = get_docker_client()
    if not client:
        return None, "Error: Tidak dapat terhubung ke Docker daemon."
    name = params.get("name")
    if not name:
        return None, "Error: Nama kontainer dibutuhkan."
    try:
        container = client.containers.get(name)
        formatted_json = json.dumps(container.attrs, indent=2)
        return formatted_json, ""
    except docker.errors.NotFound:
        return None, f"Error: Kontainer '{name}' tidak ditemukan."
    except Exception as e:
        return None, f"Error tak terduga: {str(e)}"