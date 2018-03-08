#!/usr/bin/python3 -i

import time
from web3 import Web3, IPCProvider
import json
import glob
import os

gas = 50000000
gas_price = 20000000000

# Change ipcPath if needed
ipc_path = '/home/coinfabrik/Programming/blockchain/node/geth.ipc'
# web3.py instance
web3 = Web3(IPCProvider(ipc_path))
miner = web3.miner
accounts = web3.eth.accounts
sender_account = accounts[0]

# Get Syndicatev2 ABI
with open("../build/Syndicatev2.abi") as contract_abi_file:
	syndicate_abi = json.load(contract_abi_file)

# Get Syndicatev2 Bytecode
with open("../build/Syndicatev2.bin") as contract_bin_file:
	syndicate_bytecode = '0x' + contract_bin_file.read()

file_list = glob.glob('../address_log/*')
latest_file = max(file_list, key=os.path.getctime)

# Get Syndicatev2 address
with open(latest_file) as contract_address_file:
	syndicate_address_json = json.load(contract_address_file)

syndicate_address = syndicate_address_json['syndicate_address']

# Syndicatev2 instance creation
syndicate_contract = web3.eth.contract(address=syndicate_address, abi=syndicate_abi, bytecode=syndicate_bytecode)


# Custom functions-------------------------------------------------------------------------
def buy(from_address, to_address, value):
	return status(web3.eth.sendTransaction(transaction_info(from_address, to_address, value)))

def get_transaction_receipt(tx_hash):
	status_deploy_crowdsale = status(tx_hash)
	if status_deploy_crowdsale == 1:
		return web3.eth.getTransactionReceipt(tx_hash)
	else:
		print("Unsuccessful Transaction")

def status(tx_receipt):
	wait()
	return web3.eth.getTransactionReceipt(tx_receipt).status

# Transaction parameter
def transaction_info(sender, receiver=None, value=0):
	return {"from": sender, "to": receiver, "value": value*(10**18), "gas": gas, "gasPrice": gas_price}

def wait():
	block_number = web3.eth.blockNumber
	while web3.eth.blockNumber <= (block_number + 2):
		time.sleep(1)

# Crowdsale Contract's functions-----------------------------------------------------------
def approve_unwanted_tokens(token, dest, value):
	return status(syndicate_contract.functions.approve_unwanted_tokens(token, dest, value).transact(transaction_info(sender_account)))

def emergency_withdraw():
	return status(syndicate_contract.functions.emergency_withdraw().transact(transaction_info(sender_account)))

def set_transfer_gas(transfer_gas): 
	return status(syndicate_contract.functions.set_transfer_gas(transfer_gas).transact(transaction_info(sender_account)))

def token_balance(investor):
	return syndicate_contract.functions.token_balance(investor).call()

def update_balances(token):
	return status(syndicate_contract.functions.update_balances().transact(transaction_info(sender_account)))

def update_token(token):
	return status(syndicate_contract.functions.update_token(token).transact(transaction_info(sender_account)))

def whitelist(investor, allowed):
	return status(syndicate_contract.functions.whitelist(investor, allowed).transact(transaction_info(sender_account)))

def withdraw_tokens_approve():
	return status(syndicate_contract.functions.withdraw_tokens_approve().transact(transaction_info(sender_account)))

def withdraw_tokens_transfer():
	return status(syndicate_contract.functions.withdraw_tokens_transfer().transact(transaction_info(sender_account)))

