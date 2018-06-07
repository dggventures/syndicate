#!/usr/bin/bash

virtualenv -p python3 ./py-venv
source ./py-venv/bin/activate
pip install --upgrade pip setuptools
pip install --upgrade web3
