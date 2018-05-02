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
  "to": "0x56968ED69c4269eAaD419AF20a22c4C16f2F5005", 
  "value": int(105 * (10 ** (18-5))), 
  "gas": 150000, 
  "gasPrice": 3000000000
})
