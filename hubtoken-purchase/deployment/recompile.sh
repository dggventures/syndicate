#!/usr/bin/env sh
cd ../contracts
solc --abi --bin --overwrite --optimize --optimize-runs 0 -o ../deployment/build HubTokenPurchase.sol
