#!/usr/bin/env python3

import sys
from web3 import Web3, HTTPProvider, IPCProvider
import json
import os, errno
import time
from datetime import datetime
import rlp
from eth_utils import keccak, to_checksum_address

web3 = Web3(IPCProvider("/home/horacio/.dev/geth.ipc"))
# web3 = Web3(HTTPProvider("http://localhost:8545"))
eth = web3.eth
miner = web3.miner
accounts = eth.accounts
gwei = 1000000000


contract_name = "PinProtocolInvestment"
gas = 4600000
gas_price = 1 * gwei
deployer_account = accounts[0]


deployment_tx = {"from": deployer_account, "value": 0, "gas": gas, "gasPrice": gas_price}
address_log_path = "deployment_logs"
token_contract = None
token_address = None

# Get contract ABI
with open("./build/" + contract_name + ".abi") as contract_abi_file:
  contract_abi = json.load(contract_abi_file)

# Get contract Bytecode
with open("./build/" + contract_name + ".bin") as contract_bin_file:
  contract_bytecode = '0x' + contract_bin_file.read()

def generate_contract_address(address, nonce):
  return to_checksum_address('0x' + keccak(rlp.encode([bytes(bytearray.fromhex(address[2:])), nonce]))[-20:].hex())

deployer_nonce = eth.getTransactionCount(deployer_account)
contract_address = generate_contract_address(deployer_account, deployer_nonce)

# contract instance creation
contract = eth.contract(address=contract_address, abi=contract_abi, bytecode=contract_bytecode)

miner.start(1)

# contract contract deployment
deployment_tx_hash = contract.deploy(transaction=deployment_tx, args=None)

print("\n\ncontract address: " + contract_address + "\n")

block_number = eth.blockNumber
while eth.blockNumber <= (block_number + 2):
  time.sleep(1)

# Write json file with contract contract's address if it's a test -------------------------
if __name__ == '__main__':
  deployment_name = input('\n\nEnter name of deployment: ')
  
  local_time = datetime.now()
  
  json_file_name = deployment_name + "--" + local_time.strftime('%Y-%m-%d--%H-%M-%S') 
  
  try:
    if not os.path.exists(address_log_path):
      os.makedirs(address_log_path)
  except OSError as e:
    if e.errno != errno.EEXIST:
      raise
  
  # Writing configuration parameters into json file for logging purposes
  file_path_name_w_ext = address_log_path + '/' + json_file_name + '.json'
  address_for_file = {
    'deployment_tx_hash': deployment_tx_hash.hex(),
    'contract_address': contract_address
  }
  with open(file_path_name_w_ext, 'x') as fp:
    json.dump(address_for_file, fp, sort_keys=True, indent=2)