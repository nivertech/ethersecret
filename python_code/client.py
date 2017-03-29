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
from bike.parsing.fastparserast import Node


from eth_warpper import *

import node


def xor( x, y ):
    a = bytearray(x)
    b = bytearray(y)
    
    z = bytearray(32)

    result = h2b("")
    
    for i in range(32):
        z[i] = a[i] ^ b[i]
        result = result + h2b("%02X" % z[i])
       
    return result




def encrypt( text, key ):
    if( len(text) != 32 or len(key) != 32 ):
        return None
    return xor(text,key)

def decrypt( chiper, key ):
    if( len(chiper) != 32 or len(key) != 32 ):
        return None    
    return xor(chiper,key)


def CreateNodeKeys( key, rand1, rand2, rand3, node_ind ):
    if( node_ind == 1 ):
        clientKey1 = xor(key,rand1) 
        clientKey2 = xor(xor(key,rand1),rand2)
        clientKey3 = xor(xor(key,rand1),rand3)
    elif( node_ind == 2 ):
        clientKey1 = xor(key,rand2) 
        clientKey2 = xor(xor(key,rand2),rand1)
        clientKey3 = xor(xor(key,rand2),rand3)
    elif( node_ind == 3 ):
        clientKey1 = xor(key,rand3) 
        clientKey2 = xor(xor(key,rand3),rand1)
        clientKey3 = xor(xor(key,rand3),rand2)
            
    return [clientKey1, clientKey2, clientKey3]



def upload_enc_secret_to_blockchain_and_send_keys_to_nodes( secret, secret_index, ethereum_key ):
    key = utils.sha3("password") 
    rand1 = utils.sha3("rand1")
    rand2 = utils.sha3("rand2")
    rand3 = utils.sha3("rand3")

    enc_secret = encrypt(secret, key)
    
    keys1 = CreateNodeKeys( key, rand1, rand2, rand3, 1 ) 
    keys2 = CreateNodeKeys( key, rand1, rand2, rand3, 2 )
    keys3 = CreateNodeKeys( key, rand1, rand2, rand3, 3 )
    
    newSecret( ethereum_key, enc_secret )
    
    # TODO - send to nodes
    node.submit_keys( secret_index, keys1, 1 )
    node.submit_keys( secret_index, keys2, 2 )
    node.submit_keys( secret_index, keys3, 3 )    

def key12( xor_key_rand1, xor_key_rand2, xor_key_rand1_rand2 ):
    key = xor( xor( xor_key_rand1, xor_key_rand2 ), xor_key_rand1_rand2 )
    return key


def key13( xor_key_rand1, xor_key_rand3, xor_key_rand1_rand3 ):
    key = xor( xor( xor_key_rand1, xor_key_rand3 ), xor_key_rand1_rand3 )
    return key


def key23( xor_key_rand2, xor_key_rand3, xor_key_rand2_rand3 ):
    key = xor( xor( xor_key_rand2, xor_key_rand3 ), xor_key_rand2_rand3 )
    return key


def read_and_decrypt_secret( secret_index, ethereum_key ):
    # 1) read encrypted secret
    data = getEncData( ethereum_key, secret_index)
    
    # 2) ask for keys and get at least two - TODO
    keys1 = node.get_keys(ethereum_key, secret_index, 1)
    keys2 = node.get_keys(ethereum_key, secret_index, 2)
    keys3 = node.get_keys(ethereum_key, secret_index, 3)    

    key = None

    if( not (keys1 is None) and not (keys2 is None) ):
        key = key12( keys1[0], keys2[0], keys1[1]) 
    elif( not (keys1 is None) and not (keys3 is None) ):
        key = key13( keys1[0], keys3[0], keys1[2]) 
    elif( not (keys2 is None) and not (keys3 is None) ):
        key = key23( keys2[0], keys3[0], keys2[2]) 
    else:
        print "cannot decrypt"
        return h2b("00") * 32
    
    return decrypt(data,key)


    
secret = h2b("c0dec0defacefeed") * 4
secret_index = 3
ethereum_key = utils.sha3("Smart Pool2")
################################################################################

upload_enc_secret_to_blockchain_and_send_keys_to_nodes( secret, secret_index, ethereum_key )
print "upload done" 
data = read_and_decrypt_secret(secret_index, ethereum_key)
print b2h(data)

set_prem( ethereum_key, secret_index, "0x6d87462cB31C1217cf1eD61B4FCC37F823c61624", 0, 2490817702 )
print "set prem"

data = read_and_decrypt_secret(secret_index, ethereum_key)
print b2h(data)
