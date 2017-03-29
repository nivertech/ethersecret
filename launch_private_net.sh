#!/bin/bash
# Author: Zvi Avraham

NETWORK_ID="347965709"
DATADIR="/home/${USER}/.ethereum/net_${NETWORK_ID}"
GENESIS_FILE="/home/${USER}/.ethereum/genesis_${NETWORK_ID}.json"

cat <<'EOF' > ${GENESIS_FILE}
{
    "nonce": "0x0000000000003942",
    "timestamp": "0x0",
    "parentHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
    "extraData": "0x0",
    "gasLimit": "0x4c4b40",
    "difficulty": "0x400",
    "mixhash": "0x0000000000000000000000000000000000000000000000000000000000000000",
    "coinbase": "0x0000000000000000000000000000000000000000",
    "alloc": {
        "0x6d87462cB31C1217cf1eD61B4FCC37F823c61624": "1000000000000000000000000"
    }
}
EOF

mkdir -p ${DATADIR}

# Run this once, but it does not hurt to run it every time
geth --datadir ${DATADIR} init ${GENESIS_FILE}

geth --datadir ${DATADIR} \
    --networkid ${NETWORK_ID} \
    --rpc \
    --rpcport 8545 \
    --rpcaddr 0.0.0.0 \
    --rpccorsdomain "*" \
    --rpcapi "eth,web3" \
    console

    # use this to listen on all IPs from VM:
    #--rpcaddr 0.0.0.0 \
    #--rpcaddr 127.0.0.1 \
