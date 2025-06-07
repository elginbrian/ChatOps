import docker
import re
from flask import current_app
from .docker_client import get_docker_client

def pull_image(params: dict) -> tuple[dict, str]: #
    client = get_docker_client() #
    if not client: return None, "Error: Tidak dapat terhubung ke Docker daemon." #
    image_name = params.get("image") #
    if not image_name: return None, "Error: Nama image dibutuhkan." #
    if not re.match(r"^[a-zA-Z0-9/:_.-]+$", image_name): return None, "Error: Nama image mengandung karakter tidak valid." #
    try:
        current_app.logger.info(f"Menarik image: {image_name}") #
        image_obj = client.images.pull(image_name) #
        current_app.logger.info(f"Selesai pull image: {image_name}") #
        output = { #
            "action": "Pull", #
            "status": "Berhasil Ditarik", #
            "resource_type": "Image", #
            "resource_name": image_obj.tags[0] if image_obj.tags else image_name #
        }
        return output, "" #
    except docker.errors.APIError as e: #
        current_app.logger.error(f"Docker API Error saat pull image '{image_name}': {e}") #
        return None, f"Error Docker API saat pull '{image_name}': {e.explanation or str(e)}" #
    except Exception as e: #
        current_app.logger.exception(f"Error tak terduga saat pull image '{image_name}':") #
        return None, f"Error tak terduga saat pull '{image_name}': {str(e)}" #

def list_images(params: dict) -> tuple[list, str]: #
    client = get_docker_client() #
    if not client: return None, "Error: Tidak dapat terhubung ke Docker daemon." #
    try:
        images = client.images.list() #
        image_list = [] #
        for img in images: #
            repo_tags = img.tags #
            if not repo_tags: #
                repo = "<none>" #
                tag = "<none>" #
            else: #
                parts = repo_tags[0].rsplit(':', 1) #
                repo = parts[0] #
                tag = parts[1] if len(parts) > 1 else "<none>" #

            image_list.append({ #
                "id": img.short_id[7:19], #
                "repository": repo, #
                "tag": tag, #
                "created": img.attrs['Created'][:19].replace('T', ' '), #
                "size": round(img.attrs['Size'] / (1024 * 1024), 2) #
            })
        return image_list, "" 
    except docker.errors.APIError as e: 
        return None, f"Error Docker API: {e.explanation or str(e)}" 
    except Exception as e: return None, f"Error tak terduga: {str(e)}" 