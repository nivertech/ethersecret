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


ethereum_key = utils.sha3("Smart Pool2")

deploy(ethereum_key)