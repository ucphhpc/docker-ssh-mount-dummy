import pytest
import socket
import docker
import random
from paramiko import SSHClient
from paramiko.client import AutoAddPolicy
from paramiko.ssh_exception import (
    BadHostKeyException,
    AuthenticationException,
    SSHException,
)
from os.path import dirname, realpath
from helpers import wait_for_container_output, wait_for_session, remove_container

IMAGE_NAME = "ssh-mount-dummy"
IMAGE_TAG = "edge"
IMAGE = "".join([IMAGE_NAME, ":", IMAGE_TAG])
NETWORK_NAME = "ssh_test"

# paths
root_path = dirname(dirname(realpath(__file__)))
sock_path = "/var/run/docker.sock"
dockerfile_path = "{}/{}/{}".format(
    root_path, IMAGE_NAME, "Dockerfile.{}".format(IMAGE_TAG)
)

# image_build
docker_img = {
    "path": root_path,
    "dockerfile": dockerfile_path,
    "tag": IMAGE,
    "rm": True,
    "pull": False,
}

# containers
random_ssh_port = random.randint(2200, 2299)
ssh_dummy_cont = {"image": IMAGE, "detach": True, "ports": {22: random_ssh_port}}


# launch underlying stack for the test
@pytest.mark.parametrize("image", [docker_img], indirect=["image"])
@pytest.mark.parametrize(
    "network", [{"name": NETWORK_NAME, "driver": "bridge"}], indirect=["network"]
)
def test_ssh_mount(image, network, make_container):
    client = docker.from_env()
    ssh = SSHClient()
    container = make_container(ssh_dummy_cont)
    assert container
    assert container.status == "running"
    assert wait_for_container_output(container.id, "Running the OpenSSH Server")

    # volume
    target_user = "mountuser"
    password = "Passw0rd!"
    ssh_host_target = "127.0.0.1"
    ssh.set_missing_host_key_policy(AutoAddPolicy)
    try:
        assert wait_for_session(ssh_host_target, random_ssh_port, max_attempts=10)
        ssh.connect(
            ssh_host_target,
            port=random_ssh_port,
            username=target_user,
            password=password,
        )
    except (
        BadHostKeyException,
        AuthenticationException,
        SSHException,
        socket.error,
    ) as error:
        print("Error: {}".format(error))
        assert False
    finally:
        assert remove_container(container.id)

    client.volumes.prune()
