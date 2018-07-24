#!/usr/bin/env python3

import pytest
import sys
sys.path.append("../../../deployment")
from contract import Contract
from tx_args import tx_args


@pytest.fixture(scope="session")
def ether_sender(web3_2):
  return web3_2.eth.accounts[0]

@pytest.fixture(scope="session")
def not_ether_sender(web3_2):
  return web3_2.eth.accounts[1]

@pytest.fixture(scope="session")
def token_owner(web3_2):
  return web3_2.eth.accounts[2]

@pytest.fixture(scope="session")
def agent(web3_2):
  return web3_2.eth.accounts[3]

@pytest.fixture(scope="session")
def operator(web3_2):
  return web3_2.eth.accounts[4]

@pytest.fixture(scope="session")
def no_credentials_sender(web3_2):
  return web3_2.eth.accounts[5]

@pytest.fixture
def nftoken():
  return Contract()

@pytest.fixture
def deploy(wait, token_owner):
  def inner_deploy(contract, contract_name, gas):
    tx_hash = contract.deploy("../../build/", contract_name, tx_args(token_owner, gas=gas),)
    wait(tx_hash)
    return tx_hash
  return inner_deploy

@pytest.fixture
def deployment_status(nftoken, deploy, status):
  def inner_deployment_status(gas):
    return status(deploy(nftoken, "NFToken", gas))
  return inner_deployment_status

@pytest.fixture
def safe_transfer_from(status, deploy, nftoken, token_owner, agent, operator):
  def inner_safe_transfer_from(current_sender, from_addr, to_addr):
    deploy(nftoken, "NFTokenMock", 5000000)
    tx_hash = nftoken.contract.functions.mintInternalMock(token_owner).transact(tx_args(token_owner, gas=1000000))
    assert status(tx_hash)
    token_id = nftoken.contract.functions.token_id().call()
    data = ""
    data = data.encode()
    tx_hash = nftoken.contract.functions.approve(agent, token_id).transact(tx_args(token_owner, gas=1000000))
    assert status(tx_hash)
    tx_hash = nftoken.contract.functions.setApprovalForAll(operator, True).transact(tx_args(token_owner, gas=1000000))
    assert status(tx_hash)
    tx_hash = nftoken.contract.functions.safeTransferFrom(from_addr,
                                                          to_addr,
                                                          token_id,
                                                          data).transact(tx_args(current_sender, gas=1000000))
    return status(tx_hash)
  return inner_safe_transfer_from


# General test cases functions

def test_deployment_raises_error_with_intrinsic_gas_too_low(deployment_status):
  with pytest.raises(ValueError):
    deployment_status(50000)

def test_deployment_fails_with_not_enough_gas(deployment_status):
  assert deployment_status(500000) == 0

def test_deployment_succeeds_with_enough_gas(deployment_status):
  assert deployment_status(9000000)

@pytest.mark.parametrize("current_sender", ["token_owner", "agent", "operator", "no_credentials_sender"])
@pytest.mark.parametrize("from_addr", ["token_owner", "no_credentials_sender"])
def test_safe_transfer_from(request, safe_transfer_from, current_sender, from_addr, token_owner, agent, operator):
  current_sender = request.getfixturevalue(current_sender)
  from_addr = request.getfixturevalue(from_addr)
  to_addr = operator
  if (current_sender == token_owner or current_sender == agent or current_sender == operator) and from_addr == token_owner:
    assert safe_transfer_from(current_sender, from_addr, to_addr)
  else:
    assert safe_transfer_from(current_sender, from_addr, to_addr) == 0