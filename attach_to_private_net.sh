#!/bin/bash
# Author: Zvi Avraham

NETWORK_ID="347965709"
DATADIR="/home/${USER}/.ethereum/net_${NETWORK_ID}"
GENESIS_FILE="/home/${USER}/.ethereum/genesis_${NETWORK_ID}.json"

geth attach "ipc:${DATADIR}/geth.ipc"
