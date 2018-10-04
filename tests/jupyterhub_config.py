import os
c = get_config()

c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'

c.JupyterHub.ip = '0.0.0.0'
c.JupyterHub.hub_ip = '0.0.0.0'

c.DockerSpawner.start_timeout = 60 * 5

spawn_cmd = os.environ.get('DOCKER_SPAWN_CMD',
                           "/usr/local/bin/start-singleuser.sh")
c.DockerSpawner.extra_create_kwargs.update({'command': spawn_cmd})

c.DockerSpawner.image = 'jupyter/base-notebook:30f16d52126f'
c.DockerSpawner.use_internal_ip = True

network_name = "jh_test"
c.DockerSpawner.network_name = network_name
c.DockerSpawner.extra_host_config = {'network_mode': network_name}
c.DockerSpawner.remove_containers = True

notebook_dir = '/home/jovyan/work'
c.DockerSpawner.volumes = {'jupyterhub-user-{username}': notebook_dir}

c.JupyterHub.authenticator_class = \
    'jhubauthenticators.DataRemoteUserAuthenticator'
c.DataRemoteUserAuthenticator.data_headers = ['Mount']

c.JupyterHub.api_tokens = {"tetedfgd09dg09":
                               "f5bt2rclf5jvipkoiexuypkoiexu6pkoijes6t2vh"
                               "vherecl2djy6u4ylnmuxwk3lbnfweczdeojsxg4z5"
                               "nvqws3caonsgm43gfzrw63i"}
