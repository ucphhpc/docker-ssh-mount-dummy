import os
import pytest
import time
import socket
import requests
import docker
from os.path import join, dirname, realpath
from docker.types import Mount

IMAGE_NAME = "jupyter-mount-dummy"
IMAGE_TAG = "test"
IMAGE = ''.join([IMAGE_NAME, ":", IMAGE_TAG])
NETWORK_NAME = "jh_test"

# paths
docker_path = dirname(os.getcwd())
config_path = join(dirname(realpath(__file__)), 'jupyterhub_config.py')
sock_path = '/var/run/docker.sock'

# image_build
docker_img = {'path': docker_path, 'tag': IMAGE, 'rm': True, 'pull': True}

# containers
jhub_cont = {'image': 'nielsbohr/jupyterhub:devel', 'name': 'jupyterhub',
             'mounts': [Mount(source=sock_path,
                              target=sock_path,
                              read_only=False,
                              type='bind'),
                        Mount(source=config_path,
                              target='/etc/jupyterhub/jupyterhub_config.py',
                              read_only=True,
                              type='bind')],
             'network': NETWORK_NAME,
             'ports': {8000: 8000},
             'detach': True, 'command': ['jupyterhub', '-f',
                                         '/etc/jupyterhub/jupyterhub_config.py']}

host = socket.gethostname()
dummy_cont = {'image': IMAGE, 'detach': True, 'ports': {22: 2222}}


# launch underlying stack for the test
@pytest.mark.parametrize('image', [docker_img], indirect=['image'])
@pytest.mark.parametrize('network', [{'name': NETWORK_NAME, 'driver': 'bridge',
                                      'options': {'subnet': '192.168.0.0/20'},
                                      'attachable': True}], indirect=['network'])
def test_jupyter_mount(image, network, make_containers):
    client = docker.from_env()
    jhub, dummy = make_containers([jhub_cont, dummy_cont])
    hub_url = 'http://127.0.0.1:8000'
    auth_url = '/hub/auth'
    spawn_url = '/hub/spawn'
    mount_url = '/hub/mount'
    #private_key = container.exec_run('cat /home/mountuser/.ssh/id_rsa')[1]

    # volume
    target_user = 'mountuser'
    ssh_host_target = ''
    private_key = ''
    sshcmd = ''.join([target_user, '@', ssh_host_target, ':'])

    sshfs_volume = {'name': 'testvolume', 'driver': 'rasmunk/sshfs:latest',
                    'driver_opts': {'sshcmd': sshcmd, 'id_rsa': private_key,
                                    'big_writes': '', 'allow_other': '', 'port': '2222'}}

    # Auth requests
    user_cert = '/C=DK/ST=NA/L=NA/O=NBI/OU=NA/CN=Name' \
                '/emailAddress=mail@sdfsf.com'

    # Username should not be root normally, used for testing here
    user_header = {'Remote-User': user_cert}

    with requests.Session() as session:
        try:
            session.get(hub_url)
        except (requests.ConnectionError, requests.exceptions.InvalidSchema):
            print("{} can't be reached".format(hub_url))
            return 1

        # Auth
        session.get(''.join([hub_url, auth_url]), headers=user_header)
        # Spawn
        session.post(''.join([hub_url, spawn_url]), headers=user_header)

        # Write test

# name = NETWORK_NAME,
# driver = "overlay",
# options = {"subnet": "192.168.0.0/20"},
# attachable = True
