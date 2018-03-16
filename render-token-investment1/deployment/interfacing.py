#!/usr/bin/env python3

import sys
print(sys.version)
from web3 import Web3, HTTPProvider

eth = web3.eth

web3 = Web3(HTTPProvider('http://localhost:8545'))

with open("./build/" + contract_name + ".abi") as contract_abi_file:
  contract_abi = json.load(contract_abi_file)

with open("./build" + contract_name + ".bin") as contract_bin_file:
  contract_bin = "0x" + contract_bin_file.read()


