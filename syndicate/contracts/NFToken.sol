pragma solidity ^0.4.21;
pragma experimental "v0.5.0";

import "./ERC165.sol";
import "./ERC721.sol";

contract NFToken is ERC165, ERC721, ERC721Enumerable, ERC721Metadata {
  struct Account {
    uint256[] tokens;
    mapping(address => bool) approved_operator;
  }

  struct Token {
    uint256 index;
    address approved_agent;
    address owner;
  }

  uint256 total_tokens;
  mapping(uint256 => Token) tokens;
  mapping(address => Account) accounts;
  
  string public name = "";
  string public symbol = "";

  function balanceOf(address account) external view returns (uint256) {
    return accounts[account].tokens.length;
  }

  function ownerOf(uint256 token_id) external view returns (address) {
    return tokens[token_id].owner;
  }

  function totalSupply() external view returns (uint256) {
    return total_tokens;
  }

  function safeTransferFrom(address from, address to, uint256 token_id, bytes data) public canTransfer(token_id) {
    commitTransfer(from, to, token_id);
    notifyTransfer(from, to, token_id, data);
  }

  function safeTransferFrom(address from, address to, uint256 token_id) external canTransfer(token_id) {
    safeTransferFrom(from, to, token_id, "");
  }

  function transferFrom(address from, address to, uint256 token_id) external canTransfer(token_id) {
    commitTransfer(from, to, token_id);
  }

  function commitTransfer(address from, address to, uint256 token_id) private {
    // Overwrite with last element before shortening array
    uint256[] storage from_tokens = accounts[from].tokens;
    from_tokens[tokens[token_id].index] = from_tokens[from_tokens.length - 1];
    from_tokens.length -= 1;

    // Update token ownership information
    tokens[token_id].index = accounts[to].tokens.push(token_id) - 1;
    tokens[token_id].owner = to;
    tokens[token_id].approved_agent = address(0);
    emit Transfer(from, to, token_id);
  }

  function notifyTransfer(address from, address to, uint256 token_id, bytes data) private {
    ERC721TokenReceiver receiver = ERC721TokenReceiver(to);
    bytes4 res = receiver.onERC721Received(from, token_id, data);
    require(res == receiver.onERC721Received.selector);
  }

  modifier canTransfer(uint256 token_id) {
    address token_owner = tokens[token_id].owner;
    require(msg.sender == token_owner ||
            msg.sender == tokens[token_id].approved_agent ||
            accounts[token_owner].approved_operator[msg.sender]);
    _;
  }

  function approve(address approved, uint256 token_id) external {
    require(msg.sender == tokens[token_id].owner);
    tokens[token_id].approved_agent = approved;
    emit Approval(msg.sender, approved, token_id);
  }

  function setApprovalForAll(address operator, bool approved) external {
    accounts[msg.sender].approved_operator[operator] = approved;
    emit ApprovalForAll(msg.sender, operator, approved);
  }

  function getApproved(uint256 token_id) external view returns (address) {
    return tokens[token_id].approved_agent;
  }

  function isApprovedForAll(address account, address operator) external view returns (bool) {
    return accounts[account].approved_operator[operator];
  }

  function tokenByIndex(uint256 index) external view returns (uint256) {
    require(index < total_tokens);
    return index;
  }

  function tokenOfOwnerByIndex(address account, uint256 index) external view returns (uint256) {
    require(index < accounts[account].tokens.length);
    return accounts[account].tokens[index];
  }

  function tokenURI(uint256 token_id) external view returns (string) {
    return "";
  }

  function supportsInterface(bytes4 interfaceID) external view returns (bool) {
    return 0x01ffc9a7 == interfaceID || 0x80ac58cd == interfaceID || 0x780e9d63 == interfaceID ||
           0x5b5e139f == interfaceID;


    /* May be of use when there's better function selection support in solidity
    return interfaceID == this.balanceOf.selector ^ this.ownerOf.selector ^
                          this.safeTransferFrom(address, address, uint256).selector ^
                          this.safeTransferFrom(address, address, uint256, bytes).selector ^
                          this.transferFrom.selector ^ this.approve.selector ^
                          this.setApprovalForAll.selector ^ this.getApproved.selector ^
                          this.isApprovedForAll.selector ||
           interfaceID == this.name.selector ^ this.symbol.selector ^
                          this.tokenURI.selector ||
           interfaceID == this.totalSupply.selector ^
                          this.tokenByIndex.selector ^
                          this.tokenOfOwnerByIndex ||
           interfaceID == this.supportsInterface.selector;
    */
  }
}