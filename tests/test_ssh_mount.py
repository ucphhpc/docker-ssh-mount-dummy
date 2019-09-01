import pytest
import socket
import docker
from paramiko import SSHClient
from paramiko.client import AutoAddPolicy
from paramiko.ssh_exception import BadHostKeyException, AuthenticationException, \
    SSHException
from os.path import dirname, realpath

IMAGE_NAME = "ssh-mount-dummy"
IMAGE_TAG = "test"
IMAGE = ''.join([IMAGE_NAME, ":", IMAGE_TAG])
NETWORK_NAME = "ssh_test"

# paths
docker_path = dirname(dirname(realpath(__file__)))
sock_path = '/var/run/docker.sock'

# image_build
docker_img = {'path': docker_path, 'tag': IMAGE, 'rm': True, 'pull': False}

# containers
host = socket.gethostname()
ssh_dummy_cont = {'image': IMAGE, 'detach': True, 'ports': {22: 2222}}


# launch underlying stack for the test
@pytest.mark.parametrize('image', [docker_img], indirect=['image'])
@pytest.mark.parametrize('network', [{'name': NETWORK_NAME, 'driver': 'bridge'}],
                         indirect=['network'])
def test_ssh_mount(image, network, make_container):
    client = docker.from_env()
    ssh = SSHClient()
    make_container(ssh_dummy_cont)
    # volume
    target_user = 'mountuser'
    password = 'Passw0rd!'
    ssh_host_target = '127.0.0.1'
    ssh.set_missing_host_key_policy(AutoAddPolicy)
    try:
        ssh.connect(ssh_host_target, port=2222, username=target_user,
                    password=password)
    except (BadHostKeyException, AuthenticationException,
            SSHException, socket.error) as error:
        print("Error: {}".format(error))
        assert False

    client.volumes.prune()
