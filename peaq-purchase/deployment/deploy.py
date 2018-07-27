#!/usr/bin/env python3

import sys
print(sys.version)
from web3 import Web3, HTTPProvider
import json
import os, errno

web3 = Web3(HTTPProvider('http://localhost:8545'))
deployer_address = "0x54d9249C776C56520A62faeCB87A00E105E8c9Dc"

contract_name = "PeaqPurchase"

# Get contract ABI
with open("./build/" + contract_name + ".abi") as contract_abi_file:
  contract_abi = json.load(contract_abi_file)

# Get contract Bytecode
with open("./build/" + contract_name + ".bin") as contract_bin_file:
  contract_bytecode = '0x' + contract_bin_file.read()

# contract instance creation
contract = web3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)

deployment_tx = { "from": deployer_address, "gas": 500000, "gasPrice": web3.toWei(3, "gwei") }

d_hash = contract.deploy(transaction=deployment_tx)
  
