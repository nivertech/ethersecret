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


global_wait_for_confirm = True
use_ether_scan = False
use_augor = False
ether_scan_api_key = '66FCG5X3HSVW23R2ZJTFJEKWMKKGJVIQXK'
local_url = "http://localhost:8545/jsonrpc"
augor_local_url = "https://eth3.augur.net/jsonrpc"

def merge_two_dicts(x, y):
    '''Given two dicts, merge them into a new dict as a shallow copy.'''
    z = x.copy()
    z.update(y)
    return z

def etherscan_call(method_name, params):
    url = "https://kovan.etherscan.io/api"
    payload = {"module" : "proxy",
               "action" : method_name,
               "apikey" : ether_scan_api_key }
    payload = merge_two_dicts(payload, params[0])
    response = requests.post(url, params=payload)
    #print str(response)
    return response.json()[ 'result' ]
    
    
def json_call(method_name, params):
    if use_ether_scan:
        return etherscan_call(method_name, params)
    url = local_url
    if use_augor:
        url = augor_local_url
    headers = {'content-type': 'application/json'}
    
    # Example echo method
    payload = { "method": method_name,
                "params": params,
                "jsonrpc": "2.0",
                "id": 1,
                }
    # print str(params)
    response = requests.post(url, data=json.dumps(payload), headers=headers).json()
    #print str(response)
    #print response
    return response[ 'result' ]

global_nonce = -1
def get_num_transactions(address):
    #return "12d"
    #return "6"
    
    global global_nonce
    # if( global_nonce > 0 ):
    #    global_nonce += 1
    #    return "0x" + "%x" % global_nonce
    if use_ether_scan:
        params = [{ "address" : "0x" + address, "tag" : "pending" }]
    else:
        params = [ "0x" + address, "pending" ]
    nonce = json_call("eth_getTransactionCount", params)
    # print "nonce: " + str(nonce)
    global_nonce = int(nonce, 16)
    return nonce 

def get_gas_price_in_wei():
    if use_ether_scan:
        return "0x%x" % 20000000000  # 20 gwei
    return json_call("eth_gasPrice", [])

def eval_startgas(src, dst, value, data, gas_price):
    if use_ether_scan or True:
        return "0x%x" % (4712388 / 2)  # hardcoded max gas
        
    params = { "value" : "0x" + str(value),
               "pasPrice" : gas_price }
    if len(data) > 0:
        params["data"] = "0x" + str(data)
    if len(dst) > 0:
        params["to"] = "0x" + dst
    #           "from" : "0x" + dst }
    # params = { "from" : "0x06f099a7d789f10b0c1c1f069638ba25b2bf8483",
    #           "data" : "123456789" }
    # print str(params)
    return json_call("eth_estimateGas", [params])


def make_transaction(src_priv_key, dst_address, value, data):
    src_address = b2h(utils.privtoaddr(src_priv_key))
    nonce = get_num_transactions(src_address)
    gas_price = get_gas_price_in_wei()
    data_as_string = b2h(data)
    # print len(data_as_string)
    # if len(data) > 0:
    #    data_as_string = "0x" + data_as_string 
    start_gas = eval_startgas(src_address, dst_address, value, data_as_string, gas_price)
    
    nonce = int(nonce, 16)
    gas_price = int(gas_price, 16) 
    #int(gas_price, 16)/20
    start_gas = int(start_gas, 16) + 100000
    
    start_gas = 4612288  # // 10
    #start_gas = 38336
    #start_gas = 30048
    # start_gas = 5000000    
    
    for i in range(1):
        tx = transactions.Transaction(nonce,
                                       gas_price,
                                       start_gas,
                                       dst_address,
                                       value,
                                       data).sign(src_priv_key)
        
        
                                       
        tx_hex = b2h(rlp.encode(tx))
        tx_hash = b2h(tx.hash)
                        
        #print(tx_hex)
        # print str(tx_hash)
        if use_ether_scan:
            params = [{"hex" : "0x" + tx_hex }]
        else:
            params = ["0x" + tx_hex]
        return_value = json_call("eth_sendRawTransaction", params)                       
        if return_value == "0x0000000000000000000000000000000000000000000000000000000000000000":
            print "Transaction failed"
            return return_value
        
        nonce += 1
        print str(nonce)
    wait_for_confirmation(tx_hash)
    return return_value        

    
