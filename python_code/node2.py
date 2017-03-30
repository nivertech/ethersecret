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
    return 0

def get_keys( ethereum_key_sender, secret_index, node_index ):
    global keys
    address = "0x" + b2h(utils.privtoaddr(ethereum_key_sender))
    if( can_read( h2b(ethereum_key_sender), secret_index ) ):
        print address + " authorized to read"
        return (keys[node_index-1])[secret_index]
    
    print address + " not authorized to read"
    
    return []

'''
import socket
TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 20  # Normally 1024, but we want fast response
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)
conn, addr = s.accept()
print 'Connection address:', addr
while 1:
    data = conn.recv(BUFFER_SIZE)
    if not data: break
    print "received data:", data
    #conn.send(data)  # echo
    if( data[0] > 0 ):
        print "submit_keys"
    conn.close()
'''



# Print list of available methods
#print s.system.listMethods()
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

# Create server
print "I am server 2"
server = SimpleXMLRPCServer(("localhost", 8002),
                            requestHandler=RequestHandler)
server.register_introspection_functions()

# Register pow() function; this will use the value of
# pow.__name__ as the name, which is just 'pow'.
server.register_function(submit_keys)
server.register_function(get_keys)
'''
# Register a function under a different name
def adder_function(x,y):
    return x + y
server.register_function(adder_function, 'add')

# Register an instance; all the methods of the instance are
# published as XML-RPC methods (in this case, just 'div').
class MyFuncs:
    def div(self, x, y):
        return x // y

server.register_instance(MyFuncs())
'''
# Run the server's main loop

server.serve_forever()