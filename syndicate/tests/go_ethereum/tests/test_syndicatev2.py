#!/usr/bin/env python3

import pytest
import sys
sys.path.append("../../../deployment")
from contract import Contract
from tx_args import tx_args
import os
from client_config import config_f


ADDRESS_ZERO = "0x0000000000000000000000000000000000000000"

@pytest.fixture
def crowdsale_path():
  return os.path.abspath("../../../../../../ICOSample/ICOSample/deployment/build")

@pytest.fixture
def address_zero():
  return ADDRESS_ZERO

@pytest.fixture
def config():
  return config_f()

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
def deployed_crowdsale(crowdsale, owner, config, status, crowdsale_path):
  def inner_deployed_crowdsale():
    tx_hash = crowdsale.deploy(crowdsale_path, "Crowdsale", tx_args(owner, gas=5000000),)
    assert status(tx_hash)
    tx_hash = crowdsale.contract.functions.configurationCrowdsale(config["MW_address"],
                                                                  config["start_time"],
                                                                  config["end_time"],
                                                                  config["token_retriever_account"],
                                                                  config["tranches"],
                                                                  config["multisig_supply"],
                                                                  config["crowdsale_supply"],
                                                                  config["token_decimals"],
                                                                  config["max_tokens_to_sell"]
                                                                  ).transact(tx_args(owner, gas=9000000))
    assert status(tx_hash)
    return crowdsale
  return inner_deployed_crowdsale

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
def get_balance(deploy, syndicatev2, web3_2, status, owner):
  def inner_get_balance():
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
  return inner_get_balance

@pytest.fixture
def real_eip20token_address(standard_token, crowdsale_path, not_owner, status):
  tx_hash = standard_token.deploy(crowdsale_path, "StandardToken", tx_args(not_owner, gas=5000000),)
  assert status(tx_hash)
  token_address = standard_token.contract.address
  return token_address

@pytest.fixture
def update_token(status, deploy, syndicatev2):
  def inner_update_token(current_owner, token):
    deploy(syndicatev2, "Syndicatev2", 5000000)
    print("\nFirst token address during update_token:", syndicatev2.contract.functions.token().call())
    print("\nToken address I am trying to update to:", token)
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
    print("THE ASSERT OF THE PURCHASE IS PASSING")
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


def test_deployment_raises_error_with_intrinsic_gas_too_low(deployment_status):
  with pytest.raises(ValueError):
    deployment_status(50000)

def test_deployment_fails_with_not_enough_gas(deployment_status):
  assert deployment_status(500000) == 0

def test_deployment_succeeds_with_enough_gas(deployment_status):
  assert deployment_status(9000000)

@pytest.mark.parametrize("current_owner", ["owner", "not_owner"])
def test_both_cases_of_set_transfer_gas(set_transfer_gas, current_owner, owner, request):
  current_owner = request.getfixturevalue(current_owner)
  if current_owner == owner:
    assert set_transfer_gas(current_owner)
  else:
    assert set_transfer_gas(current_owner) == 0

def test_there_is_no_token_balance_of_contract_after_sending_ether(get_balance):
  assert get_balance() == 0

@pytest.mark.parametrize("token_address", ["real_eip20token_address", "address_zero"])
@pytest.mark.parametrize("current_owner", ["owner", "not_owner"])
def test_all_cases_of_update_token(request, update_token, current_owner, token_address, owner, address_zero):
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

def test_one_withdraw_tokens(withdraw_tokens, ether_sender):
  assert withdraw_tokens(ether_sender)

def test_one_send_ether(send_ether, ether_sender):
  assert send_ether(ether_sender)