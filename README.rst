======================
docker-ssh-mount-dummy
======================

A simple repo for providing a Docker container that can be used to test SSH(FS) access and mounting.

**This is used for testing and should not be used in production for anything!**

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

-------------
Configuration
-------------

The default password in the `ucphhpc/ssh-mount-dummy` image is set to ``Passw0rd!``.
This can be changed by modifying the ``.env`` file before the image is being built with make.

After changing either the ``PASSWORD`` or ``USERNAME`` definitions in the ``.env`` file, the image has to be rebuilt before the changes
will take effect.

-------
Running
-------

To launch the built image, the easiest way is to simply use ``docker-compose`` inside the repo directory::

    $ docker-compose up -d

This will launch the image with the environment specifications defined in the .env file.

In turn, the launched image can be stopped by running the following command::

    docker-compose down

