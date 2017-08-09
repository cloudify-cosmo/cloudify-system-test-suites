import os
import pytest

from cosmo_tester.framework import util
from cosmo_tester.framework.cluster import CloudifyCluster

from framework.blueprint_example import BlueprintExample
from framework.concurrent_resource_creator import ConcurrentResourceCreator

pytest_plugins = "cosmo_tester.conftest"


@pytest.fixture(scope='module')
def scale_attributes(attributes, logger):
    resources_path = os.path.join(os.path.dirname(__file__), 'resources')
    current_attributes = util.get_attributes(logger, resources_dir=resources_path)
    attributes.update(current_attributes)
    return attributes


@pytest.fixture(scope='module')
def manager(cfy, ssh_key, module_tmpdir, scale_attributes, logger):
    """Creates a cloudify manager from an image in rackspace OpenStack."""
    cluster = CloudifyCluster.create_image_based(
            cfy, ssh_key, module_tmpdir, scale_attributes, logger)
    cluster.managers[0].use()
    yield cluster.managers[0]
    cluster.destroy()


@pytest.fixture(scope='module')
def blueprint_example(manager, scale_attributes):
    scale_attributes.remote_private_key_path = manager.remote_private_key_path
    blueprint = BlueprintExample(scale_attributes)
    return blueprint


@pytest.fixture(scope='module')
def resource_creator(manager, blueprint_example, logger):
    creator = ConcurrentResourceCreator(
        manager.client, blueprint_example, logger)
    return creator
