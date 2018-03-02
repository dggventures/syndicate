#!/home/horacio/web3py-env/bin/python3 -i

import sys
print(sys.version)
from web3 import Web3, HTTPProvider
import json
#import unlock
import os, errno
import time
from datetime import datetime

import rlp
from eth_utils import keccak, to_checksum_address

web3 = Web3(HTTPProvider('http://localhost:7999'))
eth = web3.eth
accounts = eth.accounts
address_log_path = "./address_log"

contract_name = "PinProtocolInvestment"

# Get contract ABI
with open("./build/" + contract_name + ".abi") as contract_abi_file:
  contract_abi = json.load(contract_abi_file)

# Get contract Bytecode
with open("./build/" + contract_name + ".bin") as contract_bin_file:
  contract_bytecode = '0x' + contract_bin_file.read()

def generate_contract_address(address, nonce):
  return to_checksum_address('0x' + keccak(rlp.encode([bytes(bytearray.fromhex(address[2:])), nonce]))[-20:].hex())

deployer_nonce = web3.eth.getTransactionCount(accounts[0])
contract_address = generate_contract_address(accounts[0], deployer_nonce)

# contract instance creation
contract = web3.eth.contract(address=contract_address, abi=contract_abi, bytecode=contract_bytecode)

deployment_tx = {"from": eth.accounts[0], "gas": 50000000, "gasPrice": 20000000000}

def receipt(tx_hash):
  return eth.getTransactionReceipt(tx_hash)

def status(tx_hash):
  print("Status:", eth.getTransactionReceipt(tx_hash)["status"])

d_hash = contract.deploy(transaction=deployment_tx)
# d_hash = contract.constructor.transact(deployment_tx)

def gas(tx_hash):
  return eth.getTransactionReceipt(tx_hash)["gasUsed"]

def addAddress():
  status(d_hash)
  contract.address = receipt(d_hash).contractAddress
  print(contract_name, contract.address)
  
def partners():
  partners = []
  partners.append(contract.call().investment_address())
  partners.append(contract.call().major_partner_address())
  partners.append(contract.call().minor_partner_address())
  return partners

def set_transfer_gas(gas_amount):
  contract.transact(tx()).set_transfer_gas(gas_amount)