def get_contract_data(contract_name, ctor_args):
    bin_file = open(contract_name + ".bin", "rb")
    bin = h2b(bin_file.read())
    # print bin
    bin_file.close()
    bin = h2b("6060604052341561000c57fe5b5b5b5b6103b08061001e6000396000f300606060405263ffffffff60e060020a6000350416631e5e2d8f81146100425780637789139314610069578063d40f1da21461007e578063de9702a4146100a5575bfe5b341561004a57fe5b610067600435602435600160a060020a03604435166064356100ef565b005b341561007157fe5b610067600435610162565b005b341561008657fe5b6100916004356101f8565b604080519115158252519081900360200190f35b34156100ad57fe5b6100b8600435610276565b60408051600160a060020a039687168152949095166020850152838501929092526060830152608082015290519081900360a00190f35b600060008281548110151561010057fe5b906000526020600020906005020160005b50805490915033600160a060020a0390811691161461012f57610000565b600181018054600160a060020a031916600160a060020a03851617905560028101859055600381018490555b5050505050565b61016a6102c3565b600160a060020a033316815260808101829052600080546001810161018f8382610305565b916000526020600020906005020160005b5082518154600160a060020a03918216600160a060020a0319918216178355602085015160018401805491909316911617905560408301516002820155606083015160038201556080830151600490910155505b5050565b6000600060008381548110151561020b57fe5b906000526020600020906005020160005b50600181015490915033600160a060020a039081169116146102415760009150610270565b80600201544210156102565760009150610270565b806003015442111561026b5760009150610270565b600191505b50919050565b600080548290811061028457fe5b906000526020600020906005020160005b508054600182015460028301546003840154600490940154600160a060020a03938416955091909216929085565b60a0604051908101604052806000600160a060020a031681526020016000600160a060020a031681526020016000815260200160008152602001600081525090565b815481835581811511610331576005028160050283600052602060002091820191016103319190610337565b5b505050565b61038191905b8082111561037d578054600160a060020a03199081168255600182018054909116905560006002820181905560038201819055600482015560050161033d565b5090565b905600a165627a7a72305820c2389efff0fcf3752969acca63721798524aa30be1bcda35155b682da37f83b20029")
    
    abi_file = open(contract_name + ".abi", "r")
    abi = abi_file.read()
    abi_file.close()
    
    translator = ContractTranslator(abi)
    ctor_call = translator.encode_constructor_arguments(ctor_args)
    #print "ctor"
    #print b2h(ctor_call)
    
        
    return (bin + ctor_call, abi)
    
def upload_contract(priv_key, contract_data, value):
    src_address = b2h(utils.privtoaddr(priv_key))
    nonce = get_num_transactions(src_address)
    print "nonce"
    print str(nonce)
    gas_price = get_gas_price_in_wei()
    start_gas = eval_startgas(src_address, "", value, b2h(contract_data), gas_price)    
    
    contract_hash = b2h(mk_contract_address(src_address, int(nonce, 16))) 
    print "contract hash"
    print contract_hash
    
    nonce = int(nonce, 16)
    # print str(nonce)
    gas_price = int(gas_price, 16) * 3 /3
    start_gas = int(start_gas, 16) + 100000
    print str(start_gas)
    start_gas = 4700000  # 4710388#3000000#4712388 # 5183626 / 2
    #start_gas = 4990000
    
    tx = transactions.contract(nonce, gas_price, start_gas, value, contract_data).sign(priv_key)
                     
    # print contract_data                  
    tx_hex = b2h(rlp.encode(tx))
    tx_hash = b2h(tx.hash)
    print(tx_hex)
    print tx_hash
    
    # print str(tx_hash)
    if use_ether_scan:
        params = [{"hex" : "0x" + tx_hex }]
    else:
        params = ["0x" + tx_hex]
            
    return_value = (json_call("eth_sendRawTransaction", params), contract_hash)
    wait_for_confirmation(tx_hash)
    return return_value        

