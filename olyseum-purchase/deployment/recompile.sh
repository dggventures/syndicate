#!/usr/bin/env sh
cd ../contracts
~/solc19/solc --abi --bin --overwrite --optimize --optimize-runs 0 -o ../deployment/build OlyseumPurchase.sol
