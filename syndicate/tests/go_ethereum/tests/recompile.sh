#!/bin/sh

mkdir -p ../../build
cd ../../../contracts
solc -o ../tests/build/ --abi --bin --overwrite --optimize --optimize-runs 0 Syndicatev2.sol
solc -o ../tests/build/ --abi --bin --overwrite --optimize --optimize-runs 0 StandardToken.sol
cd ../tests/go_ethereum/tests