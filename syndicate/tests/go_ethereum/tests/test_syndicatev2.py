#!/usr/bin/env python3

import pytest
import sys
sys.path.append("../../../deployment")
from contract import Contract
from tx_args import tx_args
import os
from client_config import config_f
from datetime import datetime


ADDRESS_ZERO = "0x0000000000000000000000000000000000000000"

@pytest.fixture
def crowdsale_path():
  return os.path.abspath("../../../../../../ICOSample/ICOSample/deployment/build")

@pytest.fixture
def address_zero():
  return ADDRESS_ZERO

@pytest.fixture
def config():
  def inner_config(start_time):
    config_dict = config_f()
    config_dict["start_time"] = start_time
    return config_dict
  return inner_config

@pytest.fixture(scope="session")
def owner(web3_2):
  return web3_2.eth.accounts[0]

@pytest.fixture(scope="session")
def not_owner(web3_2):
  return web3_2.eth.accounts[1]

@pytest.fixture(scope="session")
def ether_sender(web3_2):
  return web3_2.eth.accounts[2]

@pytest.fixture(scope="session")
def not_ether_sender(web3_2):
  return web3_2.eth.accounts[3]

@pytest.fixture
def syndicatev2():
  return Contract()

@pytest.fixture
def crowdsale():
  return Contract()

@pytest.fixture
def standard_token():
  return Contract()

@pytest.fixture
def contract_from_address(web3_2, crowdsale_path):
  def inner_contract_from_address(address, contract_name):
    contract_abi, contract_bytecode = Contract.get_abi_and_bytecode(crowdsale_path, contract_name)
    contract = web3_2.eth.contract(address=address, abi=contract_abi, bytecode=contract_bytecode)
    return contract
  return inner_contract_from_address

@pytest.fixture
def get_balance_after_sending_ether(deploy, syndicatev2, web3_2, status, owner):
  def inner_get_balance_after_sending_ether():
    deploy(syndicatev2, "Syndicatev2", 3000000)
    tx_hash = syndicatev2.contract.functions.set_transfer_gas(300000).transact(tx_args(owner, gas=900000))
    assert status(tx_hash)
    tx_hash = web3_2.eth.sendTransaction({"from": owner,
                                          "to": syndicatev2.contract.address,
                                          "value": web3_2.toWei(20, "ether"),
                                          "gas": 500000})
    assert status(tx_hash)
    balance = web3_2.fromWei(web3_2.eth.getBalance(syndicatev2.contract.address), "ether")
    return balance
  return inner_get_balance_after_sending_ether

@pytest.fixture
def deployed_crowdsale(crowdsale, owner, config, status, crowdsale_path):
  def inner_deployed_crowdsale():
    config_dict = config(int(datetime.now().timestamp()) + 6)
    tx_hash = crowdsale.deploy(crowdsale_path, "Crowdsale", tx_args(owner, gas=5000000),)
    assert status(tx_hash)
    tx_hash = crowdsale.contract.functions.configurationCrowdsale(config_dict["MW_address"],
                                                                  config_dict["start_time"],
                                                                  config_dict["end_time"],
                                                                  config_dict["token_retriever_account"],
                                                                  config_dict["tranches"],
                                                                  config_dict["multisig_supply"],
                                                                  config_dict["crowdsale_supply"],
                                                                  config_dict["token_decimals"],
                                                                  config_dict["max_tokens_to_sell"]
                                                                  ).transact(tx_args(owner, gas=9000000))
    assert status(tx_hash)
    return crowdsale
  return inner_deployed_crowdsale

@pytest.fixture
def eip20token_address(deployed_crowdsale):
  crowdsale = deployed_crowdsale()
  token_address = crowdsale.contract.functions.token().call()
  return token_address

@pytest.fixture
def deploy(owner, address_zero, wait, deployed_crowdsale):
  def inner_deploy(contract, contract_name, gas):
    crowdsale = deployed_crowdsale()
    token_address = crowdsale.contract.functions.token().call()
    assert token_address != address_zero
    assert crowdsale.contract.address != address_zero
    tx_hash = contract.deploy("../../build/",
                              contract_name,
                              tx_args(owner, gas=gas),
                              token_address,
                              crowdsale.contract.address,
                              "0x8ffC991Fc4C4fC53329Ad296C1aFe41470cFFbb3",
                              "0x1B91518648F8f153CE954a18d53BeF5047e39c73")
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
    tx_hash = syndicatev2.contract.functions.set_transfer_gas(gas).transact(tx_args(current_owner, gas=1000000))
    return status(tx_hash)
  return inner_set_transfer_gas