def call_function(priv_key, value, contract_hash, contract_abi, function_name, args):
    translator = ContractTranslator(contract_abi)
    call = translator.encode_function_call(function_name, args)
    return make_transaction(priv_key, contract_hash, value, call)
    

def call_const_function(priv_key, value, contract_hash, contract_abi, function_name, args):
    src_address = b2h(utils.privtoaddr(priv_key))    
    translator = ContractTranslator(contract_abi)
    call = translator.encode_function_call(function_name, args)  
    nonce = get_num_transactions(src_address)
    gas_price = get_gas_price_in_wei()
    
    start_gas = eval_startgas(src_address, contract_hash, value, b2h(call), gas_price)    
    nonce = int(nonce, 16)
    gas_price = int(gas_price, 16)
    start_gas = int(start_gas, 16) + 100000
    start_gas = 7612288 

    
    params = { "from" : "0x" + src_address,
               "to"   : "0x" + contract_hash,
               "gas"  : "0x" + "%x" % start_gas,
               "gasPrice" : "0x" + "%x" % gas_price,
               "value" : "0x" + str(value),
               "data" : "0x" + b2h(call) }
    
    return_value = json_call("eth_call", [params])
    print return_value
    return_value = h2b(return_value[2:])  # remove 0x
    return translator.decode(function_name, return_value)



def make_new_filter(contract_address, topic):
    params = { "fromBlock" : "0x1",
               "address": "0x" + contract_address,
               "topics" : [topic] }
    filter_id = json_call("eth_newFilter", [params])
    # filter_id = "0x0"
    print filter_id
    params = filter_id
    print json_call("eth_getFilterLogs", [params])

def wait_for_confirmation(tx_hash):
    
    params = None
    if use_ether_scan:
        params = { "txhash" : "0x" + tx_hash }
    else:
        params = "0x" + tx_hash
    round = 0
    while(True):
        print "waiting for confirmation round " + str(round)
        round += 1 
        result = json_call("eth_getTransactionReceipt", [params])
        # print result
        if result is None:
            if(global_wait_for_confirm):
                time.sleep(10)
                continue
            else:
                time.sleep(1)
                return                
        # print str(result["blockHash"])
        if not(result["blockHash"] is None):
            return result
        time.sleep(10)
        
        
    
################################################################################

def augmented_node(left_child_int, right_child_int, min_timestamp_int, max_timestamp_int):
    left_child_hex = ("%0.32x" % left_child_int).zfill(64)
    right_child_hex = ("%0.32x" % right_child_int).zfill(64)
    children_hex = left_child_hex + right_child_hex  
    hash_int = int(b2h(utils.sha3(h2b(children_hex))), 16) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
    
    node_hex = ("%0.16x" % hash_int).zfill(32) + ("%0.4x" % max_timestamp_int).zfill(8) + ("%0.4x" % min_timestamp_int).zfill(8)
        
    node_int = int(node_hex, 16)
    
    return node_int  
    
def augmented_leaf(block_header_hex, timestamp_int):
    block_header_int = int(b2h(utils.sha3(h2b(block_header_hex))), 16)
    return augmented_node(block_header_int, block_header_int, timestamp_int, timestamp_int)
         
# build branch 000...0000         
def augmented_branch_zero(block_header_hex, timestamp_int, height):
    branch = []
    sybil = []
    leaf = augmented_leaf(block_header_hex, timestamp_int)
    branch.append(leaf)
    last_in_branch = leaf
    dummy_sybil = int("ff" * 32, 16)
    for i in range(height):
        node = augmented_node(last_in_branch, dummy_sybil, timestamp_int, 0xffffffff)
        branch.append(node)
        sybil.append(dummy_sybil)
        last_in_branch = node

    branch.reverse()
    sybil.reverse()
    
    return (branch, sybil)
    
