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

@pytest.fixture(scope="session")
def correct_token_id():
  return 0

@pytest.fixture(scope="session")
def incorrect_token_id():
  return 1

@pytest.fixture(scope="session")
def data_example():
  return "MessageData"

@pytest.fixture(scope="session")
def empty_data():
  return ""

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
def safe_transfer_from_with_data(status, deploy, nftoken, token_owner, agent, operator, correct_token_id):
  def inner_safe_transfer_from_with_data(current_sender, from_addr, to_addr, data, token_id):
    deploy(nftoken, "NFTokenMock", 5000000)
    tx_hash = nftoken.contract.functions.mintInternalMock(token_owner).transact(tx_args(token_owner, gas=1000000))
    assert status(tx_hash)
    data = data.encode()
    tx_hash = nftoken.contract.functions.approve(agent, token_id).transact(tx_args(token_owner, gas=1000000))
    if token_id == correct_token_id:
      assert status(tx_hash)
    else:
      assert status(tx_hash) == 0
    tx_hash = nftoken.contract.functions.setApprovalForAll(operator, True).transact(tx_args(token_owner, gas=1000000))
    assert status(tx_hash)
    tx_hash = nftoken.contract.functions.safeTransferFrom(from_addr,
                                                          to_addr,
                                                          token_id,
                                                          data).transact(tx_args(current_sender, gas=1000000))
    return status(tx_hash)
  return inner_safe_transfer_from_with_data

@pytest.fixture
def safe_transfer_from_without_data(status, deploy, nftoken, token_owner, agent, operator, correct_token_id):
  def inner_safe_transfer_from_without_data(current_sender, from_addr, to_addr, token_id):
    deploy(nftoken, "NFTokenMock", 5000000)
    tx_hash = nftoken.contract.functions.mintInternalMock(token_owner).transact(tx_args(token_owner, gas=1000000))
    assert status(tx_hash)
    tx_hash = nftoken.contract.functions.approve(agent, token_id).transact(tx_args(token_owner, gas=1000000))
    if token_id == correct_token_id:
      assert status(tx_hash)
    else:
      assert status(tx_hash) == 0
    tx_hash = nftoken.contract.functions.setApprovalForAll(operator, True).transact(tx_args(token_owner, gas=1000000))
    assert status(tx_hash)
    tx_hash = nftoken.contract.functions.safeTransferFrom(from_addr,
                                                          to_addr,
                                                          token_id).transact(tx_args(current_sender, gas=1000000))
    return status(tx_hash)
  return inner_safe_transfer_from_without_data

@pytest.fixture
def transfer_from(status, deploy, nftoken, token_owner, agent, operator, correct_token_id):
  def inner_transfer_from(current_sender, from_addr, to_addr, token_id):
    deploy(nftoken, "NFTokenMock", 5000000)
    tx_hash = nftoken.contract.functions.mintInternalMock(token_owner).transact(tx_args(token_owner, gas=1000000))
    assert status(tx_hash)
    tx_hash = nftoken.contract.functions.approve(agent, token_id).transact(tx_args(token_owner, gas=1000000))
    if token_id == correct_token_id:
      assert status(tx_hash)
    else:
      assert status(tx_hash) == 0
    tx_hash = nftoken.contract.functions.setApprovalForAll(operator, True).transact(tx_args(token_owner, gas=1000000))
    assert status(tx_hash)
    tx_hash = nftoken.contract.functions.transferFrom(from_addr,
                                                      to_addr,
                                                      token_id).transact(tx_args(current_sender, gas=1000000))
    return status(tx_hash)
  return inner_transfer_from

@pytest.fixture
def approve(status, deploy, nftoken, token_owner, agent, operator):
  def inner_approve(current_sender, token_id):
    deploy(nftoken, "NFTokenMock", 5000000)
    tx_hash = nftoken.contract.functions.mintInternalMock(token_owner).transact(tx_args(token_owner, gas=1000000))
    assert status(tx_hash)
    tx_hash = nftoken.contract.functions.setApprovalForAll(operator, True).transact(tx_args(token_owner, gas=1000000))
    assert status(tx_hash)
    tx_hash = nftoken.contract.functions.approve(agent, token_id).transact(tx_args(current_sender, gas=1000000))
    return status(tx_hash)
  return inner_approve

