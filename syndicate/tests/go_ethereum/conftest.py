import json
import os
import pytest
import shutil
import subprocess
import time
import socket
from collections import namedtuple

from eth_utils import (
  to_text,
  remove_0x_prefix,
)

from web3 import Web3
from web3.auto import w3

import tests.go_ethereum.common


Genesis = namedtuple('Genesis', 'data path')

GETH_SCOPE = 'session'
WEB3_SCOPE = 'session'

@pytest.fixture(scope=GETH_SCOPE)
def geth_binary():
  return 'geth'


@pytest.fixture(scope=GETH_SCOPE)
def geth_dir():
  geth_dir_path = "geth"
  tests.go_ethereum.common.ensure_path_exists(geth_dir_path)
  return geth_dir_path


@pytest.fixture(scope=GETH_SCOPE)
def datadir(geth_dir, geth_binary):
  tmp_datadir = os.path.join(geth_dir, 'datadir')
  if os.path.exists(tmp_datadir):
    removedb_datadir_command = (
      geth_binary,
      '--datadir', str(tmp_datadir),
      'removedb',
    )
    proc = get_process(removedb_datadir_command)
    proc.communicate(input="y\ny\ny\ny\n".encode())
    transaction_journal = os.path.join(tmp_datadir, 'geth', 'transactions.rlp')
    if os.path.exists(transaction_journal):
      os.remove(transaction_journal)

  return tmp_datadir

@pytest.fixture(scope=GETH_SCOPE)
def keystore(datadir):
  keystore_dir = os.path.join(datadir, 'keystore')
  tests.go_ethereum.common.ensure_path_exists(keystore_dir)

  for serialized_keyfile in tests.go_ethereum.common.KEYFILES:
    keyfile_path = os.path.join(keystore_dir, serialized_keyfile["filename"])
    with open(keyfile_path, 'w') as keyfile:
      json.dump(serialized_keyfile["data"], keyfile)

@pytest.fixture(scope=GETH_SCOPE)
def ipc_socket(geth_dir):
  return os.path.join(geth_dir, 'geth.ipc')

@pytest.fixture(scope=GETH_SCOPE)
def genesis(geth_dir):
  genesis_file_path = os.path.join(geth_dir, 'genesis.json')
  genesis_data = tests.go_ethereum.common.generate_genesis()
  with open(genesis_file_path, 'w') as genesis_file:
    json.dump(genesis_data, genesis_file)
  return Genesis(data=genesis_data, path=genesis_file_path)

@pytest.fixture(scope=GETH_SCOPE)
def ipc_file(geth_dir):
  return os.path.join(geth_dir, 'geth.ipc')

@pytest.fixture(scope=GETH_SCOPE)
def open_port():
  with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    return str(port)

def get_process(run_command):
  proc = subprocess.Popen(
    run_command,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    bufsize=1,
  )
  return proc

@pytest.fixture(scope=GETH_SCOPE)
def geth_process(geth_binary, datadir, genesis, ipc_file, open_port, keystore):
  init_datadir_command = (
    geth_binary,
    '--datadir', str(datadir),
    'init',
    str(genesis.path),
  )
  subprocess.check_output(
    init_datadir_command,
    stdin=subprocess.PIPE,
    stderr=subprocess.PIPE,
  )
  run_geth_command = (
    geth_binary,
    '--datadir', str(datadir),
    '--ipcpath', str(ipc_file),
    '--nodiscover',
    '--port', open_port,
    '--networkid', str(genesis.data['config']['chainId']),
    '--etherbase', remove_0x_prefix(tests.go_ethereum.common.COINBASE),
    '--gasprice', '0',                           # Gas price threshold for the cpu miner
    '--targetgaslimit', genesis.data['gasLimit']
  )
  print(' '.join(run_geth_command))
  try:
    proc = get_process(run_geth_command)
    yield proc
  finally:
    tests.go_ethereum.common.kill_proc_gracefully(proc)
    output, errors = proc.communicate()
    print(
      "Geth Process Exited:\n"
      "stdout:{0}\n\n"
      "stderr:{1}\n\n".format(
        to_text(output),
        to_text(errors),
      )
    )

def wait_for_socket(ipc_path, timeout=30):
  start = time.time()
  while time.time() < start + timeout:
    try:
      with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(ipc_path)
        sock.settimeout(timeout)
    except (FileNotFoundError, socket.error):
      time.sleep(0.01)
    else:
      break

@pytest.fixture(scope=WEB3_SCOPE)
def web3(ipc_file, geth_process):
  ipc_path = str(os.path.abspath(ipc_file))
  wait_for_socket(ipc_path)
  return Web3(Web3.IPCProvider(ipc_path))

@pytest.fixture(scope=WEB3_SCOPE)
def web3_2():
  return w3

@pytest.fixture(scope=WEB3_SCOPE)
def unlocked_accounts(web3):
  accounts = web3.eth.accounts
  for account in accounts:
    web3.personal.unlockAccount(account, tests.go_ethereum.common.KEYFILE_PW, 10000000)
  return accounts

@pytest.fixture(scope=WEB3_SCOPE)
def status(get_tx_receipt):
  def inner_status(tx_hash):
    return get_tx_receipt(tx_hash).status
  return inner_status

@pytest.fixture(scope=WEB3_SCOPE)
def wait(get_tx_receipt):
  def inner_wait(tx_hash):
    get_tx_receipt(tx_hash)
  return inner_wait

@pytest.fixture(scope=WEB3_SCOPE)
def get_tx_receipt(web3_2):
  def inner_get_tx_receipt(tx_hash):
    return web3_2.eth.waitForTransactionReceipt(tx_hash, timeout=10)
  return inner_get_tx_receipt

# unused
# @pytest.yield_fixture(scope="module")
# def event_loop(request):
#   loop = asyncio.get_event_loop_policy().new_event_loop()
#   yield loop
#   loop.close()
