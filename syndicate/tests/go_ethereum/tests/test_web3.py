
from tests.go_ethereum.common import (
  mine_transaction_hash,
)


def test_web3(web3, unlocked_accounts):
  some_address = "0x0000000000000000000000000000000000000000"
  previous_balance = web3.eth.getBalance(some_address)
  sent_value = web3.toWei(10, "ether")
  tx_hash = web3.eth.sendTransaction(
    {"from": unlocked_accounts[0], "to": some_address, "value": sent_value, "gas": 25000, "gasPrice": web3.toWei(1, "gwei")})
  mine_transaction_hash(web3, tx_hash)
  assert previous_balance + sent_value == web3.eth.getBalance(some_address)