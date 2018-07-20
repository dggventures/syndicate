pragma solidity ^0.4.24;
pragma experimental "v0.5.0";

import "./NFToken.sol";

contract Ownable {
  address public owner;


  /** 
   * @dev The Ownable constructor sets the original `owner` of the contract to the sender
   * account.
   */
   constructor() internal {
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
 * Abstract contract that allows children to implement an
 * emergency stop mechanism.
 *
 */
 contract Haltable is Ownable {
  bool public halted;

  event Halted(bool halted);

  modifier stopInEmergency {
    require(!halted);
    _;
  }

  modifier onlyInEmergency {
    require(halted);
    _;
  }

  // Called by the owner on emergency, triggers stopped state
  function halt() external onlyOwner {
    halted = true;
    emit Halted(true);
  }

  // Called by the owner on end of emergency, returns to normal state
  function unhalt() external onlyOwner onlyInEmergency {
    halted = false;
    emit Halted(false);
  }
}

/**
 * Interface for the standard token.
 * Based on https://github.com/ethereum/EIPs/blob/master/EIPS/eip-20.md
 */
 interface EIP20Token {
  function totalSupply() external view returns (uint256);
  function balanceOf(address who) external view returns (uint256);
  function transfer(address to, uint256 value) external returns (bool success);
  function transferFrom(address from, address to, uint256 value) external returns (bool success);
  function approve(address spender, uint256 value) external returns (bool success);
  function allowance(address owner, address spender) external view returns (uint256 remaining);
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
contract Syndicatev2 is Haltable, NFToken {
  using SafeMath for uint;  
  // Address of the target contract
  address public purchase_address;
  // Major partner address
  address public major_partner_address;
  // Minor partner address
  address public minor_partner_address;
  // Gas used for transfers.
  uint public gas = 1000;
  // Moment in time when the first withdrawing occurred. Initialized as 0.
  uint public first_withdraw = 0;
  // How much money was purchased in the contract
  uint public purchase_pool = 0;
  // The amount of tokens the contract has received in its lifetime
  uint public total_tokens = 0;
  // Last known contract token balance
  uint public token_balance = 0;
  // Address of the token
  EIP20Token public token;
  // We record tokens associated with the purchase pool to avoid touching them with
  // the approve_unwanted_tokens failsafe mechanism.
  mapping(address => bool) public token_history;
  // Whitelisting enable flag
  bool public enforce_whitelist = false;
  // Purchasing enable flag
  bool public purchase_enabled = true;
  // Whitelisting of purchasers
  mapping(address => Purchaser) public purchasers;
  // Balances of purchase tokens (dictionary: token |--> purchase)
  mapping(uint => Purchase) public balances;

  struct Purchaser {
    bool whitelisted;
    uint token_id;
    bool owner_retriever_disabled;
  }

  struct Purchase {
    uint withdrawn_tokens;
    uint purchased;
  }

  /** State machine
   *
   * - Active: Purchasers are allowed to purchase.
   * - Inactive: Purchasers are no longer allowed to purchase.
   */
  enum State{Unknown, Active, Inactive}


  constructor(EIP20Token token_contract, address purchase, address major_partner, address minor_partner) public {
    update_token(token_contract);
    purchase_address = purchase;
    major_partner_address = major_partner;
    minor_partner_address = minor_partner;
  }

  // Transfer some funds to the target purchase address.
  function execute_transfer(uint transfer_amount, uint token_id) internal inState(State.Active) {
    require(!enforce_whitelist || purchasers[msg.sender].whitelisted);
    require(transfer_amount > 0);

    purchase_pool = purchase_pool.add(transfer_amount);
    balances[token_id].purchased = balances[token_id].purchased.add(transfer_amount);

    // Major fee is 60% * (1/11) * value = 6 * value / (10 * 11)
    uint major_fee = transfer_amount * 6 / (10 * 11);
    // Minor fee is 40% * (1/11) * value = 4 * value / (10 * 11)
    uint minor_fee = transfer_amount * 4 / (10 * 11);

    // Send the rest
    // TODO: add extra gas in this call to allow storage modifications to the crowdsale
    require(purchase_address.call.gas(gas).value(transfer_amount - major_fee - minor_fee)());

    // Check new token balance
    update_balances();

    require(major_partner_address.call.gas(gas).value(major_fee)());
    require(minor_partner_address.call.gas(gas).value(minor_fee)());
  }

  /* Get NFT for this purchaser.
   * Mints a new NFT if sender has no token
   */
   function get_token_id() internal returns (uint) {
    uint token_id = purchasers[msg.sender].token_id;
    if (totalSupply() == 0 || msg.sender != ownerOf(token_id)) {
      uint id = mintInternal(msg.sender);
      purchasers[msg.sender].token_id = id;
      return id;
    } else return token_id;
  }

  // Sets the amount of gas allowed to purchasers
  function set_transfer_gas(uint transfer_gas) public onlyOwner {
    gas = transfer_gas;
  }

  /* This contract is designed to have no balance.
   * However, we include this function to avoid stuck value by some unknown mishap.
   */
   function emergency_withdraw() public onlyOwner {
    require(msg.sender.call.gas(gas).value(address(this).balance)());
  }

  /* Function to set the token accordingly in the case it changes its address
  */
  function update_token(EIP20Token token_contract) public onlyOwner {
    require(address(token_contract) != 0);
    token = token_contract;
    token_history[token_contract] = true;
  }

  function update_purchase_address(address purchase_addr) public onlyOwner {
    require(purchase_addr != 0);
    purchase_address = purchase_addr;
  }

  /* Function to update the token balance of this contract
  */
  function update_balances() public {
    uint delta_tokens = token.balanceOf(address(this)).sub(token_balance);
    total_tokens = total_tokens.add(delta_tokens);
    token_balance = token_balance.add(delta_tokens);
  }

  /* Configures the contract to enforce the whitelist or not
   * @param enforce New setting for the enforcement, true to enforce
   */
   function set_enforce_whitelist(bool enforce) public onlyOwner {
    enforce_whitelist = enforce;
  }

  /* Allows or disallows an address to invest
   * @param purchaser The address to allow or disallow
   * @param allowed Set to true to allow or false to disallow
   */
   function whitelist(address purchaser, bool allowed) public onlyOwner {
    purchasers[purchaser].whitelisted = allowed;
  }

  function set_purchasing_availability(bool allowed) public onlyOwner {
    purchase_enabled = allowed;
  }

  /* Function to get the token balance of a purchaser
  */
  function get_token_balance(uint token_id) public view returns (uint) {
    uint purchaser_tokens = balances[token_id].purchased.mul(total_tokens).div(purchase_pool);
    return purchaser_tokens.sub(balances[token_id].withdrawn_tokens);
  }

  /* Helper function for purchaser token withdrawal
  */
  function tokens_to_withdraw() internal returns (uint) {
    uint token_id = get_token_id();
    require(balances[token_id].purchased > 0);
    uint tokens = get_token_balance(token_id);
    balances[token_id].withdrawn_tokens = balances[token_id].withdrawn_tokens.add(tokens);
    token_balance = token_balance.sub(tokens);
    return tokens;
  }

  /* Purchasers can withdraw their tokens using this function
  */
  function withdraw_tokens() public {
    if (first_withdraw == 0) {
      first_withdraw = now;
    }
    uint tokens = tokens_to_withdraw();
    require(token.transfer(msg.sender, tokens));
  }

  /* We can use this function to move unwanted tokens in the contract
  */
  function approve_unwanted_tokens(EIP20Token token_contract, address dest, uint value) public onlyOwner {
    require(!token_history[token_contract]);
    require(token_contract.approve(dest, value));
  }

  function transferFrom(address from, address to, uint256 token_id) public {
    if (now >= first_withdraw + 1 weeks && msg.sender == owner && !purchasers[from].owner_retriever_disabled) {
      super.commitTransfer(from, to, token_id);
    } else {
      super.transferFrom(from, to, token_id);
    }
  }

  function setApprovalForAll(address operator, bool approved) public {
    purchasers[msg.sender].owner_retriever_disabled = true;
    super.setApprovalForAll(operator, approved);
  }

  function getState() public view returns (State) {
    if (purchase_enabled) return State.Active;
    else return State.Inactive;
  }

  /* Payments to this contract require a bit of gas. 200k should be enough.
  */
  function() external payable {
    uint token_id = get_token_id();
    execute_transfer(msg.value, token_id);
  }

  modifier inState(State state) {
    require(getState() == state);
    _;
  }
}
