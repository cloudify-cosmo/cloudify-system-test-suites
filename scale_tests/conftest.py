import os
import pytest

from cosmo_tester.framework import util
from cosmo_tester.framework.cluster import CloudifyCluster

from .framework.constants import BLUEPRINT_TYPES
from .framework.blueprint_example import BlueprintExample
from .framework.concurrent_resource_creator import ConcurrentResourceCreator

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
    current_manager = cluster.managers[0]
    _install_datadog_agent(current_manager, logger)
    current_manager.use()
    yield current_manager
    cluster.destroy()


@pytest.fixture(scope='module')
def blueprint_example(manager, scale_attributes):
    scale_attributes.remote_private_key_path = manager.remote_private_key_path
    blueprint = BlueprintExample(scale_attributes)
    return blueprint


@pytest.fixture(scope='module')
def resource_creator(manager, blueprint_example, logger):
    creator = ConcurrentResourceCreator(manager, blueprint_example, logger)
    return creator


@pytest.fixture(scope='module')
def deployments_count(request):
    """Get the cli option of how many deployments to create/install"""
    return int(request.config.getoption('--deployments-count'))


def pytest_addoption(parser):
    parser.addoption('--deployments-count', action='store', default=10,
                     help='how many deployments to create/install')
    parser.addoption('--tenants-count', action='store', default=10,
                     help='how many tenants to create')
    parser.addoption('--blueprint-type', action='store', default='monitoring',
                     help="the blueprint's type, one of : {}".format(', '.join(BLUEPRINT_TYPES)))
    parser.addoption('--blueprints-count', action='store', default=10,
                     help='how many blueprints to upload')


def _install_datadog_agent(manager, logger):
    logger.info('Installing Datadog agent on the manager')
    dd_api_key = os.environ.get('DD_API_KEY')

    if not dd_api_key:
        raise Exception('DD_API_KEY environment variable is not set')

    install_cmd = 'DD_HOSTNAME={0} DD_API_KEY={1} bash -c "$(curl -L https://' \
                  'raw.githubusercontent.com/DataDog/dd-agent/master/packaging/datadog-agent/' \
                  'source/install_agent.sh)"'.format('scale-tests', dd_api_key)
    with manager.ssh() as fabric_ssh:
        fabric_ssh.sudo(install_cmd)
