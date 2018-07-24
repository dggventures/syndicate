pragma solidity ^0.4.24;
pragma experimental "v0.5.0";

import "./NFToken.sol";
import "./SafeMath.sol";

contract NFTokenMock is NFToken {
  using SafeMath for uint;

  uint public token_id;

  /// @dev Mint an NFT
  /// @param receiver Address of the owner of the newly minted NFT
  /// @return Token ID
  function mintInternalMock(address receiver) public {
    token_id = mintInternal(receiver);
  }
}