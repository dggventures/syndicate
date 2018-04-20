pragma solidity ^0.4.22;

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
 * Based on https://github.com/ethereum/EIPs/blob/master/EIPS/eip-20-token-standard.md
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


/* The owner of this contract should be an externally owned account
 */
contract SimpleTokenPurchase is Ownable {

  // Address of the target contract
  address public purchase_address = 0x8ffC991Fc4C4fC53329Ad296C1aFe41470cFFbb3;
  // Major partner address
  address public first_partner_address = 0x8ffC991Fc4C4fC53329Ad296C1aFe41470cFFbb3;
  // Minor partner address
  address public second_partner_address = 0x8ffC991Fc4C4fC53329Ad296C1aFe41470cFFbb3;
  // Third partner address
  address public third_partner_address = 0x8ffC991Fc4C4fC53329Ad296C1aFe41470cFFbb3;
  // Additional gas used for transfers.
  uint public gas = 1000;
  // Address of the token contract
  EIP20Token token;
  // We record tokens associated with the investment pool to avoid touching them with
  // the approve_unwanted_tokens failsafe mechanism.
  mapping(address => bool) public token_history;

  function TokenPurchase() public {
    update_token(address(0));
    require(token != address(0));
  }

  /* Payments to this contract require a bit of gas. 100k should be enough.
   */
  function() payable public {
    execute_transfer(msg.value);
  }

  // First fee is 1.5%
  uint constant private first_proportion = 15;
  // Second fee is 1%
  uint constant private second_proportion = 1;
  // Third fee is 2.5%
  uint constant private third_proportion = 25;
  // Divisor must be chosen according to the desired fees above
  uint constant private ether_divisor = 1000;

  /* Transfer some funds to the target purchase address.
   */
  function execute_transfer(uint transfer_amount) internal {
    uint first_fee = transfer_amount * first_proportion / ether_divisor;
    uint second_fee = transfer_amount * second_proportion / ether_divisor;
    uint third_fee = transfer_amount * third_proportion / ether_divisor;

    require(first_partner_address.call.gas(gas).value(first_fee)());
    require(second_partner_address.call.gas(gas).value(second_fee)());
    require(third_partner_address.call.gas(gas).value(third_fee)());

    // Send the rest
    uint purchase_amount = transfer_amount - first_fee - second_fee - third_fee;
    require(purchase_address.call.gas(gas).value(purchase_amount)());
  }

  /* Sets the amount of additional gas allowed to addresses called
   * @dev This allows transfers to multisigs that use more than 2300 gas in their fallback function.
   */
  function set_transfer_gas(uint transfer_gas) public onlyOwner {
    gas = transfer_gas;
  }

  /* We can use this function to move unwanted tokens in the contract
   */
  function approve_unwanted_tokens(EIP20Token token, address dest, uint value) public onlyOwner {
    token.approve(dest, value);
  }

  /* This contract is designed to have no balance.
   * However, we include this function to avoid stuck value by some unknown mishap.
   */
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

  /* This function provides the withdrawal mechanism for purchased tokens
   */
  function withdraw_tokens() public {
    require(msg.sender == owner || msg.sender == first_partner_address ||
            msg.sender == second_partner_address || msg.sender == third_partner_address);
    
    uint token_balance = token.balanceOf(address(this));
    uint total = first_proportion + second_proportion + third_proportion;

    uint first_partner_tokens = token_balance * first_proportion / total;
    uint second_partner_tokens = token_balance * second_proportion / total;
    uint third_partner_tokens = token_balance - first_partner_tokens - second_partner_tokens;

    require(token.transfer(first_partner_address, first_partner_tokens));
    require(token.transfer(second_partner_address, second_partner_tokens));
    require(token.transfer(third_partner_address, third_partner_tokens));
  }

  /* This contract is designed to have no balance.
   * However, we include this function to avoid stuck value by some unknown mishap.
   */
  function emergency_withdraw_tokens() public onlyOwner {
    require(msg.sender.call.gas(gas).value(this.balance)());
  }

}
