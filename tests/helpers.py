import docker
import socket
import time


def wait_for_container_output(container_id, output, wait_seconds=30):
    client = docker.from_env()
    container = client.containers.get(container_id)
    attempt = 0
    while True:
        logs = container.logs()
        if output in logs.decode():
            return True
        attempt += 1
        if attempt >= wait_seconds:
            break
        time.sleep(1)
    return False


def remove_container(container_id, max_attempts=10):
    client = docker.from_env()
    container = client.containers.get(container_id)
    container.stop()
    container.wait()
    container.remove()
    attempt = 0
    while True:
        try:
            client.containers.get(container_id)
            attempt += 1
            if attempt >= max_attempts:
                break
            time.sleep(1)
        except docker.errors.NotFound:
            return True
    return False


def check_socket(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex((host, port))
            return result == 0
    except socket.error as err:
        print("Failed to open socket: {}".format(err))
        return False
    return False


def wait_for_session(host, port, max_attempts=10):
    attempt = 0
    while attempt <= max_attempts:
        socket_result = check_socket(host, port)
        if not socket_result:
            attempt += 1
            time.sleep(1)
            continue
        return True
    return False
