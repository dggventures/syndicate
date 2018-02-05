#!/usr/bin/python3 -i
from web3 import Web3, HTTPProvider
import json

web3 = Web3(HTTPProvider('http://localhost:8545'))

eth = web3.eth

contract_name = "MainframeInvestment"

with open("build/" + contract_name + ".abi") as contract_abi_file:
  contract_abi = json.load(contract_abi_file)

#Comes as string without '0x'
contract_bin = open("build/" + contract_name + ".bin").read()
contract = eth.contract(contract_abi, bytecode=("0x" + contract_bin))

def trans():
  return {"from": "0x54d9249c776c56520a62faecb87a00e105e8c9dc", "gas": 800000, "gasPrice": 3000000000}

dHash = contract.deploy(transaction=trans(0,0))

def receipt(tx_hash):
  return eth.getTransactionReceipt(tx_hash)

def status(tx_hash):
  print("Status:", eth.getTransactionReceipt(tx_hash)["status"])

def gas(tx_hash):
  return eth.getTransactionReceipt(tx_hash)["gasUsed"]

def addAddress():
  status(dHash)
  contract.address = receipt(dHash).contractAddress
  print(contract_name, contract.address)
  
def partners():
  partners = []
  partners.append(contract.call().investment_address())
  partners.append(contract.call().major_partner_address())
  partners.append(contract.call().minor_partner_address())
  return partners

def set_transfer_gas(gas_amount):
  contract.transact(trans()).set_transfer_gas(gas_amount)