@pytest.fixture
def emergency_withdraw(status, deploy, syndicatev2):
  def inner_emergency_withdraw(current_owner):
    deploy(syndicatev2, "Syndicatev2", 5000000)
    tx_hash = syndicatev2.contract.functions.emergency_withdraw().transact(tx_args(current_owner, gas=1000000))
    return status(tx_hash)
  return inner_emergency_withdraw

@pytest.fixture
def update_token(status, deploy, syndicatev2):
  def inner_update_token(current_owner, token):
    deploy(syndicatev2, "Syndicatev2", 5000000)
    tx_hash = syndicatev2.contract.functions.update_token(token).transact(tx_args(current_owner, gas=3000000))
    return status(tx_hash)
  return inner_update_token

@pytest.fixture
def set_enforce_whitelist(status, deploy, syndicatev2):
  def inner_set_enforce_whitelist(current_owner, value):
    deploy(syndicatev2, "Syndicatev2", 5000000)
    tx_hash = syndicatev2.contract.functions.set_enforce_whitelist(value).transact(tx_args(current_owner, gas=1000000))
    return status(tx_hash)
  return inner_set_enforce_whitelist

@pytest.fixture
def whitelist(status, deploy, syndicatev2):
  def inner_whitelist(current_owner, value):
    deploy(syndicatev2, "Syndicatev2", 5000000)
    tx_hash = syndicatev2.contract.functions.whitelist(current_owner, value).transact(tx_args(current_owner, gas=1000000))
    return status(tx_hash)
  return inner_whitelist

@pytest.fixture
def withdraw_tokens(status, deploy, syndicatev2, ether_sender, owner, web3_2, contract_from_address):
  def inner_withdraw_tokens(current_sender):
    deploy(syndicatev2, "Syndicatev2", 5000000)
    tx_hash = syndicatev2.contract.functions.set_transfer_gas(2000000).transact(tx_args(owner, gas=900000))
    assert status(tx_hash)
    crowdsale_contract = contract_from_address(syndicatev2.contract.functions.purchase_address().call(), "Crowdsale")
    tx_hash = crowdsale_contract.functions.setTransferAgent(syndicatev2.contract.address, True).transact(tx_args(owner, gas=900000))
    assert status(tx_hash)
    tx_hash = web3_2.eth.sendTransaction({"from": ether_sender,
                                          "to": syndicatev2.contract.address,
                                          "value": web3_2.toWei(5, "ether"),
                                          "gas": 2000000})
    assert status(tx_hash)
    tx_hash = syndicatev2.contract.functions.withdraw_tokens().transact(tx_args(current_sender, gas=1900000))
    return status(tx_hash)
  return inner_withdraw_tokens

@pytest.fixture
def send_ether(status, deploy, syndicatev2, web3_2, owner):
  def inner_send_ether(current_sender):
    deploy(syndicatev2, "Syndicatev2", 5000000)
    tx_hash = syndicatev2.contract.functions.set_transfer_gas(260000).transact(tx_args(owner, gas=50000))
    assert status(tx_hash)
    tx_hash = web3_2.eth.sendTransaction({"from": current_sender,
                                          "to": syndicatev2.contract.address,
                                          "value": web3_2.toWei(5, "ether"),
                                          "gas": 500000})
    return status(tx_hash)
  return inner_send_ether

@pytest.fixture
def transfer_from(status, deploy, syndicatev2, ether_sender, web3_2, owner):
  def inner_transfer_from(from_addr, to_addr, token_id, current_tx_sender):
    deploy(syndicatev2, "Syndicatev2", 5000000)
    tx_hash = syndicatev2.contract.functions.set_transfer_gas(260000).transact(tx_args(owner, gas=50000))
    assert status(tx_hash)
    tx_hash = web3_2.eth.sendTransaction({"from": ether_sender,
                                          "to": syndicatev2.contract.address,
                                          "value": web3_2.toWei(5, "ether"),
                                          "gas": 500000})
    assert status(tx_hash)
    print(str(type(from_addr)) + "\n" + str(type(to_addr)) + "\n" + str(type(token_id)) + "\n")
    tx_hash = syndicatev2.contract.functions.transferFrom(from_addr, to_addr, token_id).transact(tx_args(current_tx_sender, gas=1000000))
    return status(tx_hash)
  return inner_transfer_from

