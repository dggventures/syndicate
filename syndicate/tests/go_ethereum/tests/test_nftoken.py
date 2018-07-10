#!/usr/bin/env python3

import pytest
import sys
sys.path.append("../../../deployment")
from contract import Contract
from tx_args import tx_args


@pytest.fixture(scope="session")
def owner(web3_2):
  return web3_2.eth.accounts[0]

@pytest.fixture(scope="session")
def not_owner(web3_2):
  return web3_2.eth.accounts[1]

@pytest.fixture
def nftoken():
  return Contract()

@pytest.fixture
def deploy(wait, owner):
  def inner_deploy(contract, contract_name, gas):
    tx_hash = contract.deploy("../../build/", contract_name, tx_args(owner, gas=gas),)
    wait(tx_hash)
    return tx_hash
  return inner_deploy

@pytest.fixture
def deployment_status(nftoken, deploy, status):
  def inner_deployment_status(gas):
    return status(deploy(nftoken, "NFToken", gas))
  return inner_deployment_status