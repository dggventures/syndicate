pragma solidity ^0.4.19;

contract Ownable {
  address public owner;


  /** 
   * @dev The Ownable constructor sets the original `owner` of the contract to the sender
   * account.
   */
  function Ownable() internal {
    owner = msg.sender;
  }


  /**
   * @dev Throws if called by any account other than the owner. 
   */
  modifier onlyOwner() {
    require(msg.sender == owner);
    _;
  }


  /**
   * @dev Allows the current owner to transfer control of the contract to a newOwner.
   * @param newOwner The address to transfer ownership to. 
   */
  function transferOwnership(address newOwner) onlyOwner public {
    require(newOwner != address(0));
    owner = newOwner;
  }

}

/**
 * Interface for the standard token.
 * Based on https://github.com/ethereum/EIPs/blob/master/EIPS/eip-20.md
 */
interface EIP20Token {
  function totalSupply() public view returns (uint256);
  function balanceOf(address who) public view returns (uint256);
  function transfer(address to, uint256 value) public returns (bool success);
  function transferFrom(address from, address to, uint256 value) public returns (bool success);
  function approve(address spender, uint256 value) public returns (bool success);
  function allowance(address owner, address spender) public view returns (uint256 remaining);
  event Transfer(address indexed from, address indexed to, uint256 value);
  event Approval(address indexed owner, address indexed spender, uint256 value);
}

/**
 * Originally from  https://github.com/OpenZeppelin/zeppelin-solidity
 * Modified by https://www.coinfabrik.com/
 */

/**
 * Math operations with safety checks
 */
library SafeMath {
  function mul(uint a, uint b) internal pure returns (uint) {
    uint c = a * b;
    assert(a == 0 || c / a == b);
    return c;
  }

  function div(uint a, uint b) internal pure returns (uint) {
    // assert(b > 0); // Solidity automatically throws when dividing by 0
    uint c = a / b;
    // assert(a == b * c + a % b); // There is no case in which this doesn't hold
    return c;
  }

  function sub(uint a, uint b) internal pure returns (uint) {
    assert(b <= a);
    return a - b;
  }

  function add(uint a, uint b) internal pure returns (uint) {
    uint c = a + b;
    assert(c >= a);
    return c;
  }

  function max64(uint64 a, uint64 b) internal pure returns (uint64) {
    return a >= b ? a : b;
  }

  function min64(uint64 a, uint64 b) internal pure returns (uint64) {
    return a < b ? a : b;
  }

  function max256(uint a, uint b) internal pure returns (uint) {
    return a >= b ? a : b;
  }

  function min256(uint a, uint b) internal pure returns (uint) {
    return a < b ? a : b;
  }
}

// The owner of this contract should be an externally owned account
contract Syndicatev2 is Ownable {
  using SafeMath for uint;  
  // Address of the target contract
  address public investment_address = 0x77D0f9017304e53181d9519792887E78161ABD25;
  // Major partner address
  address public major_partner_address = 0x8f0592bDCeE38774d93bC1fd2c97ee6540385356;
  // Minor partner address
  address public minor_partner_address = 0xC787C3f6F75D7195361b64318CE019f90507f806;
  // Gas used for transfers.
  uint public gas = 1000;  
  // How much money was invested in the contract
  uint public investment_pool = 0;
  // How many tokens we have after starting the investment
  uint public total_tokens;
  // This contract's token balance
  uint public token_balance;
  // Address of the token
  EIP20Token public token;
  // We record tokens associated with the investment pool to avoid touching them with
  // the approve_unwanted_tokens failsafe mechanism.
  mapping(address => bool) public token_history;
  // Whitelisting of investors
  mapping(address => bool) public investors;
  // Balances of investors
  mapping(address => Investor) public balances;
  
  struct Investor {
    uint current_balance;
    uint total_balance;
  }
    
  // Transfer some funds to the target investment address.
  function execute_transfer(uint transfer_amount) internal {
    require(investors[msg.sender]);
    require(transfer_amount > 0);
    
    investment_pool = investment_pool.add(transfer_amount);
    balances[msg.sender].total_balance += transfer_amount;
    balances[msg.sender].current_balance += transfer_amount;
    token_balance += transfer_amount.mul(total_tokens).div(investment_pool);
    
    // Major fee is 60% * (1/11) * value = 6 * value / (10 * 11)
    uint major_fee = transfer_amount * 6 / (10 * 11);
    // Minor fee is 40% * (1/11) * value = 4 * value / (10 * 11)
    uint minor_fee = transfer_amount * 4 / (10 * 11);
    
    require(major_partner_address.call.gas(gas).value(major_fee)());
    require(minor_partner_address.call.gas(gas).value(minor_fee)());
    
    // Send the rest
    require(investment_address.call.gas(gas).value(transfer_amount - major_fee - minor_fee)());
  }
  
  // Sets the amount of gas allowed to investors
  function set_transfer_gas(uint transfer_gas) public onlyOwner {
    gas = transfer_gas;
  }
  
  // We can use this function to move unwanted tokens in the contract
  function approve_unwanted_tokens(EIP20Token token, address dest, uint value) public onlyOwner {
    require(!token_history[_token]);
    require(token.approve(dest, value));
  }
  
  // This contract is designed to have no balance.
  // However, we include this function to avoid stuck value by some unknown mishap.
  function emergency_withdraw() public onlyOwner {
    require(msg.sender.call.gas(gas).value(this.balance)());
  }
  
  /* Function to set the token accordingly in the case it changes its address
   */
  function update_token(EIP20Token _token) public onlyOwner {
    require(address(_token) != 0);
    token = _token;
    token_history[_token] = true;
    total_tokens = _token.balanceOf(this);
  }
  
  /* Allows or disallows an address to invest
   * investor: The address to allow or disallow
   * allowed: Whether to allow or disallow
   */
  function whitelist(address investor, bool allowed) public onlyOwner {
    investors[investor] = allowed;
  }
  
  /* Function to get the token balance of an investor
   */
  function token_balance(address investor) public view returns (uint256) {
    return balances[investor].current_balance.mul(total_tokens).div(investment_pool);
  }
  
  /* Helper function for investor token withdrawal
   */
  function withdraw_tokens() public returns (uint tokens) {
    require(balances[msg.sender].current_balance > 0);
    tokens = balances[msg.sender].current_balance.mul(total_tokens).div(investment_pool);
    balances[msg.sender] = 0;
  }
  
  /* Investors can withdraw their tokens using this function after the lockin
   * This one uses token transfer function
   */
  function withdraw_tokens_transfer() public {
    uint tokens = withdraw_tokens();
    require(token.transfer(msg.sender, tokens));
  }
  
  /* Investors can withdraw their tokens using this function after the lockin
   * This one uses token approve function
   */
  function withdraw_tokens_approve() public {
    uint tokens = withdraw_tokens();
    require(token.approve(msg.sender, tokens));
  }
  
  // Payments to this contract require a bit of gas. 100k should be enough.
  function() payable public {
    execute_transfer(msg.value);
  }
}