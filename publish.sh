#!/bin/bash

set -e

REPO=https://artifactory.gamma.bcg.com/artifactory/api/pypi/local-pypi-8999823-devex-br-01
USERNAME=almeida.cloves@bcg.com
PASSWORD="$ARTIFACTORY_KEY"

. venv/bin/activate
pip install twine

python setup.py bdist_wheel

twine upload --verbose \
    --repository-url "$REPO" \
    -u $USERNAME -p $PASSWORD \
    dist/*.whl
