pragma solidity ^0.4.22;
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

  event Minted(address indexed owner, uint256 token_id);

  /// @notice Get the amount of NFTs owned by an address
  /// @param account An address for whom to query the balance
  /// @return The number of NFTs owned by `account`
  function balanceOf(address account) external view validAddress(account) returns (uint256) {
    return accounts[account].tokens.length;
  }

  /// @notice Find the owner of an NFT
  /// @param token_id The identifier for an NFT
  /// @return The address of the owner of the NFT
  function ownerOf(uint256 token_id) external view validIndex(token_id) returns (address) {
    return tokens[token_id].owner;
  }

  /// @notice Count NFTs tracked by this contract
  /// @return A count of valid NFTs tracked by this contract, where each one of
  ///  them has an assigned and queryable owner not equal to the zero address
  function totalSupply() external view returns (uint256) {
    return total_tokens;
  }

  /// @notice Transfers the ownership of an NFT from one address to another address
  /// @param from The current owner of the NFT
  /// @param to The new owner
  /// @param token_id The NFT to transfer
  /// @param data Additional data with no specified format, sent in call to `to`
  function safeTransferFrom(address from, address to, uint256 token_id, bytes data) public {
    // @dev Do not reorder these. The call of untrusted code should be done at the very end.
    commitTransfer(from, to, token_id);
    notifyTransfer(from, to, token_id, data);
  }

  /// @notice Transfers the ownership of an NFT from one address to another address
  /// @param from The current owner of the NFT
  /// @param to The new owner
  /// @param token_id The NFT to transfer
  function safeTransferFrom(address from, address to, uint256 token_id) external {
    safeTransferFrom(from, to, token_id, "");
  }

  /// @notice Transfer ownership of an NFT -- THE CALLER IS RESPONSIBLE
  ///  TO CONFIRM THAT `to` IS CAPABLE OF RECEIVING NFTs OR ELSE
  ///  THEY MAY BE PERMANENTLY LOST
  /// @param from The current owner of the NFT
  /// @param to The new owner
  /// @param token_id The NFT to transfer
  function transferFrom(address from, address to, uint256 token_id) external {
    commitTransfer(from, to, token_id);
  }

  function commitTransfer(address from, address to, uint256 token_id) private 
  validAddress(to) validIndex(token_id) canTransfer(token_id) {
    // Verify ownership of the token
    require(from == tokens[token_id].owner)

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
    uint256 code_size = 0;
    assembly {
      code_size := extcodesize(to)
    }
    if (code_size == 0)
      return;

    ERC721TokenReceiver receiver = ERC721TokenReceiver(to);
    bytes4 res = receiver.onERC721Received(from, token_id, data);
    require(res == receiver.onERC721Received.selector);
  }

  /// @notice Set or reaffirm the approved address for an NFT
  /// @param approved The new approved NFT controller
  /// @param token_id The NFT to approve
  function approve(address approved, uint256 token_id) external {
    address token_owner = tokens[token_id].owner;
    // Only owner or operator are allowed to approve another address.
    require(msg.sender == token_owner || accounts[token_owner].approved_operator[msg.sender]);
    tokens[token_id].approved_agent = approved;
    emit Approval(msg.sender, approved, token_id);
  }

  /// @notice Enable or disable approval for a third party ("operator") to manage
  ///  all your assets.
  /// @param operator Address to add to the set of authorized operators.
  /// @param approved True if the operators is approved, false to revoke approval
  function setApprovalForAll(address operator, bool approved) external {
    accounts[msg.sender].approved_operator[operator] = approved;
    emit ApprovalForAll(msg.sender, operator, approved);
  }

  /// @notice Get the approved address for a single NFT
  /// @param token_id The NFT to find the approved address for
  /// @return The approved address for this NFT, or the zero address if there is none
  function getApproved(uint256 token_id) external view validIndex(index) returns (address) {
    return tokens[token_id].approved_agent;
  }

  /// @notice Query whether an address is an authorized operator for another address
  /// @param account The address that owns the NFTs
  /// @param operator The address that acts on behalf of the owner
  /// @return True if `operator` is an approved operator for `account`, false otherwise
  function isApprovedForAll(address account, address operator) external view returns (bool) {
    return accounts[account].approved_operator[operator];
  }

  /// @notice Enumerate valid NFTs
  /// @param index A counter less than `totalSupply()`
  /// @return The token identifier for the `index`th NFT.
  function tokenByIndex(uint256 index) external view validIndex(index) returns (uint256) {
    return index;
  }

  /// @notice Enumerate NFTs assigned to an account
  /// @dev Throws if `index` >= `balanceOf(account)` or if
  ///  `account` is the zero address, representing invalid NFTs.
  /// @param account An address where we are interested in NFTs owned by them
  /// @param index A counter less than `balanceOf(account)`
  /// @return The token identifier for the `index`th NFT assigned to `account`.
  function tokenOfOwnerByIndex(address account, uint256 index) external view
  validAddress(account) returns (uint256) {
    require(index < accounts[account].tokens.length);
    return accounts[account].tokens[index];
  }

  /// @dev You may wish to override this function to provide context sensitive URIs.
  function tokenURI(uint256 /*token_id*/) external view returns (string) {
    return "";
  }

  /// @notice Query whether a contract implements an interface
  /// @param interface_id The interface identifier, as specified in ERC-165
  /// @return `true` if the contract implements `interface_id` and
  ///  `interface_id` is not 0xffffffff, `false` otherwise
  function supportsInterface(bytes4 interface_id) external view returns (bool) {
    return interface_id == hex"01ffc9a7" || interface_id == hex"80ac58cd" ||
           interface_id == hex"780e9d63" || interface_id == hex"5b5e139f";


    /* May be of use when there's better function selection support in solidity
    return interface_id == this.balanceOf.selector ^ this.ownerOf.selector ^
                          this.safeTransferFrom(address, address, uint256).selector ^
                          this.safeTransferFrom(address, address, uint256, bytes).selector ^
                          this.transferFrom.selector ^ this.approve.selector ^
                          this.setApprovalForAll.selector ^ this.getApproved.selector ^
                          this.isApprovedForAll.selector ||
           interface_id == this.name.selector ^ this.symbol.selector ^
                          this.tokenURI.selector ||
           interface_id == this.totalSupply.selector ^
                          this.tokenByIndex.selector ^
                          this.tokenOfOwnerByIndex ||
           interface_id == this.supportsInterface.selector;
    */
  }

  /// @dev Mint an NFT
  /// @param receiver Address of the owner of the newly minted NFT
  /// @returns Token ID
  function mintInternal(address receiver) internal returns (uint){
    uint token_id = total_tokens;
    uint index = accounts[receiver].tokens.push(token_id) - 1;
    tokens[token_id].index = index;
    tokens[token_id].owner = receiver;
    total_tokens += 1;
    emit Minted(receiver, token_id);
    emit Transfer(address(0), receiver, token_id);
    return token_id;
  }

  modifier canTransfer(uint256 token_id) {
    address token_owner = tokens[token_id].owner;
    require(msg.sender == token_owner ||
            msg.sender == tokens[token_id].approved_agent ||
            accounts[token_owner].approved_operator[msg.sender]);
    _;
  }

  modifier validIndex(uint256 token_id) {
    require(token_id < total_tokens);
    _;
  }

  modifier validAddress(address account) {
    require(account != address(0));
    _;
  }
}