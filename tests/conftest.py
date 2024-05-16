import time
import docker
import pytest
from docker.errors import NotFound


@pytest.fixture(scope="function")
def network(request):
    """Create the overlay network that the hub and server services will
    use to communicate.
    """
    client = docker.from_env()
    _network = client.networks.create(**request.param)
    yield _network
    _network.remove()
    removed = False
    while not removed:
        try:
            client.networks.get(_network.id)
        except NotFound:
            removed = True


@pytest.fixture(scope="function")
def image(request):
    client = docker.from_env()
    _image = client.images.build(**request.param)
    yield _image

    # Remove image after test usage
    image_obj = _image[0]
    image_id = image_obj.id
    client.images.remove(image_obj.tags[0], force=True)

    removed = False
    while not removed:
        try:
            client.images.get(image_id)
        except NotFound:
            removed = True


@pytest.fixture(name="make_service")
def make_service_():
    created = []
    client = docker.from_env()

    def make_service(options):
        _service = client.services.create(**options)
        while "running" not in [task["Status"]["State"] for task in _service.tasks()]:
            time.sleep(1)
            _service = client.services.get(_service.id)
        created.append(_service)
        return _service

    yield make_service

    for c in created:
        assert hasattr(c, "id")
        c.remove()
        removed = False
        while not removed:
            try:
                client.services.get(c.id)
            except NotFound:
                removed = True


@pytest.fixture(name="make_volume")
def make_volume_():
    created = []
    client = docker.from_env()

    def make_volume(options):
        _volume = client.volumes.create(options)
        created.append(_volume)
        return _volume

    yield make_volume

    for c in created:
        _id = c.id
        c.remove()
        removed = False
        while not removed:
            try:
                client.volumes.get(_id)
            except NotFound:
                removed = True
