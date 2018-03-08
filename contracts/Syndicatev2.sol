pragma solidity ^0.4.20;

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
  address public investment_address; // 0x77D0f9017304e53181d9519792887E78161ABD25;
  // Major partner address
  address public major_partner_address; // 0x8f0592bDCeE38774d93bC1fd2c97ee6540385356;
  // Minor partner address
  address public minor_partner_address; // 0xC787C3f6F75D7195361b64318CE019f90507f806;
  // Gas used for transfers.
  uint public gas = 1000;  
  // How much money was invested in the contract
  uint public investment_pool = 0;
  // The amount of tokens the contract has received in its lifetime
  uint public total_tokens = 0;
  // Last known contract token balance
  uint public token_balance = 0;
  // Address of the token
  EIP20Token public token;
  // We record tokens associated with the investment pool to avoid touching them with
  // the approve_unwanted_tokens failsafe mechanism.
  mapping(address => bool) public token_history;
  // Whitelisting enable flag
  bool public whitelist = false;
  // Whitelisting of investors
  mapping(address => bool) public investors;
  // Balances of investors
  mapping(address => Investor) public balances;
  
  struct Investor {
    uint withdrawn_tokens;
    uint invested;
  }
  
  function Syndicatev2(EIP20Token token_contract, address investment, address major_partner, address minor_partner) public {
    token = token_contract;
    investment_address = investment;
    major_partner_address = major_partner;
    minor_partner_address = minor_partner;
  }

  // Transfer some funds to the target investment address.
  function execute_transfer(uint transfer_amount) internal {
    require(!whitelist || investors[msg.sender]);
    require(transfer_amount > 0);
    
    investment_pool = investment_pool.add(transfer_amount);
    balances[msg.sender].invested = balances[msg.sender].invested.add(transfer_amount);
    
    // Major fee is 60% * (1/11) * value = 6 * value / (10 * 11)
    uint major_fee = transfer_amount * 6 / (10 * 11);
    // Minor fee is 40% * (1/11) * value = 4 * value / (10 * 11)
    uint minor_fee = transfer_amount * 4 / (10 * 11);
    
    // Send the rest
    // TODO: add extra gas in this call to allow storage modifications to the crowdsale
    require(investment_address.call.gas(gas).value(transfer_amount - major_fee - minor_fee)());
    // Check new token balance
    uint token_delta = token.balanceOf(address(this)).sub(token_balance);
    total_tokens = total_tokens.add(token_delta);
    token_balance = token_balance.add(token_delta);
    
    require(major_partner_address.call.gas(gas).value(major_fee)());
    require(minor_partner_address.call.gas(gas).value(minor_fee)());
  }
  
  // Sets the amount of gas allowed to investors
  function set_transfer_gas(uint transfer_gas) public onlyOwner {
    gas = transfer_gas;
  }
  
  // We can use this function to move unwanted tokens in the contract
  function approve_unwanted_tokens(EIP20Token token_contract, address dest, uint value) public onlyOwner {
    require(!token_history[token_contract]);
    require(token_contract.approve(dest, value));
  }
  
  // This contract is designed to have no balance.
  // However, we include this function to avoid stuck value by some unknown mishap.
  function emergency_withdraw() public onlyOwner {
    require(msg.sender.call.gas(gas).value(this.balance)());
  }
  
  /* Function to set the token accordingly in the case it changes its address
   */
  function update_token(EIP20Token token_contract) public onlyOwner {
    require(address(token_contract) != 0);
    token = token_contract;
    token_history[token_contract] = true;
  }

  /* Function to update the token balance of this contract
   */
  function update_balances() public onlyOwner {
    uint token_delta = token.balanceOf(address(this)).sub(token_balance);
    total_tokens = total_tokens.add(token_delta);
    token_balance = token_balance.add(token_delta);
  }

  /* Allows or disallows an address to invest
   * @param investor The address to allow or disallow
   * @param allowed Set to true to allow or false to disallow
   */
  function whitelist(address investor, bool allowed) public onlyOwner {
    investors[investor] = allowed;
  }
  
  /* Function to get the token balance of an investor
   */
  function token_balance(address investor) public view returns (uint256) {
    uint investor_tokens = balances[investor].invested.mul(total_tokens).div(investment_pool);
    return investor_tokens.sub(balances[investor].withdrawn_tokens);
  }
  
  /* Helper function for investor token withdrawal
   */
  function withdraw_tokens() internal returns (uint) {
    require(balances[msg.sender].invested > 0);
    uint tokens = token_balance(msg.sender);
    balances[msg.sender].withdrawn_tokens = balances[msg.sender].withdrawn_tokens.add(tokens);
    token_balance = token_balance.sub(tokens);
    return tokens;
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