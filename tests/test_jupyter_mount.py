import os
import pytest
import socket
import requests
import json
import docker
from docker.types import Mount
from os.path import join, dirname, realpath

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
@pytest.mark.parametrize('network', [{'name': NETWORK_NAME, 'driver': 'bridge'}],
                         indirect=['network'])
def test_jupyter_mount(image, network, make_container):
    client = docker.from_env()
    jhub = make_container(jhub_cont)
    dummy = make_container(dummy_cont)
    containers_pre = set(client.containers.list())
    base_url = 'http://127.0.0.1:8000'
    hub_url = '{}/hub'.format(base_url)

    auth_url, mount_url, spawn_url = '/login', '/mount', '/spawn'
    # volume
    target_user = 'mountuser'
    ssh_host_target = socket.gethostname()
    private_key = dummy.exec_run('cat /home/mountuser/.ssh/id_rsa')[1].decode('utf-8')

    # Auth requests
    user_cert = '/C=DK/ST=NA/L=NA/O=NBI/OU=NA/CN=Name' \
                '/emailAddress=mail@sdfsf.com'

    mount_dict = {'HOST': 'DUMMY', 'USERNAME': target_user,
                  'PATH': ''.join(['@', ssh_host_target, ':']),
                  'PRIVATEKEY': private_key}

    # Username should not be root normally, used for testing here
    header = {'Remote-User': user_cert,
              'Mount': str(mount_dict)}

    with requests.Session() as session:
        try:
            resp = session.get(hub_url)
        except (requests.ConnectionError, requests.exceptions.InvalidSchema):
            print("{} can't be reached".format(hub_url))
            return 1
        # Auth
        resp = session.get(''.join([hub_url, auth_url]), headers=header)
        cookies = resp.cookies
        assert resp.status_code == 200
        # Mount
        resp = session.post(''.join([hub_url, mount_url]), headers=header)
        assert resp.status_code == 200
        # Spawn
        resp = session.post(''.join([hub_url, spawn_url]), headers=header)
        assert resp.status_code == 200

        spawned_containers = set(client.containers.list()) - containers_pre

        for container in spawned_containers:
            notebook_id = container.name.strip("jupyter-")
            hub_api_url = "/user/{}/api/contents/".format(notebook_id)
            # Write test
            new_file = 'work/write_test.ipynb'
            data = json.dumps({'name': new_file})
            notebook_headers = {'X-XSRFToken': session.cookies['_xsrf']}
            resp = session.put(''.join([base_url, hub_api_url, new_file]), data=data,
                               headers=notebook_headers)
            assert resp.status_code == 201

            # Remove notebook
            remove_url = '/api/users/{}/server'.format(notebook_id)
            header.update({'Authorization': 'token tetedfgd09dg09'})
            # Remove
            resp = session.delete(''.join([hub_url, remove_url]), headers=header)
            assert resp.status_code == 204
            client.volumes.prune()