################################################################################

def block_branch_zero(coinbase_tx_hex, height):
    branch = []
    sybil = []
    leaf = encoding.double_sha256(h2b(coinbase_tx_hex))
    dummy_sybil = h2b("ab" * 32)
    branch.append(int(b2h(leaf), 16))
    last_node = leaf
    for i in range(height):
        concat_hex = b2h(last_node).zfill(64) + b2h(dummy_sybil)
        node_hex = b2h(encoding.double_sha256(h2b(concat_hex)))
        sybil.append(int(b2h(dummy_sybil), 16))
        branch.append(int(node_hex, 16))
        last_node = h2b(node_hex)

    branch.reverse()
    sybil.reverse()
    
    return (branch, sybil)

def generate_block_header_hex(merkle_root_int, timestamp_int):
    nonce = 0
    merkle_hex = ("%0.32x" % merkle_root_int).zfill(64)
    timestamp_hex = ("%0.4x" % timestamp_int).zfill(8)
    header_hex = "00" * 36 + merkle_hex + timestamp_hex + "00" * 4
    
    while(True):
        nonce_hex = ("%0.4x" % nonce).zfill(8)
        result_header_hex = header_hex + nonce_hex
        sha = int(b2h(encoding.double_sha256(h2b(result_header_hex))), 16)
        if(sha & 0x03 == 0):
            return result_header_hex
        nonce += 1
        
        
    return None
        
################################################################################

def generate_verification_params(aug_height, merkle_height, coinbase_tx_hex_middle, coinbase_tx_hex_end):
    timestamp_int = 1
    coinbase_tx_hex = coinbase_tx_hex_middle + coinbase_tx_hex_end
    (block_merkle_branch, block_sibils) = block_branch_zero(coinbase_tx_hex, merkle_height)
    block_header_hex = generate_block_header_hex(block_merkle_branch[0], timestamp_int)
    (aug_branch, aug_sibils) = augmented_branch_zero(block_header_hex, timestamp_int, aug_height)
    seed = int("ff" * 32, 16)
    timestampIndex = 0
    coinbase_middle = h2b(coinbase_tx_hex_middle)
    
    return [aug_branch, aug_sibils, seed, block_merkle_branch, block_sibils, h2b(block_header_hex), coinbase_middle, timestampIndex]

def prepare_first_run(tx_suf_hex, contract_hash, abi):
    
    global global_wait_for_confirm
    global_origin_value = global_wait_for_confirm 
    length = len(tx_suf_hex) // 2
    # length -= 6400 # already uploaded
    if((length % 3200) > 0):
        raise "Invalid length"
    num_iters = length // 3200
    for i in range(num_iters):
        print "debug_extendCoinbaseTxOutput"
        # global_wait_for_confirm = ((i % 3 ) == 0)
        print call_function(key, 0, contract_hash, abi, "debug_extendCoinbaseTxOutput", [0, 3200])
        print "(" + str(i) + "/" + str(num_iters) + ")"
    global_wait_for_confirm = global_origin_value
        
    print "register"
    print call_function(key, 0, contract_hash, abi, "register", [0xdeadbeef])


def prepare_contract_env(num_shares, aug_merkle, contract_hash, abi):
    print "submitShares"    
    print call_function(key, 0, contract_hash, abi, "submitShares", [aug_merkle, num_shares])         
         

################################################################################

