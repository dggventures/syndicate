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
def multisig_sender(status, web3_2, owner, ether_sender):
  path = os.path.abspath("../../../../../../MultisigWallet/MultisigWallet/deployment/build")
  contract_abi, contract_bytecode = Contract.get_abi_and_bytecode(path, "MultiSigWallet")
  sender_nonce = web3_2.eth.getTransactionCount(owner)
  contract_address = Contract.generate_contract_address(owner, sender_nonce)
  multisig_wallet_contract = web3_2.eth.contract(address=contract_address, abi=contract_abi, bytecode=contract_bytecode)
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
def contract_from_address(web3_2):
  def inner_contract_from_address(address, contract_name, path):
    contract_abi, contract_bytecode = Contract.get_abi_and_bytecode(path, contract_name)
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
def withdraw_tokens(status, deploy, syndicatev2, ether_sender, owner, web3_2, contract_from_address, crowdsale_path):
  def inner_withdraw_tokens(current_sender):
    deploy(syndicatev2, "Syndicatev2", 5000000)
    tx_hash = syndicatev2.contract.functions.set_transfer_gas(2000000).transact(tx_args(owner, gas=900000))
    assert status(tx_hash)
    crowdsale_contract = contract_from_address(syndicatev2.contract.functions.purchase_address().call(), "Crowdsale", crowdsale_path)
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
def send_ether(status, deploy, syndicatev2, web3_2, owner, ether_sender):
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
    tx_hash = web3_2.eth.sendTransaction({"from": ether_sender,
                                          "to": syndicatev2.contract.address,
                                          "value": web3_2.toWei(amount, "ether"),
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
    print(from_addr + "\n" + to_addr + "\n" + str(token_id) + "\n")
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
def send_ether_and_verify(deploy, syndicatev2, owner, status, config, web3_2):
  def inner_send_ether_and_verify(current_sender):
    deploy(syndicatev2, "Syndicatev2", 5000000)
    data = ""
    data = data.encode()
    amount = 5
    wei_amount = web3_2.toWei(amount, "ether")
    tx_hash = syndicatev2.contract.functions.set_transfer_gas(260000).transact(tx_args(owner, gas=50000))
    assert status(tx_hash)
    if web3_2.isAddress(current_sender):
      tx_hash = web3_2.eth.sendTransaction({"from": current_sender,
                                            "to": syndicatev2.contract.address,
                                            "value": wei_amount,
                                            "gas": 500000})
    else:
      multisig_wallet_contract = current_sender
      tx_hash = multisig_wallet_contract.functions.submitTransaction(syndicatev2.contract.address,
                                                                     wei_amount,
                                                                     data).transact(tx_args(owner, gas=1500000))
      current_sender = current_sender.address
    assert status(tx_hash)
    nftoken_balance = syndicatev2.contract.functions.balanceOf(current_sender).call()
    assert nftoken_balance
    config_dict = config(int(datetime.now().timestamp()) + 6)
    tranches_amount = len(config_dict["tranches"]) // 4
    print(type(tranches_amount))
    tranches = range(tranches_amount)
    tokens_per_wei = config_dict["tranches"][4*tranches[0] + 3]
    major_fee = (wei_amount * 6) / (10 * 11)
    minor_fee = (wei_amount * 4) / (10 * 11)
    expected_erc20token_balance = (int(wei_amount - major_fee - minor_fee)) * tokens_per_wei
    token_id = syndicatev2.contract.functions.tokenOfOwnerByIndex(current_sender, 0).call()
    actual_erc20token_balance = syndicatev2.contract.functions.get_token_balance(token_id).call()
    print("Expected:", expected_erc20token_balance)
    print("Actual:", actual_erc20token_balance)
    return expected_erc20token_balance == actual_erc20token_balance
  return inner_send_ether_and_verify

@pytest.fixture
def send_ether_with_multisig_and_verify(deploy, syndicatev2, owner, status, web3_2, get_tx_receipt):
  def inner_send_ether_with_multisig_and_verify(multisig_wallet_contract):
    deploy(syndicatev2, "Syndicatev2", 5000000)
    data = ""
    data = data.encode()
    amount = 5
    wei_amount = web3_2.toWei(amount, "ether")
    tx_hash = syndicatev2.contract.functions.set_transfer_gas(2060000).transact(tx_args(owner, gas=50000))
    assert status(tx_hash)
    tx_hash = multisig_wallet_contract.functions.submitTransaction(syndicatev2.contract.address,
                                                                   wei_amount,
                                                                   data).transact(tx_args(owner, gas=15000000))
    assert status(tx_hash)
    # receipt = get_tx_receipt(tx_hash)
    # rich_logs_execution = multisig_wallet_contract.events.Execution(0).processReceipt(receipt)
    # rich_logs_submission = multisig_wallet_contract.events.Submission(0).processReceipt(receipt)
    # rich_logs_confirmation = multisig_wallet_contract.events.Confirmation(owner, 0).processReceipt(receipt)
    # rich_logs_executionfailure = multisig_wallet_contract.events.ExecutionFailure(0).processReceipt(receipt)
    # transactions = multisig_wallet_contract.functions.transactions(0).call()
    # print(receipt)
    # print(tx_hash.hex())
    # print(transactions)
    # print(rich_logs_execution)
    # print(rich_logs_submission)
    # print(rich_logs_confirmation)
    # print(rich_logs_executionfailure)
    # purchase_pool = syndicatev2.contract.functions.purchase_pool().call()
    # total_tokens = syndicatev2.contract.functions.total_tokens().call()
    # token_balance = syndicatev2.contract.functions.token_balance().call()
    # owneroftoken = syndicatev2.contract.functions.ownerOf(0).call()
    # totalsupply = syndicatev2.contract.functions.totalSupply().call()
    nftoken_balance = syndicatev2.contract.functions.balanceOf(multisig_wallet_contract.address).call()
    # print("Purchase Pool:", purchase_pool)
    # print("Total eip20tokens in Syndicatev2:", total_tokens)
    # print("Syndicatev2's eip20tokens balance:", token_balance)
    # print("Owner of NFToken 0:", owneroftoken)
    # print("Multisig Address:", multisig_wallet_contract.address)
    # print("Total supply of NFTokens:", totalsupply)
    # print("NFTokens balance of Multisig:", nftoken_balance)
    assert nftoken_balance
    major_fee = (wei_amount * 6) / (10 * 11)
    minor_fee = (wei_amount * 4) / (10 * 11)
    expected_erc20token_balance = (int(wei_amount - major_fee - minor_fee)) * 410
    token_id = syndicatev2.contract.functions.tokenOfOwnerByIndex(current_sender, 0).call()
    actual_erc20token_balance = syndicatev2.contract.functions.get_token_balance(token_id).call()
    print("Expected:", expected_erc20token_balance)
    print("Actual:", actual_erc20token_balance)
    return expected_erc20token_balance == actual_erc20token_balance
  return inner_send_ether_with_multisig_and_verify

# General test cases functions

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

def test_sending_ether_with_multisig_and_verify(send_ether_with_multisig_and_verify, multisig_sender):
  assert send_ether_with_multisig_and_verify(multisig_sender)