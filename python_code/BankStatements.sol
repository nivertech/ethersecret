pragma solidity ^0.4.8;

contract BankStatements {

    struct Secret {
        address owner;
        address reader;
        uint    startTime;
        uint    endTime;
        
        uint    secret;
    }
    
    Secret[] public secrets;
    
    function BankStatements() {}
    
    function setPremission( uint startTime, uint endTime, address reader, uint secretIndex ) {
        Secret secret = secrets[secretIndex];
        if( secret.owner != msg.sender ) throw;
        secret.reader = reader;
        secret.startTime = startTime;
        secret.endTime = endTime;
    }
    
    function newSecret( uint _secret ) {
        Secret memory secret;
        secret.owner = msg.sender;
        secret.secret = _secret;
        //= new Secret({owner: msg.sender, secret: _secret});
        secrets.push(secret);
    }
    
    function getPremission( uint secretIndex ) constant returns(bool) {
        Secret secret = secrets[secretIndex];
        if( secret.reader != msg.sender ) return false;
        if( now < secret.startTime ) return false;
        if( now > secret.endTime ) return false;
        
        return true;

    }
}