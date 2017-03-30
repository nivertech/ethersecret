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

#import node


import xmlrpclib

is_localhost = False
if(is_localhost):
    sever1 = xmlrpclib.ServerProxy('http://localhost:8001')
    sever2 = xmlrpclib.ServerProxy('http://localhost:8002')
    sever3 = xmlrpclib.ServerProxy('http://localhost:8003')
else:
    sever1 = xmlrpclib.ServerProxy('http://10.101.154.71:8001')
    sever2 = xmlrpclib.ServerProxy('http://10.79.151.81:8001')
    sever3 = xmlrpclib.ServerProxy('http://10.65.213.19:8001')


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
    
    print "uploading encrypted secret to blockchain"
    newSecret( ethereum_key, enc_secret )
    
    # TODO - send to nodes
    keys1 = [b2h(keys1[0]), b2h(keys1[1]), b2h(keys1[2])]
    keys2 = [b2h(keys2[0]), b2h(keys2[1]), b2h(keys2[2])]    
    keys3 = [b2h(keys3[0]), b2h(keys3[1]), b2h(keys3[2])]    
    
    #print str(keys1)
    
    print "send key share 1 to server 1"
    sever1.submit_keys( secret_index, keys1, 1 )
    print "send key share 2 to server 2"    
    sever2.submit_keys( secret_index, keys2, 2 )
    print "send key share 3 to server 3"    
    sever3.submit_keys( secret_index, keys3, 3 )    

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
    print "read raw encrypted data from blockchain"
    data = getEncData( ethereum_key, secret_index)
    
    # 2) ask for keys and get at least two - TODO
    print "requesting key share 1 from server 1"
    keys1 = sever1.get_keys(b2h(ethereum_key), secret_index, 1)
    print "requesting key share 2 from server 2"    
    keys2 = sever2.get_keys(b2h(ethereum_key), secret_index, 2)
    print "requesting key share 3 from server 3"    
    keys3 = sever3.get_keys(b2h(ethereum_key), secret_index, 3)
    
    if( len(keys1) == 3 ):
        print "received receive key share 1 from server 1"         
        keys1 = [ h2b(keys1[0]),h2b(keys1[1]),h2b(keys1[2])]
    else:
        print "didn't received receive key share 1 from server 1"        
        keys1 = None    

    if( len(keys2) == 3 ):
        print "received receive key share 2 from server 2"
        keys2 = [ h2b(keys2[0]),h2b(keys2[1]),h2b(keys2[2])]
    else:
        print "didn't received receive key share 2 from server 2"                 
        keys2 = None    

    if( len(keys3) == 3 ):
        print "received receive key share 3 from server 3"        
        keys3 = [ h2b(keys3[0]),h2b(keys3[1]),h2b(keys3[2])]
    else:
        print "didn't received receive key share 3 from server 3"
        keys3 = None



    key = None

    if( not (keys1 is None) and not (keys2 is None) ):
        key = key12( keys1[0], keys2[0], keys1[1]) 
    elif( not (keys1 is None) and not (keys3 is None) ):
        key = key13( keys1[0], keys3[0], keys1[2]) 
    elif( not (keys2 is None) and not (keys3 is None) ):
        key = key23( keys2[0], keys3[0], keys2[2]) 
    else:
        print "cannot decrypt, less than 2 servers sent keys"
        return h2b("00") * 32
    
    return decrypt(data,key)


'''    
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
'''

'''
import socket
TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 1024
MESSAGE = "Hello, World!"
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.send(MESSAGE)
data = s.recv(BUFFER_SIZE)
s.close()

print "received data:", data
'''



ethereum_key = utils.sha3("Smart Pool2")

secret = h2b("45746865722050726976616379205465616d") + h2b("00") * 14
#secret = h2b("476176696e206973207361746f736869") + h2b("00") * 16

#secret = h2b("c0dec0defacefeed") * 4
secret_index = 22


print "secret index " + str(secret_index)

################################################################################



upload_enc_secret_to_blockchain_and_send_keys_to_nodes( secret, secret_index, ethereum_key )
 
data = read_and_decrypt_secret(secret_index, ethereum_key)
print "decrytion returned: " + b2h(data)

print "giving read access to 0x6d87462cB31C1217cf1eD61B4FCC37F823c61624 for 3 hours"
set_prem( ethereum_key, secret_index, "0x6d87462cB31C1217cf1eD61B4FCC37F823c61624", 0, 2490817702 )

data = read_and_decrypt_secret(secret_index, ethereum_key)
print "decrytion returned: " + data
#print b2h(data)