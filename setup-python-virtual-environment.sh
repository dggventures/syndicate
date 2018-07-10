#!/usr/bin/bash

virtualenv -p python3 ./py-venv
source ./py-venv/bin/activate
pip install --upgrade pip setuptools
pip install --upgrade pytest
pip install --upgrade web3 eth_utils
