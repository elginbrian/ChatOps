import docker
from flask import current_app
from .docker_client import get_docker_client

def prune_system(params: dict) -> tuple[dict, str]:
    client = get_docker_client()
    if not client:
        return None, "Error: Tidak dapat terhubung ke Docker daemon."
    try:
        containers_pruned = client.containers.prune()
        reclaimed_containers = containers_pruned.get('SpaceReclaimed', 0)

        images_pruned = client.images.prune(filters={'dangling': False})
        reclaimed_images = images_pruned.get('SpaceReclaimed', 0)

        volumes_pruned = client.volumes.prune()
        reclaimed_volumes = volumes_pruned.get('SpaceReclaimed', 0)

        networks_pruned = client.networks.prune()

        total_reclaimed = (reclaimed_containers + reclaimed_images + reclaimed_volumes) / (1024 * 1024)

        details = [
            {"key": "Kontainer Dihapus", "value": str(len(containers_pruned.get('ContainersDeleted', [])))},
            {"key": "Image Dihapus", "value": str(len(images_pruned.get('ImagesDeleted', [])))},
            {"key": "Volume Dihapus", "value": str(len(volumes_pruned.get('VolumesDeleted', [])))},
            {"key": "Total Ruang Dihemat", "value": f"{total_reclaimed:.2f} MB"}
        ]

        output = {
            "action": "Prune",
            "status": "Sistem Berhasil Dibersihkan",
            "resource_type": "Sistem Docker",
            "resource_name": "Global",
            "details": details
        }
        return output, ""
    except docker.errors.APIError as e:
        return None, f"Error Docker API saat prune: {e.explanation or str(e)}"
    except Exception as e:
        return None, f"Error tak terduga saat prune: {str(e)}"
    
def system_info(params: dict) -> tuple[str, str]:
    client = get_docker_client()
    if not client:
        return None, "Error: Tidak dapat terhubung ke Docker daemon."
    try:
        info = client.info()
        formatted_json = json.dumps(info, indent=2, default=str)
        return formatted_json, ""
    except Exception as e:
        return None, f"Error tak terduga saat mengambil info sistem: {str(e)}"

def system_version(params: dict) -> tuple[str, str]:
    client = get_docker_client()
    if not client:
        return None, "Error: Tidak dapat terhubung ke Docker daemon."
    try:
        version_info = client.version()
        formatted_json = json.dumps(version_info, indent=2)
        return formatted_json, ""
    except Exception as e:
        return None, f"Error tak terduga saat mengambil versi sistem: {str(e)}"