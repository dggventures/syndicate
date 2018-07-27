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
def owner(unlocked_accounts):
  return unlocked_accounts[0]

@pytest.fixture(scope="session")
def not_owner(unlocked_accounts):
  return unlocked_accounts[1]

@pytest.fixture(scope="session")
def ether_sender(unlocked_accounts):
  return unlocked_accounts[2]

@pytest.fixture(scope="session")
def not_ether_sender(unlocked_accounts):
  return unlocked_accounts[3]

@pytest.fixture
def multisig_sender(status, web3, owner, ether_sender):
  path = os.path.abspath("../../../../../../MultisigWallet/MultisigWallet/deployment/build")
  contract_abi, contract_bytecode = Contract.get_abi_and_bytecode(path, "MultiSigWallet")
  sender_nonce = web3.eth.getTransactionCount(owner)
  contract_address = Contract.generate_contract_address(owner, sender_nonce)
  multisig_wallet_contract = web3.eth.contract(address=contract_address, abi=contract_abi, bytecode=contract_bytecode)
  tx_hash = multisig_wallet_contract.constructor([owner, ether_sender], 1).transact(transaction=tx_args(owner, gas=3900000))
  status(tx_hash)
  return multisig_wallet_contract

@pytest.fixture(scope="session")
def true():
  return True

@pytest.fixture(scope="session")
def false():
  return False

@pytest.fixture
def syndicatev2():
  return Contract()

@pytest.fixture
def crowdsale():
  return Contract()

@pytest.fixture
def contract_from_address(web3):
  def inner_contract_from_address(address, contract_name, path):
    contract_abi, contract_bytecode = Contract.get_abi_and_bytecode(path, contract_name)
    contract = web3.eth.contract(address=address, abi=contract_abi, bytecode=contract_bytecode)
    return contract
  return inner_contract_from_address

