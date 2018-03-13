#!/usr/bin/python3 -i

import deploy
import testing_helpers

#Assigning testing_helpers module functions and variables to local variables
miner = deploy.miner

buy = testing_helpers.buy
get_transaction_receipt = testing_helpers.get_transaction_receipt
status = testing_helpers.status
transaction_info = testing_helpers.transaction_info
wait = testing_helpers.wait

approve_unwanted_tokens = testing_helpers.approve_unwanted_tokens
emergency_withdraw = testing_helpers.emergency_withdraw
set_transfer_gas = testing_helpers.set_transfer_gas
token_balance = testing_helpers.token_balance
update_balances = testing_helpers.update_balances
update_token = testing_helpers.update_token
whitelist = testing_helpers.whitelist
withdraw_tokens_approve = testing_helpers.withdraw_tokens_approve
withdraw_tokens_transfer = testing_helpers.withdraw_tokens_transfer




# Testing start ---------------------------------------------------

# Set transfer gas
print("\nSetting transfer gas...\n")
if (1 == set_transfer_gas(1200)):
	print("\nSuccess!\n")
else:
	print("Transfer gas not set")


wait()





miner.stop()