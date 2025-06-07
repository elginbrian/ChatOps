import docker
from flask import current_app
from .docker_client import get_docker_client
import json

def list_volumes(params: dict) -> tuple[list, str]:
    client = get_docker_client()
    if not client:
        return None, "Error: Tidak dapat terhubung ke Docker daemon."
    try:
        volumes = client.volumes.list()
        volume_list = []
        for vol in volumes:
            volume_list.append({
                "name": vol.name,
                "driver": vol.driver,
                "created_at": vol.attrs.get('CreatedAt', '-')[:19].replace('T', ' ')
            })
        return volume_list, ""
    except docker.errors.APIError as e:
        return None, f"Error Docker API: {e.explanation or str(e)}"
    except Exception as e:
        return None, f"Error tak terduga: {str(e)}"

def remove_volume(params: dict) -> tuple[dict, str]:
    client = get_docker_client()
    if not client:
        return None, "Error: Tidak dapat terhubung ke Docker daemon."
    name = params.get("name")
    if not name:
        return None, "Error: Nama volume dibutuhkan."
    try:
        volume = client.volumes.get(name)
        volume.remove()
        output = {
            "action": "Remove",
            "status": "Berhasil Dihapus",
            "resource_type": "Volume",
            "resource_name": name
        }
        return output, ""
    except docker.errors.NotFound:
        return None, f"Error: Volume '{name}' tidak ditemukan."
    except docker.errors.APIError as e:
        if "in use by" in str(e):
             return None, f"Error: Volume '{name}' sedang digunakan oleh sebuah kontainer."
        return None, f"Error Docker API: {e.explanation or str(e)}"
    except Exception as e:
        return None, f"Error tak terduga: {str(e)}"

def inspect_volume(params: dict) -> tuple[str, str]:
    client = get_docker_client()
    if not client:
        return None, "Error: Tidak dapat terhubung ke Docker daemon."
    name = params.get("name")
    if not name:
        return None, "Error: Nama volume dibutuhkan."
    try:
        volume = client.volumes.get(name)
        formatted_json = json.dumps(volume.attrs, indent=2)
        return formatted_json, ""
    except docker.errors.NotFound:
        return None, f"Error: Volume '{name}' tidak ditemukan."
    except Exception as e:
        return None, f"Error tak terduga: {str(e)}"