@pytest.fixture
def deployed_crowdsale(crowdsale, owner, config, status, crowdsale_path, web3):
  def inner_deployed_crowdsale():
    config_dict = config(int(datetime.now().timestamp()) + 3)
    tx_hash = crowdsale.deploy(crowdsale_path, "Crowdsale", tx_args(owner, gas=5000000), web3,)
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
def deploy(owner, address_zero, wait, deployed_crowdsale, web3):
  def inner_deploy(contract, contract_name, gas):
    crowdsale = deployed_crowdsale()
    token_address = crowdsale.contract.functions.token().call()
    assert token_address != address_zero
    assert crowdsale.contract.address != address_zero
    tx_hash = contract.deploy("../../build/",
                              contract_name,
                              tx_args(owner, gas=gas),
                              web3,
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
def withdraw_tokens(status, deploy, syndicatev2, ether_sender, owner, web3, contract_from_address, crowdsale_path):
  def inner_withdraw_tokens(current_sender):
    deploy(syndicatev2, "Syndicatev2", 5000000)
    tx_hash = syndicatev2.contract.functions.set_transfer_gas(2000000).transact(tx_args(owner, gas=900000))
    assert status(tx_hash)
    crowdsale_contract = contract_from_address(syndicatev2.contract.functions.purchase_address().call(), "Crowdsale", crowdsale_path)
    tx_hash = crowdsale_contract.functions.setTransferAgent(syndicatev2.contract.address, True).transact(tx_args(owner, gas=900000))
    assert status(tx_hash)
    tx_hash = web3.eth.sendTransaction({"from": ether_sender,
                                          "to": syndicatev2.contract.address,
                                          "value": web3.toWei(5, "ether"),
                                          "gas": 2000000})
    assert status(tx_hash)
    tx_hash = syndicatev2.contract.functions.withdraw_tokens().transact(tx_args(current_sender, gas=1900000))
    return status(tx_hash)
  return inner_withdraw_tokens

@pytest.fixture
def send_ether(status, deploy, syndicatev2, web3, owner, ether_sender):
  def inner_send_ether(enforce_whitelist, whitelisted, transfer_amount, gas, purchase_active):
    deploy(syndicatev2, "Syndicatev2", 5000000)
    if gas:
      tx_hash = syndicatev2.contract.functions.set_transfer_gas(260000).transact(tx_args(owner, gas=50000))
      assert status(tx_hash)
    if enforce_whitelist:
      tx_hash = syndicatev2.contract.functions.set_enforce_whitelist(True).transact(tx_args(owner, gas=50000))
      assert status(tx_hash)
    if transfer_amount:
      amount = 5
    else:
      amount = 0
    if whitelisted:
      tx_hash = syndicatev2.contract.functions.whitelist(ether_sender, True).transact(tx_args(owner, gas=50000))
      assert status(tx_hash)
    if not purchase_active:
      tx_hash = syndicatev2.contract.functions.set_purchasing_availability(False).transact(tx_args(owner, gas=50000))
      assert status(tx_hash)
    tx_hash = web3.eth.sendTransaction({"from": ether_sender,
                                          "to": syndicatev2.contract.address,
                                          "value": web3.toWei(amount, "ether"),
                                          "gas": 500000})
    return status(tx_hash)
  return inner_send_ether

@pytest.fixture
def transfer_from(status, deploy, syndicatev2, ether_sender, web3, owner):
  def inner_transfer_from(from_addr, to_addr, token_id, current_tx_sender):
    deploy(syndicatev2, "Syndicatev2", 5000000)
    tx_hash = syndicatev2.contract.functions.set_transfer_gas(260000).transact(tx_args(owner, gas=50000))
    assert status(tx_hash)
    tx_hash = web3.eth.sendTransaction({"from": ether_sender,
                                          "to": syndicatev2.contract.address,
                                          "value": web3.toWei(5, "ether"),
                                          "gas": 500000})
    assert status(tx_hash)
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


@pytest.fixture
def send_ether_and_verify(deploy, syndicatev2, owner, status, config, web3):
  def inner_send_ether_and_verify(current_sender):
    deploy(syndicatev2, "Syndicatev2", 5000000)
    data = "".encode()
    amount = 5
    wei_amount = web3.toWei(amount, "ether")
    tx_hash = syndicatev2.contract.functions.set_transfer_gas(2000000).transact(tx_args(owner, gas=50000))
    assert status(tx_hash)
    if web3.isAddress(current_sender):
      tx_hash = web3.eth.sendTransaction({"from": current_sender,
                                          "to": syndicatev2.contract.address,
                                          "value": wei_amount,
                                          "gas": 5000000})
    else:
      multisig_wallet_contract = current_sender
      tx_hash = web3.eth.sendTransaction({"from": owner,
                                          "to": multisig_wallet_contract.address,
                                          "value": wei_amount * 2,
                                          "gas": 5000000})
      assert status(tx_hash)
      tx_hash = multisig_wallet_contract.functions.submitTransaction(syndicatev2.contract.address,
                                                                     wei_amount,
                                                                     data).transact(tx_args(owner, gas=5000000))
      current_sender = current_sender.address
    assert status(tx_hash)
    nftoken_balance = syndicatev2.contract.functions.balanceOf(current_sender).call()
    assert nftoken_balance
    config_dict = config(int(datetime.now().timestamp()) + 6)
    tranches_amount = len(config_dict["tranches"]) // 4
    tranches = range(tranches_amount)
    tokens_per_wei = config_dict["tranches"][4*tranches[0] + 3]
    major_fee = (wei_amount * 6) // (10 * 11)
    minor_fee = (wei_amount * 4) // (10 * 11)
    expected_erc20token_balance = (wei_amount - major_fee - minor_fee) * tokens_per_wei
    token_id = syndicatev2.contract.functions.tokenOfOwnerByIndex(current_sender, 0).call()
    actual_erc20token_balance = syndicatev2.contract.functions.get_token_balance(token_id).call()
    print("Expected:", expected_erc20token_balance)
    print("  Actual:", actual_erc20token_balance)
    assert expected_erc20token_balance == actual_erc20token_balance
    balance = web3.fromWei(web3.eth.getBalance(syndicatev2.contract.address), "ether")
    return not balance
  return inner_send_ether_and_verify

@pytest.fixture
def withdraw_tokens_just_once(status, deploy, syndicatev2, ether_sender, owner, web3, contract_from_address, crowdsale_path):
  def inner_withdraw_tokens_just_once(current_sender):
    deploy(syndicatev2, "Syndicatev2", 5000000)
    tx_hash = syndicatev2.contract.functions.set_transfer_gas(2000000).transact(tx_args(owner, gas=900000))
    assert status(tx_hash)
    crowdsale_contract = contract_from_address(syndicatev2.contract.functions.purchase_address().call(), "Crowdsale", crowdsale_path)
    crowdsale_token_contract = contract_from_address(crowdsale_contract.functions.token().call(), "CrowdsaleToken", crowdsale_path)
    tx_hash = crowdsale_contract.functions.setTransferAgent(syndicatev2.contract.address, True).transact(tx_args(owner, gas=900000))
    assert status(tx_hash)
    tx_hash = web3.eth.sendTransaction({"from": ether_sender,
                                          "to": syndicatev2.contract.address,
                                          "value": web3.toWei(5, "ether"),
                                          "gas": 2000000})
    assert status(tx_hash)
    tx_hash = syndicatev2.contract.functions.withdraw_tokens().transact(tx_args(current_sender, gas=1900000))
    assert status(tx_hash)
    token_id = syndicatev2.contract.functions.tokenOfOwnerByIndex(current_sender, 0).call()
    balance = syndicatev2.contract.functions.get_token_balance(token_id).call()
    assert not balance
    token_balance_before_second_withdrawal = crowdsale_token_contract.functions.balanceOf(current_sender).call()
    tx_hash = syndicatev2.contract.functions.withdraw_tokens().transact(tx_args(current_sender, gas=1900000))
    assert status(tx_hash)
    token_balance_after_second_withdrawal = crowdsale_token_contract.functions.balanceOf(current_sender).call()
    return token_balance_after_second_withdrawal - token_balance_before_second_withdrawal
  return inner_withdraw_tokens_just_once


# General test cases functions

def test_deployment_raises_error_with_intrinsic_gas_too_low(deployment_status):
  with pytest.raises(ValueError):
    deployment_status(50000)

def test_deployment_fails_with_not_enough_gas(deployment_status):
  assert deployment_status(1000000) == 0

def test_deployment_succeeds_with_enough_gas(deployment_status):
  assert deployment_status(9000000)

@pytest.mark.parametrize("current_owner", ["owner", "not_owner"])
def test_set_transfer_gas(set_transfer_gas, current_owner, owner, request):
  current_owner = request.getfixturevalue(current_owner)
  if current_owner == owner:
    assert set_transfer_gas(current_owner)
  else:
    assert set_transfer_gas(current_owner) == 0

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

@pytest.mark.parametrize("enforce_whitelist", ["true", "false"])
@pytest.mark.parametrize("whitelisted", ["true", "false"])
@pytest.mark.parametrize("transfer_amount", ["true", "false"])
@pytest.mark.parametrize("gas", ["true", "false"])
@pytest.mark.parametrize("purchase_active", ["true", "false"])
def test_sending_ether(request, send_ether, enforce_whitelist, whitelisted, transfer_amount, gas, purchase_active):
  enforce_whitelist = request.getfixturevalue(enforce_whitelist)
  whitelisted = request.getfixturevalue(whitelisted)
  transfer_amount = request.getfixturevalue(transfer_amount)
  gas = request.getfixturevalue(gas)
  purchase_active = request.getfixturevalue(purchase_active)
  if (not enforce_whitelist or whitelisted) and transfer_amount and gas and purchase_active:
    assert send_ether(enforce_whitelist, whitelisted, transfer_amount, gas, purchase_active)
  else:
    assert 0 == send_ether(enforce_whitelist, whitelisted, transfer_amount, gas, purchase_active)

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
  from_addr = request.getfixturevalue(from_addr)
  if current_tx_sender == ether_sender and from_addr == ether_sender:
    assert transfer_from(from_addr, to_addr, token_id, current_tx_sender)
  else:
    assert transfer_from(from_addr, to_addr, token_id, current_tx_sender) == 0

def test_set_approval_for_all(set_approval_for_all, ether_sender):
  assert set_approval_for_all(ether_sender, True)


# Test functions for the doc's special cases

@pytest.mark.parametrize("current_sender", ["ether_sender", "multisig_sender"])
def test_sending_ether_and_verification(request, send_ether_and_verify, current_sender):
  current_sender = request.getfixturevalue(current_sender)
  assert send_ether_and_verify(current_sender)

def test_withdraw_tokens_just_once(withdraw_tokens_just_once, ether_sender):
  assert withdraw_tokens_just_once(ether_sender) == 0