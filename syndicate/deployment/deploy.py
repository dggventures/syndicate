#!/usr/bin/python3 -i

from web3 import Web3, IPCProvider
import json
from address import generate_contract_address
import unlock
import os, errno
import time
from datetime import datetime

# Change ipcPath if needed
ipc_path = '/home/coinfabrik/Programming/blockchain/node/geth.ipc'
# web3.py instance
web3 = Web3(IPCProvider(ipc_path))
miner = web3.miner

accounts = web3.eth.accounts
sender_account = accounts[0]
gas = 50000000
gas_price = 20000000000
address_log_path = "../address_log"
unlock.web3 = web3

def wait():
  block_number = web3.eth.blockNumber
  while web3.eth.blockNumber <= (block_number + 2):
    time.sleep(1)

# Unlock accounts
unlock.unlock()

miner.start(1)

# Deployment of StandardToken

# Get Token ABI
with open("../build/StandardToken.abi") as contract_abi_file:
  token_abi = json.load(contract_abi_file)

# Get Token Bytecode
with open("../build/StandardToken.bin") as contract_bin_file:
  token_bytecode = '0x' + contract_bin_file.read()

nonce_token = web3.eth.getTransactionCount(sender_account)
token_address = generate_contract_address(sender_account, nonce_token)

# Token instance creation
token_contract = web3.eth.contract(address=token_address, abi=token_abi, bytecode=token_bytecode)

# Token contract deployment
tx_hash_token = token_contract.deploy(transaction={"from": sender_account, "value": 0, "gas": gas, "gasPrice": gas_price}, args=None)


wait()


# Deployment of Syndicatev2

# Get Syndicatev2 ABI
with open("../build/Syndicatev2.abi") as contract_abi_file:
  syndicate_abi = json.load(contract_abi_file)

# Get Syndicatev2 Bytecode
with open("../build/Syndicatev2.bin") as contract_bin_file:
  syndicate_bytecode = '0x' + contract_bin_file.read()

nonce_syndicate = web3.eth.getTransactionCount(sender_account)
syndicate_address = generate_contract_address(sender_account, nonce_syndicate)

# Syndicatev2 instance creation
syndicate_contract = web3.eth.contract(address=syndicate_address, abi=syndicate_abi, bytecode=syndicate_bytecode)


# Syndicatev2 contract deployment
tx_hash_syndicate = syndicate_contract.deploy(transaction={"from": sender_account, "value": 0, "gas": gas, "gasPrice": gas_price}, args=[token_address, '0x77D0f9017304e53181d9519792887E78161ABD25', '0x8f0592bDCeE38774d93bC1fd2c97ee6540385356', '0xC787C3f6F75D7195361b64318CE019f90507f806'])

print("\n\nSyndicatev2 address: " + syndicate_address + "\n")


wait()


# Write json file with Syndicatev2 contract's address if it's a test -------------------------
if __name__ != '__main__':
  deployment_name = input('\n\nEnter name of deployment: ')
  
  local_time = datetime.now()
  
  json_file_name = "Syndicatev2-Address" + '--' + local_time.strftime('%Y-%m-%d--%H-%M-%S') + '--' + deployment_name
  
  try:
    if not os.path.exists(address_log_path):
      os.makedirs(address_log_path)
  except OSError as e:
    if e.errno != errno.EEXIST:
      raise
  
  # Writing configuration parameters into json file for logging purposes
  file_path_name_w_ext = address_log_path + '/' + json_file_name + '.json'
  address_for_file = {'syndicate_address': syndicate_address}
  with open(file_path_name_w_ext, 'w') as fp:
    json.dump(address_for_file, fp, sort_keys=True, indent=2)
# ------------------------------------------------------------------------------------------