@pytest.fixture
def set_approval_for_all(status, deploy, syndicatev2, owner):
  def inner_set_approval_for_all(operator, value):
    deploy(syndicatev2, "Syndicatev2", 5000000)
    tx_hash = syndicatev2.contract.functions.setApprovalForAll(operator, value).transact(tx_args(owner, gas=1000000))
    return status(tx_hash)
  return inner_set_approval_for_all


def test_deployment_raises_error_with_intrinsic_gas_too_low(deployment_status):
  with pytest.raises(ValueError):
    deployment_status(50000)

def test_deployment_fails_with_not_enough_gas(deployment_status):
  assert deployment_status(500000) == 0

def test_deployment_succeeds_with_enough_gas(deployment_status):
  assert deployment_status(9000000)

@pytest.mark.parametrize("current_owner", ["owner", "not_owner"])
def test_set_transfer_gas(set_transfer_gas, current_owner, owner, request):
  current_owner = request.getfixturevalue(current_owner)
  if current_owner == owner:
    assert set_transfer_gas(current_owner)
  else:
    assert set_transfer_gas(current_owner) == 0

def test_there_is_no_token_balance_of_contract_after_sending_ether(get_balance_after_sending_ether):
  assert get_balance_after_sending_ether() == 0

@pytest.mark.parametrize("token_address", ["eip20token_address", "address_zero"])
@pytest.mark.parametrize("current_owner", ["owner", "not_owner"])
def test_update_token(request, update_token, current_owner, token_address, owner, address_zero):
  current_owner = request.getfixturevalue(current_owner)
  token_address = request.getfixturevalue(token_address)
  if current_owner == owner and token_address != address_zero:
    assert update_token(current_owner, token_address)
  else:
    assert update_token(current_owner, token_address) == 0

@pytest.mark.parametrize("current_owner", ["owner", "not_owner"])
def test_set_enforce_whitelist(request, set_enforce_whitelist, current_owner, owner):
  current_owner = request.getfixturevalue(current_owner)
  if current_owner == owner:
    assert set_enforce_whitelist(current_owner, True)
  else:
    assert set_enforce_whitelist(current_owner, True) == 0

@pytest.mark.parametrize("current_owner", ["owner", "not_owner"])
def test_whitelist(request, whitelist, current_owner, owner):
  current_owner = request.getfixturevalue(current_owner)
  if current_owner == owner:
    assert whitelist(current_owner, True)
  else:
    assert whitelist(current_owner, True) == 0

@pytest.mark.parametrize("current_sender", ["ether_sender", "not_ether_sender"])
def test_withdraw_tokens(request, withdraw_tokens, current_sender, ether_sender):
  current_sender = request.getfixturevalue(current_sender)
  if current_sender == ether_sender:
    assert withdraw_tokens(current_sender)
  else:
    assert 0 == withdraw_tokens(current_sender)

def test_sending_ether(send_ether, ether_sender):
  assert send_ether(ether_sender)

@pytest.mark.parametrize("current_owner", ["owner", "not_owner"])
def test_emergency_withdraw(request, emergency_withdraw, current_owner, owner):
  current_owner = request.getfixturevalue(current_owner)
  if current_owner == owner:
    assert emergency_withdraw(current_owner)
  else:
    assert emergency_withdraw(current_owner) == 0

@pytest.mark.parametrize("from_addr", ["ether_sender", "not_ether_sender"])
@pytest.mark.parametrize("current_tx_sender", ["ether_sender", "not_ether_sender"])
def test_transfer_from(request, from_addr, current_tx_sender, owner, ether_sender, transfer_from):
  token_id = 0
  to_addr = owner
  current_tx_sender = request.getfixturevalue(current_tx_sender)
  if current_tx_sender == ether_sender and from_addr == ether_sender:
    assert transfer_from(from_addr, to_addr, token_id, current_tx_sender)
  else:
    assert transfer_from(from_addr, to_addr, token_id, current_tx_sender) == 0

def test_set_approval_for_all(set_approval_for_all, ether_sender):
  assert set_approval_for_all(ether_sender, True)