#!/home/horacio/web3py-env/bin/python3 -i

import sys
print(sys.version)
from web3 import Web3, HTTPProvider

eth = web3.eth

with open("./build/" + contract_name + ".bin") as contract_abi_file:
  contract_abi = json.load(contract_abi_file)

with open("./build" + contract_name + ".bin") as contract_bytecode_file:
  contract_bytecode = "0x" + contract_bytecode_file.read()