@pytest.fixture
def set_approval_for_all(status, deploy, nftoken, token_owner, operator):
  def inner_set_approval_for_all():
    deploy(nftoken, "NFTokenMock", 5000000)
    tx_hash = nftoken.contract.functions.setApprovalForAll(operator, True).transact(tx_args(token_owner, gas=1000000))
    return status(tx_hash)
  return inner_set_approval_for_all

@pytest.fixture
def mint_internal(status, deploy, nftoken, token_owner, operator):
  def inner_mint_internal():
    deploy(nftoken, "NFTokenMock", 5000000)
    tx_hash = nftoken.contract.functions.mintInternalMock(operator).transact(tx_args(token_owner, gas=1000000))
    return status(tx_hash)
  return inner_mint_internal


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
@pytest.mark.parametrize("data", ["empty_data", "data_example"])
@pytest.mark.parametrize("token_id", ["correct_token_id", "incorrect_token_id"])
def test_safe_transfer_from_with_data(request, safe_transfer_from_with_data, current_sender, from_addr, data, token_id, token_owner, agent, operator, correct_token_id):
  current_sender = request.getfixturevalue(current_sender)
  from_addr = request.getfixturevalue(from_addr)
  data = request.getfixturevalue(data)
  token_id = request.getfixturevalue(token_id)
  to_addr = operator
  if (current_sender == token_owner or current_sender == agent or current_sender == operator) and from_addr == token_owner and token_id == correct_token_id:
    assert safe_transfer_from_with_data(current_sender, from_addr, to_addr, data, token_id)
  else:
    assert safe_transfer_from_with_data(current_sender, from_addr, to_addr, data, token_id) == 0

@pytest.mark.parametrize("current_sender", ["token_owner", "agent", "operator", "no_credentials_sender"])
@pytest.mark.parametrize("from_addr", ["token_owner", "no_credentials_sender"])
@pytest.mark.parametrize("token_id", ["correct_token_id", "incorrect_token_id"])
def test_safe_transfer_from_without_data(request, safe_transfer_from_without_data, current_sender, from_addr, token_id, token_owner, agent, operator, correct_token_id):
  current_sender = request.getfixturevalue(current_sender)
  from_addr = request.getfixturevalue(from_addr)
  token_id = request.getfixturevalue(token_id)
  to_addr = operator
  if (current_sender == token_owner or current_sender == agent or current_sender == operator) and from_addr == token_owner and token_id == correct_token_id:
    assert safe_transfer_from_without_data(current_sender, from_addr, to_addr, token_id)
  else:
    assert safe_transfer_from_without_data(current_sender, from_addr, to_addr, token_id) == 0

@pytest.mark.parametrize("current_sender", ["token_owner", "agent", "operator", "no_credentials_sender"])
@pytest.mark.parametrize("from_addr", ["token_owner", "no_credentials_sender"])
@pytest.mark.parametrize("token_id", ["correct_token_id", "incorrect_token_id"])
def test_transfer_from(request, transfer_from, current_sender, from_addr, token_id, token_owner, agent, operator, correct_token_id):
  current_sender = request.getfixturevalue(current_sender)
  from_addr = request.getfixturevalue(from_addr)
  token_id = request.getfixturevalue(token_id)
  to_addr = operator
  if (current_sender == token_owner or current_sender == agent or current_sender == operator) and from_addr == token_owner and token_id == correct_token_id:
    assert transfer_from(current_sender, from_addr, to_addr, token_id)
  else:
    assert transfer_from(current_sender, from_addr, to_addr, token_id) == 0

@pytest.mark.parametrize("current_sender", ["token_owner", "operator", "no_credentials_sender"])
@pytest.mark.parametrize("token_id", ["correct_token_id", "incorrect_token_id"])
def test_approve(request, approve, current_sender, token_id, token_owner, operator, correct_token_id):
  current_sender = request.getfixturevalue(current_sender)
  token_id = request.getfixturevalue(token_id)
  if (current_sender == token_owner or current_sender == operator) and token_id == correct_token_id:
    assert approve(current_sender, token_id)
  else:
    assert approve(current_sender, token_id) == 0

def test_set_approval_for_all(set_approval_for_all):
  assert set_approval_for_all()

def test_mint_internal(mint_internal):
  assert mint_internal()