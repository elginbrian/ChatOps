import docker
from flask import current_app
from .docker_client import get_docker_client
import json

def list_networks(params: dict) -> tuple[list, str]:
    client = get_docker_client()
    if not client:
        return None, "Error: Tidak dapat terhubung ke Docker daemon."
    try:
        networks = client.networks.list()
        network_list = []
        for net in networks:
            network_list.append({
                "id": net.short_id,
                "name": net.name,
                "driver": net.attrs.get('Driver', 'n/a'), 
                "scope": net.attrs.get('Scope', 'local'),
            })
        return network_list, ""
    except docker.errors.APIError as e:
        return None, f"Error Docker API: {e.explanation or str(e)}"
    except Exception as e:
        current_app.logger.exception("Error di list_networks:")
        return None, f"Error tak terduga: {str(e)}"

def inspect_network(params: dict) -> tuple[str, str]:
    client = get_docker_client()
    if not client:
        return None, "Error: Tidak dapat terhubung ke Docker daemon."
    name = params.get("name")
    if not name:
        return None, "Error: Nama network dibutuhkan."
    try:
        network = client.networks.get(name)
        formatted_json = json.dumps(network.attrs, indent=2)
        return formatted_json, ""
    except docker.errors.NotFound:
        return None, f"Error: Network '{name}' tidak ditemukan."
    except Exception as e:
        return None, f"Error tak terduga: {str(e)}"