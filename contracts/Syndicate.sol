/*
 * Copyright (C) 2018 Coinfabrik, DG Global Ventures
 * All rights reserved. Contact: https://www.coinfabrik.com
 **/

pragma solidity ^0.4.18;

import "EIP20Token.sol";
import "Ownable.sol";
import "SafeMath.sol";

contract Syndicate is Ownable {
    using SafeMath for uint;
    // We are going to define admin ratios in parts of ratio_sum
    uint private constant ratio_sum = 100000;
    // Maximum amount of wei to receive from investors
    uint private constant investment_cap = 1000 ether;
    // In parts of 100, how much money we take away from transactions to admins
    uint private constant admin_fee = 1;
    // In parts of 100, how many tokens we take away for admins if investment is sucessful
    // This does not affect the tokens needed to reach the success threshold
    uint private constant success_fee = 20;
    // Percentage of price increase in order to consider the investment successful
    uint private constant success_threshold = 200;
    // How much time we have to start the investment after contract creation
    uint private constant investment_period = 30 days;
    // How much time the tokens are going to get locked after the start
    uint private constant lock_period = 1 years;
    // How much time we have to end the investment to assign admin bonuses
    uint private constant end_window = 10 days;

    struct Admin {
        address addr;
        uint ratio;
        uint fee_balance;
        bool wants_refund;
    }

    // Syndicate admins, they get bonus payments if investment is sucessful
    Admin[] public admins;
    // Balances of investors
    mapping(address => uint) public balances;
    // We record tokens associated with the investment pool to avoid touching them with
    //  the approve_unwanted_tokens failsafe mechanism.
    mapping(address => bool) public token_history;
    // Whitelisting of investors
    mapping(address => bool) public investors;

    // How much money was invested in the contract
    uint public investment_pool = 0;
    // How many signs from admins we have for refunding the contract
    uint public refund_signs = 0;
    // Address of the token
    EIP20Token public token;
    // How many tokens we have after starting the investment
    uint public total_tokens;
    // The price at the start of lockin
    uint public start_price;
    // When the deadline for starting the investment occurs
    uint public start_deadline;
    // When the lockin ends
    uint public end_time;

    /* The state of the contract
     *
     * We begin at Investment state where investors are able to send ethers
     * Then we can buy tokens using all the ether minus the fees.
     * This starts a lockin process, entering Started state.
     * If this doesn't happen before investment_period, investors can retrieve all their ether.
     *
     * After the lock_period, we can properly end the investment entering Ended state.
     * When investment ends admins get paid their bonuses if investment was sucessful,
     * and investors are also allowed to withdraw their tokens.
     * If this doesn't happen before end_window, investors can retrieve all their tokens.
     *
     * There is also two refund states in case something goes wrong before or after the lockin.
     * These can be activated if all admins sign a refund using a function
     */
    enum State {
        Investment,
        Started,
        Ended,
        RefundEther,
        RefundTokens
    }

    State public state;

    /* Contract constructor
     * admin_addresses: List of addresses of admins
     * admin_ratios: Respective ratios of said admins
     */
    function Syndicate(address[] admin_addresses, uint[] admin_ratios) public {
        require(admin_ratios.length == admin_addresses.length);
        uint sum = 0;
        for (uint i = 0; i < admin_ratios.length; i++) {
            require(admin_ratios[i] > 0 && admin_addresses[i] != 0);
            sum = sum.add(admin_ratios[i]);
            admins.push(Admin(admin_addresses[i], admin_ratios[i], 0, false));
        }
        require(sum == ratio_sum);
        state = State.Investment;
        start_deadline = now + investment_period;
    }

    /* Allows or disallows an address to invest
     * investor: The address to allow or disallow
     * allowed: Whether to allow or disallow
     */
    function whitelist(address investor, bool allowed) public onlyOwner {
        investors[investor] = allowed;
    }

    /* Investors may invest using this function, before the lockin period
     */
    function buy() public payable {
        require(investors[msg.sender]);
        require(msg.value > 0 && state == State.Investment);
        require(investment_pool.add(msg.value) <= investment_cap);
        balances[msg.sender] = balances[msg.sender].add(msg.value);
        investment_pool = investment_pool.add(msg.value);
    }

    /* We can start the lockin using this function
     * Admins will get paid their corresponding fees and tokens will be bought
     * ico: The address of the ICO selling the tokens
     * _token: The address of the token we are going to invest in
     * price: The price of the token at the moment of this call
     */
    function start(address ico, EIP20Token _token, uint price) public onlyOwner {
        require(ico != 0 && address(_token) != 0);
        require(state == State.Investment && now <= start_deadline);
        state = State.Started;
        uint fee_pool = investment_pool.mul(admin_fee).div(100);
        // Set admin fees
        for (uint i = 0; i < admins.length; i++) {
            admins[i].fee_balance = fee_pool.mul(admins[i].ratio).div(ratio_sum);
        }
        // Here be dragons
        require(ico.call.value(investment_pool.sub(fee_pool))());
        total_tokens = _token.balanceOf(this);
        start_price = price;
        token = _token;
        token_history[_token] = true;
        end_time = now + lock_period;
    }

    /* Function to set the token accordingly in the case it changes its address
     */
    function update_token(EIP20Token _token) public onlyOwner {
        require(state == State.Started && address(_token) != 0);
        token = _token;
        token_history[_token] = true;
        total_tokens = _token.balanceOf(this);
    }

    /* Function for admins to withdraw their fees after start
     */
    function withdraw_fees() public {
        require(state != State.Investment);
        for (uint i = 0; i < admins.length; i++) {
            if (admins[i].addr == msg.sender) {
                require(admins[i].fee_balance > 0);
                uint admin_fee_balance = admins[i].fee_balance
                admins[i].fee_balance = 0;
                msg.sender.transfer(admin_fee_balance);
            }
        }
    }

    /* Function to get the token balance of an investor
     */
    function token_balance(address investor) public view returns (uint256) {
        require(state == State.Started || state == State.Ended ||
                state == State.RefundTokens);
        return balances[investor].mul(total_tokens).div(investment_pool);
    }

    /* We can end the lockin using this function
     * Admins will get paid tokens if the investment was sucessful
     * price: The price of the token at the moment of this call
     */
    function end(uint price) public onlyOwner {
        require(state == State.Started);
        require(end_time < now && now < end_time + end_window);
        state = State.Ended;
        uint threshold = start_price.mul(success_threshold).div(100);
        // If we reach the threshold
        if (price > threshold) {
            // We take away 20% for the admins except the threshold
            uint admins_bonus = price.sub(threshold).mul(success_fee).div(100);
            uint admins_tokens = admins_bonus.mul(total_tokens).div(price);
            for (uint i = 0; i < admins.length; i++) {
                uint tokens = admins_tokens.mul(admins[i].ratio).div(ratio_sum);
                require(token.transfer(admins[i].addr, tokens));
            }
            total_tokens = total_tokens.sub(admins_tokens);
        }
    }

    /* Helper function for investor token withdrawal
     */
    function withdraw_tokens() internal returns (uint tokens) {
        require(balances[msg.sender] > 0);
        require(state == State.Ended || state == State.RefundTokens ||
                (state == State.Started && end_time + end_window < now));
        tokens = balances[msg.sender].mul(total_tokens).div(investment_pool);
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

    /* Investors can withdraw their ether using this function if refunded
     */
    function withdraw_ether() public {
        require(balances[msg.sender] > 0);
        require(state == State.RefundEther ||
                (state == State.Investment && start_deadline < now));
        uint balance = balances[msg.sender];
        balances[msg.sender] = 0;
        msg.sender.transfer(balance);
    }

    /* Admins can refund ether or tokens to the investors if something goes wrong
     * They all need to sign the refund using this function
     */
    function sign_refund() public {
        for (uint i = 0; i < admins.length; i++) {
            if (admins[i].addr == msg.sender && !admins[i].wants_refund) {
                admins[i].wants_refund = true;
                refund_signs = refund_signs.add(1);
            }
        }
        if (refund_signs == admins.length) {
            if (state == State.Investment) {
                state = State.RefundEther;
            }
            if (state == State.Started) {
                state = State.RefundTokens;
            }
        }
    }

    /* Admins can unsign their previously made refund using this function
     */
    function unsign_refund() public {
        for (uint i = 0; i < admins.length; i++) {
            if (admins[i].addr == msg.sender && admins[i].wants_refund) {
                admins[i].wants_refund = false;
                refund_signs = refund_signs.sub(1);
            }
        }
    }

    /* We can use this function to move unwanted tokens in the contract
     */
    function approve_unwanted_tokens(EIP20Token _token, address dest, uint value) public onlyOwner {
        require(!token_history[_token]);
        _token.approve(dest, value);
    }

    /* Fallback function, should be equivalent to calling buy
     */
    function () public payable {
        buy();
    }
}
