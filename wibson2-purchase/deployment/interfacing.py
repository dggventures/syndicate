#!/usr/bin/env python3

import sys
import json
print(sys.version)
from web3 import Web3, HTTPProvider

web3 = Web3(HTTPProvider('http://localhost:8545'))

# contract_name = "Wibson2Purchase"

# with open("./build/" + contract_name + ".abi") as contract_abi_file:
#   contract_abi = json.load(contract_abi_file)

# with open("./build/" + contract_name + ".bin") as contract_bin_file:
#   contract_bin = "0x" + contract_bin_file.read()

web3.eth.sendTransaction({
  "from": "0x54d9249C776C56520A62faeCB87A00E105E8c9Dc", 
  "to": "0xBAcF8282704CB4Db50F2459Db29f2e3C7cF181D8", 
  "value": web3.toWei(0.1, "milliether"), 
  "gas": 100000, 
  "gasPrice": web3.toWei(50, "gwei")
})
