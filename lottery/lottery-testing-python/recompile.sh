#!/bin/sh
cd ../contracts
solc --abi --bin --overwrite --optimize --optimize-runs 0 -o ../lottery-testing-python/build LotteryInvestment.sol