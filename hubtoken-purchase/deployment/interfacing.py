#!/usr/bin/env python3

import sys
import json
print(sys.version)
from web3 import Web3, HTTPProvider

web3 = Web3(HTTPProvider('http://localhost:8545'))

eth = web3.eth

contract_name = "HubTokenPurchase"

with open("./build/" + contract_name + ".abi") as contract_abi_file:
  contract_abi = json.load(contract_abi_file)

with open("./build/" + contract_name + ".bin") as contract_bin_file:
  contract_bin = "0x" + contract_bin_file.read()


eth.sendTransaction({
  "from": "0x54d9249C776C56520A62faeCB87A00E105E8c9Dc", 
  "to": "0xe14EaC83B3bB1Bb7B265Bf298C348264f8399834", 
  "value": int(1035 * (10 ** (18-6))), 
  "gas": 150000, 
  "gasPrice": 3000000000
})
