import docker
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