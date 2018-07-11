#!/usr/bin/env python3

import pytest
import sys
sys.path.append("../../../deployment")
from contract import Contract
from tx_args import tx_args
import os
from client_config import config_f


@pytest.fixture
def config():
  return config_f()

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
def crowdsale():
  return Contract()

@pytest.fixture
def deployed_crowdsale(crowdsale, wait, owner, config):
  def inner_deployed_crowdsale():
    crowdsale_path = os.path.abspath("../../../../../../ICOSample/ICOSample/deployment/build")
    tx_hash = crowdsale.deploy(crowdsale_path, "Crowdsale", tx_args(owner, gas=5000000),)
    wait(tx_hash)
    tx_hash = crowdsale.contract.functions.configurationCrowdsale(config["MW_address"],
                                                                  config["start_time"],
                                                                  config["end_time"],
                                                                  config["token_retriever_account"],
                                                                  config["tranches"],
                                                                  config["multisig_supply"],
                                                                  config["crowdsale_supply"],
                                                                  config["token_decimals"],
                                                                  config["max_tokens_to_sell"]
                                                                  ).transact(tx_args(owner, gas=6000000))
    wait(tx_hash)
    return crowdsale
  return inner_deployed_crowdsale

@pytest.fixture
def deploy(wait, owner):
  def inner_deploy(contract, contract_name, gas, deployed_crowdsale):
    crowdsale = deployed_crowdsale()
    token_address = crowdsale.contract.functions.token().call()
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
def deployment_status(syndicatev2, deploy, status, deployed_crowdsale):
  def inner_deployment_status(gas):
    return status(deploy(syndicatev2, "Syndicatev2", gas, deployed_crowdsale))
  return inner_deployment_status


@pytest.fixture
def set_transfer_gas(status, deploy, syndicatev2, deployed_crowdsale):
  def inner_set_transfer_gas(current_owner):
    gas = 200000
    deploy(syndicatev2, "Syndicatev2", 5000000, deployed_crowdsale)
    tx_hash = syndicatev2.contract.functions.set_transfer_gas(gas).transact(tx_args(current_owner, gas=300000))
    return status(tx_hash)
  return inner_set_transfer_gas

@pytest.fixture
def get_balance(deploy, syndicatev2, web3_2, status, owner, deployed_crowdsale, get_tx_receipt):
  def inner_get_balance():
    deploy(syndicatev2, "Syndicatev2", 3000000, deployed_crowdsale)
    tx_hash = syndicatev2.contract.functions.whitelist(web3_2.eth.accounts[0], True).transact(tx_args(owner, gas=900000))
    assert status(tx_hash)
    tx_hash = web3_2.eth.sendTransaction({"from": web3_2.eth.accounts[0],
                                          "to": syndicatev2.contract.address,
                                          "value": web3_2.toWei(5, "ether"),
                                          "gas": 30000})
    print(get_tx_receipt(tx_hash).gasUsed)
    assert status(tx_hash)
    balance = web3_2.fromWei(web3_2.eth.getBalance(syndicatev2.contract.address), "ether")
    print(balance)
    return balance
  return inner_get_balance


def test_deployment_failed_with_intrinsic_gas_too_low(deployment_status):
  with pytest.raises(ValueError):
    deployment_status(50000)

def test_deployment_successful_with_not_enough_gas(deployment_status):
  assert deployment_status(1800000) == 0

def test_deployment_successful_with_enough_gas(deployment_status):
  assert deployment_status(9000000) == 1

@pytest.mark.parametrize("current_owner", ["owner", "not_owner"])
def test_both_cases_of_set_transfer_gas(set_transfer_gas, current_owner, owner, request):
  current_owner = request.getfixturevalue(current_owner)
  if current_owner == owner:
    assert set_transfer_gas(current_owner) == 1
  else:
    assert set_transfer_gas(current_owner) == 0

def test_there_is_contract_balance_after_sending_ether(get_balance):
  assert get_balance() == 5
