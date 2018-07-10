import contextlib
import os
import shutil
import signal
import socket
import subprocess
import time
import json

from eth_utils import (
    is_checksum_address,
)

KEYFILE_PW = 'cuentahoracio0'

KEYFILES = (
  { "data": { "address": "a1aa59f3980144daebd2252c709c997c880bc324", 
              "crypto": { "cipher": "aes-128-ctr",
                          "ciphertext": "fc9c679e400498e1bbc7824f54e85d0e47c3ec5b4b44fc44d9d350c7be2c55a4",
                          "cipherparams": { "iv": "26eee096919ef15418860ab62049de69" },
                          "kdf": "scrypt",
                          "kdfparams": { "dklen": 32, "n": 262144, "p": 1, "r": 8, "salt": "c43bed3628f6c7607e73d206d1de81140f0dd710c23e27afc823e0e27412191b" },
                          "mac": "69ab4297bb1fe94c33929b6837e9c1d8bd2321a5ccd4c380bc5fc0d3b3bae9c6" },
              "id": "575069fd-465e-4202-b293-1e695ad7ad7e",
              "version": 3 },
    "filename": "UTC--2017-11-30T16-48-34.139783653Z--a1aa59f3980144daebd2252c709c997c880bc324" },

  { "data": { "address": "1985e936fc36eabe24f9100517b13f7026ec938c",
              "crypto": { "cipher": "aes-128-ctr",
                          "ciphertext": "320e17ce7cf83d04aa306a77e0fa01f3d537e5656a2c6d87e9cb938358639556",
                          "cipherparams": { "iv": "12fff6ffd91f048e6f3a793e2050c3ac" },
                          "kdf": "scrypt",
                          "kdfparams": { "dklen": 32, "n": 262144, "p": 1, "r": 8, "salt": "324e3b9d2a8266677e0cd5c13b0a0e9b97c2630996a6c65061245fc260926e9d" },
                          "mac": "69fabe831f9d476aba5201fbe3a985ed366ee01e79c5df21907cda462128e348" },
              "id": "b40e900f-2656-439e-ad6e-f5657a9a28af",
              "version": 3 },
    "filename": "UTC--2017-11-30T16-48-35.523249426Z--1985e936fc36eabe24f9100517b13f7026ec938c" },

  { "data": { "address": "45fc200f79b6ed7c424ef1d6d623797d13c4a813",
              "crypto": { "cipher": "aes-128-ctr",
                          "ciphertext": "9783aabc5f977a4e41ac7bce4e17765bf6e0df22f0d265201fff4fde9abc2bd6",
                          "cipherparams": { "iv": "b471e79c710a3bbf5d66e7c098f89ce0" },
                          "kdf": "scrypt",
                          "kdfparams": { "dklen": 32, "n": 262144, "p": 1, "r": 8, "salt": "d7b352b0112326fb46676777f4e127c5cdc0fc8f2f3530f9b8fca29267affb87" },
                          "mac": "fa83fc489ee540e7170fdc18f0d3f00375be777564b72e65b10abea9e66a41d2" },
              "id": "0234d6cc-a33e-47bf-8fed-2cd28f19f9ac",
              "version": 3 },
    "filename": "UTC--2017-11-30T16-48-36.715322533Z--45fc200f79b6ed7c424ef1d6d623797d13c4a813" },

  { "data": { "address": "dd72c8f99e53fbe343eae4efcee31f720e08568f",
              "crypto": { "cipher": "aes-128-ctr",
                          "ciphertext": "6388b7a0d7e6bca88236cb5878d1aea7bb86e24d9eb00093a5193b66a3d41012",
                          "cipherparams": { "iv": "67e3ef63eddcb45f6c5b87243470511c" },
                          "kdf": "scrypt",
                          "kdfparams": { "dklen": 32, "n": 262144, "p": 1, "r": 8, "salt": "a13e239d8a650bfcdb47997c90548b761c6fdbd8a5315323c72c5ed4c8fd4a22" },
                          "mac": "83edbcf1fb0b3a7130dbbbe3c7b86a4f86be2de84c28db0f6f862d557612c8e6" },
              "id": "11202eae-fc67-4d65-8103-4255fed6694a",
              "version": 3 },
    "filename": "UTC--2017-11-30T16-48-37.835384970Z--dd72c8f99e53fbe343eae4efcee31f720e08568f" },

  { "data": { "address": "88ff728cd9ea8956fd1aaf71171ecde57c9a6aca",
              "crypto": { "cipher": "aes-128-ctr",
                          "ciphertext": "bcfe9b490e6b841adae40b8e40b4f7675b1d45738bc0c43883b5d4cad4400294",
                          "cipherparams": { "iv": "76fa1397b6bbb633a021abe584dc032a" },
                          "kdf": "scrypt",
                          "kdfparams": { "dklen": 32, "n": 262144, "p": 1, "r": 8, "salt": "1132921cd8972aae1476fa1f18357cadc6e7922c1942e51b7c3c0dea86352840" },
                          "mac": "1059333a946121fdbfcfc22d2185836d77271bb97cdf8ad165466519e8a683d8" },
              "id": "e63e7933-1356-4067-aa22-6e0d41f65819",
              "version": 3 },
    "filename": "UTC--2017-11-30T16-48-39.035496550Z--88ff728cd9ea8956fd1aaf71171ecde57c9a6aca" },

  { "data": { "address": "f0864eb0d1dd7344b6b68a807bb6e7dcf91b5694",
              "crypto": { "cipher": "aes-128-ctr",
                          "ciphertext": "e5864006274a11154e1db03e2c47fafe31aa00d4e1d20e5ff404d9f4f58a6090",
                          "cipherparams": { "iv": "b297b4531f0e1726274877f03b1f63af" },
                          "kdf": "scrypt",
                          "kdfparams": { "dklen": 32, "n": 262144, "p": 1, "r": 8, "salt": "a5282abb8bb31682b83a9df1485d7b3e8950d6354462f5b527165d5e9eb2edab" },
                          "mac": "47220f8e7752955d63903cf93ac21d84d114655f60953a94ad0be318e5b4a8fd" },
              "id": "1ad1c0c6-10ac-44cd-9fd8-0fd3531d5b28",
              "version": 3 },
    "filename": "UTC--2017-11-30T16-48-43.419430184Z--f0864eb0d1dd7344b6b68a807bb6e7dcf91b5694" },

  { "data": { "address": "514980540142ea7ee1c85df86504041a017e8c5e",
              "crypto": { "cipher": "aes-128-ctr",
                          "ciphertext": "564e15c690034567902ba741fa88cb9070735be8e46d0e3f096432b61ea215b4",
                          "cipherparams": { "iv": "6b54e0e81a384d1e63dde647354b7cab" },
                          "kdf": "scrypt",
                          "kdfparams": { "dklen": 32, "n": 262144, "p": 1, "r": 8, "salt": "ffac97d2979eb275f1a93f489a23cea94ab991b8803b6e90fdda1bff5a03785d" },
                          "mac": "8e16d7fddf0d6514803216516bb43fcd377df263b8d06dca98655f9fb1266a97" },
              "id": "ab44e088-7690-4213-ae10-980360762cb3",
              "version": 3 },
    "filename": "UTC--2017-12-28T17-52-42.274198873Z--514980540142ea7ee1c85df86504041a017e8c5e" },
)

