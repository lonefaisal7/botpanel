import docker, logging

log = logging.getLogger(__name__)
client = docker.from_env()


def build_image(bot_id: str, bot_dir: str) -> str:
    tag = f"botpanel-{bot_id}:latest"
    client.images.build(path=bot_dir, tag=tag, rm=True, forcerm=True)
    return tag


def run_container(bot_id: str, image_tag: str) -> str:
    name = f"bot-{bot_id[:8]}"
    # Remove any stale container with the same name
    try:
        old = client.containers.get(name)
        old.remove(force=True)
    except docker.errors.NotFound:
        pass

    container = client.containers.run(
        image_tag,
        detach=True,
        name=name,
        restart_policy={"Name": "unless-stopped"},
        network_mode="bridge",
    )
    return container.id


def stop_container(container_id: str) -> bool:
    try:
        c = client.containers.get(container_id)
        c.stop(timeout=10)
        return True
    except docker.errors.NotFound:
        return False


def start_container(container_id: str) -> bool:
    try:
        c = client.containers.get(container_id)
        c.start()
        return True
    except docker.errors.NotFound:
        return False


def restart_container(container_id: str) -> bool:
    try:
        c = client.containers.get(container_id)
        c.restart(timeout=10)
        return True
    except docker.errors.NotFound:
        return False


def remove_container(container_id: str):
    try:
        c = client.containers.get(container_id)
        c.stop(timeout=5)
        c.remove(force=True)
    except docker.errors.NotFound:
        pass


def remove_image(bot_id: str):
    try:
        client.images.remove(f"botpanel-{bot_id}:latest", force=True)
    except (docker.errors.ImageNotFound, docker.errors.APIError):
        pass


def get_logs(container_id: str, tail: int = 150) -> str:
    try:
        c = client.containers.get(container_id)
        return c.logs(tail=tail, timestamps=True).decode("utf-8", errors="replace")
    except docker.errors.NotFound:
        return "⚠️  Container not found."


def get_status(container_id: str) -> str:
    try:
        c = client.containers.get(container_id)
        c.reload()
        return c.status          # running | exited | created …
    except docker.errors.NotFound:
        return "not_found"