def submit_full_block(coinbase_prefix, merkle_branch, sibil, blockHeader, timestampindex):
    params = [coinbase_prefix, merkle_branch, sibil, blockHeader]
    prev_block = blockHeader
    for index in range(1, 6):
        header_hex = "ff" * 4 + b2h(encoding.double_sha256(prev_block)) + (40 * "ff")
        nonce = 0
        while(True):
            nonce_hex = ("%0.4x" % nonce).zfill(8)
            result_header_hex = header_hex + nonce_hex
            sha = int(b2h(encoding.double_sha256(h2b(result_header_hex))), 16)
            if(sha & 0x03 == 0):
                header_hex = result_header_hex 
                break
            nonce += 1
        header = h2b(header_hex)
        params.append(header)
        prev_block = header
    
    print "submitFullBlock"
    params.append(timestampindex)
    call_function(key, 0, contract_hash, abi, "submitFullBlock", params)    
            
################################################################################            
        
def payment_request():
    print "requestPayment"
    print call_function(key, 0, contract_hash, abi, "requestPayment", [0, 2])
    print "constructCoinbaseTx"        
    print call_function(key, 0, contract_hash, abi, "constructCoinbaseTx", [2])    


################################################################################






################################################################################


'''
ethereum_key = utils.sha3("Smart Pool2")

key = utils.sha3("Smart Pool2")
print b2h(utils.privtoaddr(key))
'''
global_wait_for_confirm = True
# ( contract_data, abi ) = get_contract_data( "./DumbPool", [])#,24,5,2016] )


# print address
# global_wait_for_confirm = True
# ( contract_data, abi ) = get_contract_data( "./SmartPool", [])#,24,5,2016] )

#print( 0.0025/(21000*40))
#sd


def deploy( key ):
    (contract_data_ethash, abi_ethash) = get_contract_data("./BankStatements", [])
    #contract_data_ethash = "12323"    
    print upload_contract(key, contract_data_ethash, 0)

def can_read( key, index ):
    (contract_data_ethash, abi_ethash) = get_contract_data("./BankStatements", [])
    contract_data_ethash = "0ee9e66884C1d4b531E3E17e0eb402E861A2aCC2"    
    
    retVal = call_const_function(key, 0, contract_data_ethash, abi_ethash, "getPremission", [index])
    
    return retVal[0]


def set_prem( key, index, reader, start, end ):
    (contract_data_ethash, abi_ethash) = get_contract_data("./BankStatements", [])
    
    contract_data_ethash = "0ee9e66884C1d4b531E3E17e0eb402E861A2aCC2"    
    call_function(key, 0, contract_data_ethash, abi_ethash, "setPremission", [start,end,reader,index])


def newSecret( key, secret ):
    (contract_data_ethash, abi_ethash) = get_contract_data("./BankStatements", [])
    
    contract_data_ethash = "0ee9e66884C1d4b531E3E17e0eb402E861A2aCC2"    
    call_function(key, 0, contract_data_ethash, abi_ethash, "newSecret", [secret])

def getEncData(key, secret_index):
    (contract_data_ethash, abi_ethash) = get_contract_data("./BankStatements", [])
    
    contract_data_ethash = "0ee9e66884C1d4b531E3E17e0eb402E861A2aCC2"    
    retVal = call_const_function(key, 0, contract_data_ethash, abi_ethash, "secrets", [secret_index])
    secret_int = retVal[4]
    secret_bytes = h2b("%064x" % secret_int) 
    return secret_bytes


#deploy( ethereum_key )
#newSecret(ethereum_key, 123456)
#setprem(ethereum_key, 0, 0x6d87462cB31C1217cf1eD61B4FCC37F823c61624, 0, 2490810860)
#(contract_data_ethash, abi_ethash) = get_contract_data("./BankStatements", [])
    
#contract_data_ethash = "0ee9e66884C1d4b531E3E17e0eb402E861A2aCC2"    

#retVal = call_const_function(ethereum_key, 0, contract_data_ethash, abi_ethash, "secrets", [0])
#print str(retVal)

#sd

# gave premission to ethereum_key
# didn't give prem to ethereum_key2

#ethereum_key2 = utils.sha3("erez")
#print str(can_read(ethereum_key,0))
#print str(can_read(ethereum_key2,0))

