<img src="https://github.com/dggventures/syndicate/blob/master/images/dg-global-ventures.png" 
alt="DG Global Ventures" width="293" height="64" border="0" align="left"/>
<img src="https://github.com/dggventures/syndicate/blob/master/images/coinfabrik.png" 
alt="CoinFabrik" width="250" height="64" border="0" align="right" />
<br>
</br>
<br>
</br>
<br>
</br>
## Syndicate Investment Fund Smart Contract

## Overview
The Syndicate Smart Contract template was developed to receive investments to buy ICO tokens, buy the tokens negotiating a bonus price for the whole amount of Ethers, and finally, investors receive the ICO tokens within the contract. Depending on the project, vesting could apply for the tokens.
  
<p align="center">
<img src="https://github.com/dggventures/syndicate/blob/master/images/syndicate-workflow.png" 
alt="DG Global Ventures" width="681" height="417" border="0" align="center" margin-left="10%" />
</p>


## Parties
**Administrators:** a list of addresses with a related % for each one. E.g.: [0x1111, 30%, 0x2222, 70%]. The total % must SUM exactly 100%. These addresses receive the administration fee and the bonus if it applies.

**Contract developer (CoinFabrik):** the address which will be able to make configuration changes.

**Investors:** the addresses which send ether to the smart contract and will receive tokens in exchange.

## Details

**Steps:**
1) Investors send their Ethers to the Syndicate Smart Contract.
2) Contract Developer calls a function of the Syndicate Smart Contract to buy the tokens from the ICO Smart Contract specifying the starting token price which will be the base to calculate the bonus fee. 1% of the Ethers are sent to the administrators. 
NOTE: If this function is not called after the buy period (30 days), investors can withdraw the ethers including the administration fee.
3) After each vesting period (if applies), Contract Developer will call the end of locking function specifying the token price at the end of the period (CoinMarketCap price at the 0:00 EST after 1 year exactly after the token purchase). After this call, investors can withdraw their tokens subtracting the bonus fee. The bonus fee (20% over 2X of the original price) is paid if the token value increases above 2 times the original value (e.g.: if the token price was original $10 and after one year is $25, bonus fee will be ($25-2*$10)*0.2 = $1 per token). This bonus is paid in tokens. 
NOTE: If this function is not called after 10 days from the end of the locking period, investors can withdraw tokens without paying the bonus fee. 

## Coming Soon

- Implement ERC20 or ERC721 to provide liquidity to investors while the tokens are frozen. They will be able to sell the future possession of the tokens.

## Case Studies

These are the ICOs where we participate with our technology:

<a href="https://github.com/dggventures/syndicate/tree/master/mainframe">Mainframe</a>
<a href="https://github.com/dggventures/syndicate/tree/master/human-protocol">Human Protocol</a>
<a href="https://github.com/dggventures/syndicate/tree/master/lottery">Lottery</a>
<a href="https://github.com/dggventures/syndicate/tree/master/tari">TARI</a>
<a href="https://github.com/dggventures/syndicate/tree/master/wibson">Wibson</a>
<a href="https://github.com/dggventures/syndicate/tree/master/pin-protocol">Pin Protocol</a>



