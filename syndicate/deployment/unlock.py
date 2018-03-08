web3 = None

def unlock():
	for x in web3.eth.accounts:
		web3.personal.unlockAccount(x, 'dike2361', 1800)

