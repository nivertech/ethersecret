from pycoin.serialize import b2h, h2b
from pycoin import encoding
import rlp
from ethereum import tester, utils, abi, blocks, transactions
import requests
import json
import jsonrpc
import time
from ethereum.abi import ContractTranslator
from ethereum.utils import mk_contract_address


from eth_warpper import *


keys = [{},{},{}] # mapping from secret index to keys

def submit_keys( secret_index, user_keys, node_index ):
    global keys
    (keys[node_index-1])[secret_index] = user_keys

def get_keys( ethereum_key_sender, secret_index, node_index ):
    global keys
    if( can_read( ethereum_key_sender, secret_index ) ):
        return (keys[node_index-1])[secret_index]
    
    return None