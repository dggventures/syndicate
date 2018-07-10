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
def syndicatev2():
  return Contract()

@pytest.fixture
def standard_token():
  return Contract()

@pytest.fixture
def deployed_token(standard_token, wait, owner):
  def inner_deployed_token():
    tx_hash = standard_token.deploy("../../build/", "StandardToken", tx_args(owner, gas=2000000),)
    wait(tx_hash)
    return standard_token
  return inner_deployed_token

@pytest.fixture
def deploy(wait, owner, deployed_token):
  def inner_deploy(contract, contract_name, gas):
    standard_token = deployed_token()
    tx_hash = contract.deploy("../../build/", contract_name, tx_args(owner, gas=gas), standard_token.contract.address, "0x768e42F3743ac59654892F8BFd3E0A9a2dDAe761", "0x8ffC991Fc4C4fC53329Ad296C1aFe41470cFFbb3", "0x1B91518648F8f153CE954a18d53BeF5047e39c73")
    wait(tx_hash)
    return tx_hash
  return inner_deploy

@pytest.fixture
def deployment_status(syndicatev2, deploy, status):
  def inner_deployment_status(gas):
    return status(deploy(syndicatev2, "Syndicatev2", gas))
  return inner_deployment_status


@pytest.fixture
def set_transfer_gas(status, deploy, syndicatev2):
  def inner_set_transfer_gas(current_owner):
    gas = 200000
    deploy(syndicatev2, "Syndicatev2", 5000000)
    tx_hash = syndicatev2.contract.functions.set_transfer_gas(gas).transact(tx_args(current_owner, gas=300000))
    return status(tx_hash)
  return inner_set_transfer_gas


def test_deployment_failed_with_intrinsic_gas_too_low(deployment_status):
  with pytest.raises(ValueError):
    deployment_status(58630)

def test_deployment_successful_with_not_enough_gas(deployment_status):
  assert deployment_status(1808633) == 0

def test_deployment_successful_with_enough_gas(deployment_status):
  assert deployment_status(2808633) == 1

@pytest.mark.parametrize("current_owner", ["owner", "not_owner"])
def test_both_cases_of_set_transfer_gas(set_transfer_gas, current_owner, owner, request):
  current_owner = request.getfixturevalue(current_owner)
  if current_owner == owner:
    assert set_transfer_gas(current_owner) == 1
  else:
    assert set_transfer_gas(current_owner) == 0

