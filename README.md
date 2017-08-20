Cloudify System Test Suites
===========================

* Master [![Circle CI](https://circleci.com/gh/cloudify-cosmo/cloudify-system-test-suites/tree/master.svg?&style=shield)](https://circleci.com/gh/cloudify-cosmo/cloudify-system-test-suites/tree/master)

The system test suites uses the system tests framework, follow the instructions [here](https://github.com/cloudify-cosmo/cloudify-system-tests/blob/master/README.md).


# Scale tests
## Running tests

When running tests a Datadog Agent is being installed on the manager to collect metrics.
Before running a test, make sure to set the environment variable DD_API_KEY (Datadog API key).

```bash
export DD_API_KEY=your_api_key
```

Your API key can be found [here](https://app.datadoghq.com/account/settings#api).


Run :
```bash
pytest -s agents_test.py --deployments-count=1 --blueprint-type=monitoring
```

CLI Options :
* `--deployments-count` : how many deployments to create/install.
* `--blueprint-type` : the blueprint's type, one of : 'monitoring', 'no-monitoring' and 'agentless' (only for agents_test).


Please note it is important to run tests with the `-s` flag as the framework uses `Fabric` which is known to have problems with pytest's output capturing (https://github.com/pytest-dev/pytest/issues/1585).
