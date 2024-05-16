======================
docker-ssh-mount-dummy
======================

.. image:: https://img.shields.io/docker/v/ucphhpc/ssh-mount-dummy
    :target: https://hub.docker.com/r/ucphhpc/ssh-mount-dummy

.. image:: https://img.shields.io/docker/pulls/ucphhpc/ssh-mount-dummy
    :target: https://hub.docker.com/r/ucphhpc/ssh-mount-dummy

.. image:: https://img.shields.io/docker/image-size/ucphhpc/ssh-mount-dummy
    :target: https://hub.docker.com/r/ucphhpc/ssh-mount-dummy

A simple repo for providing a Docker container that can be used to test SSH(FS) access and mounting.

**This is used for testing and should not be used in production for anything!**

Builds of this image can be found at `DockerHub <https://hub.docker.com/r/ucphhpc/ssh-mount-dummy>`_.

---------------
Getting Started
---------------

To build the image, simply use make in the root of the repo directory::

    $ make
    ln -s defaults.env .env
    docker-compose build 
    Building agent
    Sending build context to Docker daemon  42.84MB
    Step 1/18 : FROM debian:latest
    ...
    Step 18/18 : CMD ["/usr/bin/python3", "/app/main.py"]
    [Warning] One or more build-args [TAG TZ] were not consumed
    Successfully built 0607b95f8b54
    Successfully tagged ucphhpc/ssh-mount-dummy:edge

--------------
Authentication
--------------

The default username and password for the `ucphhpc/ssh-mount-dummy` image is set to ``mountuser`` and ``Passw0rd!``.
This can be changed by modifying the ``.env`` file before the image is being built with make.
After changing either the ``PASSWORD`` or ``USERNAME`` definitions in the ``.env`` file, the image has to be rebuilt before the changes
will take effect.

An alternative to password based authentication, is to used public key authentication.
The default way to accomplish this, is to put your public key in the specified ``authorized-keys`` directory in the root path of the repository.
This directory is created by default when the ``make init`` target is executed.

The default ``docker-compose.yml`` then defines that the `authorized-keys` directory is mounted into the container's ${AUTHORIZED_KEYS_DIR} directory as set in the .env file.
Upon container instantiation, the public keys in the mounted `authorized-keys` directory are then copied to the default ``/home/${USERNAME}/.ssh/authorized_keys`` file by the ``main.py`` script.

-------------------------
Mounting host directories
-------------------------

In addition to authentication, you can also customized which directories you want to mount from the host into the ssh mount dummy container.
The recommended approach, is to amend the ``docker-compose.yml`` file to include the desired directories to be mounted via the ``volumes`` directive.
For example, to mount the host's ``mnt`` directory into the ``${USERNAME}``'s home directory, namely the ``/home/${USERNAME}/mnt`` directory, the following can be added to the ``docker-compose.yml`` file::

    volumes:
      - ./authorized-keys:${AUTHORIZED_KEYS_DIR}:ro
      - ./mnt:/home/${USERNAME}/mnt:rw

An alternative approach is to use the ``-v`` flag when launching the container with ``docker run``.

    $ docker run -d --env /path/to/docker-ssh-mount-dummy-repo/.env -p 2222:22 -v /path/to/docker-ssh-mount-dummy-repo/mnt:/home/${USERNAME}/mnt ucphhpc/ssh-mount-dummy:latest

-------
Running
-------

After every configuration change required has been made, the simplest way to run the container is to use the ``make up`` target::

    $ make up
    docker-compose up -d
    Creating network "docker-ssh-mount-dummy_default" with the default driver
    Creating agent ... done

This will launch the image with the environment specifications defined in the .env file and the specified mounted volumes.

In turn, the launched image can be stopped by executing the ``make down`` target::

    make down

--------
Security
--------
Any security related questions/issues/inquries should be directed at security@erda.dk
