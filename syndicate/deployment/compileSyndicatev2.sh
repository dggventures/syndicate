cd ..
mkdir -p build
solc -o ./build --abi --bin --overwrite --optimize --optimize-runs 0 Syndicatev2.sol
solc -o ./build --abi --bin --overwrite --optimize --optimize-runs 0 StandardToken.sol
cd deployment