COINBASE = '0x' + KEYFILES[0]["data"]["address"]

GENESIS_DATA = {
  "config": {
    "chainId": 104,
    "homesteadBlock": 0,
    "eip150Block": 0,
    "eip150Hash": "0x0000000000000000000000000000000000000000000000000000000000000000",
    "eip155Block": 0,
    "eip158Block": 0,
    "eip160Block": 0,
    "byzantiumBlock": 0,

    "clique": {
      "period": 1,
      "epoch": 30000
    }
  },
  "nonce": "0x0",
  "timestamp": "0x5a2036f7",
  "extraData": "0x0000000000000000000000000000000000000000000000000000000000000000a1aa59f3980144daebd2252c709c997c880bc3240000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
  "gasLimit": "2100000000",
  "difficulty": "0x1",
  "mixHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
  "alloc": {},
  "number": "0x0",
  "gasUsed": "0x0",
  "parentHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
  "coinbase": "0x0000000000000000000000000000000000000000"
}

def generate_precompiled_address(number):
  return "{:040x}".format(number)

def generate_genesis():
  genesis_data = GENESIS_DATA
  # Fund precompiled contract addresses with 1 wei to allow instantiation in new blockchains.
  for i in range(255):
    genesis_data["alloc"][generate_precompiled_address(i)] = { "balance": "0x1" }

  # Fund available testing accounts
  for serialized_keyfile in KEYFILES:
    address = serialized_keyfile["data"]["address"]
    genesis_data["alloc"][address] = { "balance": "10000000000000000000000000000" }
  return genesis_data




def ensure_path_exists(dir_path):
  if not os.path.exists(dir_path):
    os.makedirs(dir_path)
    return True
  return False


def wait_for_popen(proc, timeout):
  start = time.time()
  while time.time() < start + timeout:
    if proc.poll() is None:
      time.sleep(0.01)
    else:
      break


def kill_proc_gracefully(proc):
  if proc.poll() is None:
    proc.send_signal(signal.SIGINT)
    wait_for_popen(proc, 13)

  if proc.poll() is None:
    proc.terminate()
    wait_for_popen(proc, 5)

  if proc.poll() is None:
    proc.kill()
    wait_for_popen(proc, 2)






# auxiliar functions; unused in geth fixtures
def mine_block(web3):
  origin_block_number = web3.eth.blockNumber

  start_time = time.time()
  web3.miner.start(1)
  while time.time() < start_time + 120:
    block_number = web3.eth.blockNumber
    if block_number > origin_block_number:
      web3.miner.stop()
      return block_number
    else:
      time.sleep(0.1)
  else:
    raise ValueError("No block mined during wait period")



def mine_transaction_hash(web3, txn_hash):
  web3.miner.start(1)
  receipt = web3.eth.waitForTransactionReceipt(txn_hash)
  web3.miner.stop()
  return receipt


def deploy_contract(web3, name, factory, tx):
  web3.personal.unlockAccount(tx["from"], KEYFILE_PW)
  deploy_txn_hash = factory.constructor().transact(tx)
  print('{0} deploy hash: '.format(name), deploy_txn_hash)
  deploy_receipt = mine_transaction_hash(web3, deploy_txn_hash)
  contract_address = deploy_receipt['contractAddress']
  assert is_checksum_address(contract_address)
  print('{0} deploy transaction mined. Contract address: '.format(name), contract_address)
  return deploy_receipt


