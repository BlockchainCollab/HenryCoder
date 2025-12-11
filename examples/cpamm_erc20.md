# Constant Product Automated Market Maker (CPAMM) translation
In this variant we can see how Henry integrates ERC20 (FungibleToken) interface directly into the CPAMM contract. The difference from CPAMM is that we are implemenmting a proper ERC20

## Solidity source
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract CPAMM is ERC20 {
    IERC20 public immutable token0;
    IERC20 public immutable token1;

    uint256 public reserve0;
    uint256 public reserve1;

    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;

    constructor(address _token0, address _token1) {
        token0 = IERC20(_token0);
        token1 = IERC20(_token1);
    }

    function _update(uint256 _reserve0, uint256 _reserve1) private {
        reserve0 = _reserve0;
        reserve1 = _reserve1;
    }

    function swap(address _tokenIn, uint256 _amountIn)
        external
        returns (uint256 amountOut)
    {
        require(
            _tokenIn == address(token0) || _tokenIn == address(token1),
            "invalid token"
        );
        require(_amountIn > 0, "amount in = 0");

        bool isToken0 = _tokenIn == address(token0);
        (IERC20 tokenIn, IERC20 tokenOut, uint256 reserveIn, uint256 reserveOut)
        = isToken0
            ? (token0, token1, reserve0, reserve1)
            : (token1, token0, reserve1, reserve0);

        tokenIn.transferFrom(msg.sender, address(this), _amountIn);

        // 0.3% fee
        uint256 amountInWithFee = (_amountIn * 997) / 1000;
        amountOut =
            (reserveOut * amountInWithFee) / (reserveIn + amountInWithFee);

        tokenOut.transfer(msg.sender, amountOut);

        _update(
            token0.balanceOf(address(this)), token1.balanceOf(address(this))
        );
    }

    function addLiquidity(uint256 _amount0, uint256 _amount1)
        external
        returns (uint256 shares)
    {
        token0.transferFrom(msg.sender, address(this), _amount0);
        token1.transferFrom(msg.sender, address(this), _amount1);

        if (reserve0 > 0 || reserve1 > 0) {
            require(
                reserve0 * _amount1 == reserve1 * _amount0, "x / y != dx / dy"
            );
        }

        if (totalSupply == 0) {
            shares = _sqrt(_amount0 * _amount1);
        } else {
            shares = _min(
                (_amount0 * totalSupply) / reserve0,
                (_amount1 * totalSupply) / reserve1
            );
        }
        require(shares > 0, "shares = 0");
        _mint(msg.sender, shares);

        _update(
            token0.balanceOf(address(this)), token1.balanceOf(address(this))
        );
    }

    function removeLiquidity(uint256 _shares)
        external
        returns (uint256 amount0, uint256 amount1)
    {

        // bal0 >= reserve0
        // bal1 >= reserve1
        uint256 bal0 = token0.balanceOf(address(this));
        uint256 bal1 = token1.balanceOf(address(this));

        amount0 = (_shares * bal0) / totalSupply;
        amount1 = (_shares * bal1) / totalSupply;
        require(amount0 > 0 && amount1 > 0, "amount0 or amount1 = 0");

        _burn(msg.sender, _shares);
        _update(bal0 - amount0, bal1 - amount1);

        token0.transfer(msg.sender, amount0);
        token1.transfer(msg.sender, amount1);
    }

    function _sqrt(uint256 y) private pure returns (uint256 z) {
        if (y > 3) {
            z = y;
            uint256 x = y / 2 + 1;
            while (x < z) {
                z = x;
                x = (y / x + x) / 2;
            }
        } else if (y != 0) {
            z = 1;
        } else {
            z = 0;
        }
    }

    function _min(uint256 x, uint256 y) private pure returns (uint256) {
        return x <= y ? x : y;
    }
}


```

## ralph translation

### Settings
```json
{
  "optimize": false,
  "include_comments": true,
  "mimic_defaults": false,
  "translate_erc20": true,
  "smart": true
}
```

### Recommended next steps
1. The initial balance has to be minted to the contract during deployment ([doc](https://docs.alephium.org/dapps/tutorials/first-fungible-token))
2. Verify that the contract code is correct and that all storage variables are being set correctly

### Output code

```rust
// Ralph Translation of ERC20
// ===========================
//
// In Alephium/Ralph, tokens are NATIVE to the blockchain. Unlike Ethereum where
// ERC20 tokens require a contract to manage balances and transfers, Alephium's
// stateful UTXO model handles tokens at the protocol level.
//
// Key differences:
// 1. Token balances are stored in UTXOs, not contract storage
// 2. Transfers are done via native transfer functions, not contract calls
// 3. Approvals are per-transaction using brace syntax {caller -> tokenId: amount}
// 4. No need for allowance mappings - approvals happen at transaction time
//
// This file demonstrates how each ERC20 function maps to Ralph concepts.

// =============================================================================
// ERC20 EVENTS
// =============================================================================

// event Transfer(...)
// event Approval(...)
// 
// ERC20 EVENTS ARE NOT NEEDED IN RALPH:
// In Ralph, token transfers are native blockchain operations and emit native events.

// This is a base contract representing a fungible token in Ralph/Alephium, clients need to implement the concrete type
Abstract Contract FungibleToken (
  mut tokenMetadata: FungibleTokenMetadata
) implements IFungibleToken {

  // =========================================================================
  // SUPPORTED FUNCTIONS (IFungibleToken interface)
  // =========================================================================

  // SUPPORTED - Part of IFungibleToken interface
  // Returns the total supply of tokens.
  pub fn getTotalSupply() -> U256 {
    return tokenMetadata.totalSupply
  }

  @using(assetsInContract = true)
  pub fn getMaxSupply() -> U256 {
    return tokenMetadata.totalSupply + tokenRemaining!(selfAddress!(), selfTokenId!())
  }

  // Additional metadata functions from IFungibleToken:

  pub fn getSymbol() -> ByteVec {
    return tokenMetadata.symbol
  }

  pub fn getName() -> ByteVec {
    return tokenMetadata.name
  }

  pub fn getDecimals() -> U256 {
    return tokenMetadata.decimals
  }

  // @@@ In Ralph all token minting is capped by the initial UTXO issuance.
  @using(assetsInContract = true)
  fn innerMint(to: Address, amount: U256) -> () {
    transferTokenFromSelf!(to, selfTokenId!(), amount)
    tokenMetadata.totalSupply = tokenMetadata.totalSupply + amount
  }

  // @@@ Burn tokens in ERC20 sense - they can be reissued later
  @using(preapprovedAssets = true, assetsInContract = true)
  fn innerBurn(from: Address, amount: U256) -> () {
    transferTokenToSelf!(from, selfTokenId!(), amount)
    tokenMetadata.totalSupply = tokenMetadata.totalSupply - amount
  }

  // =========================================================================
  // NOT SUPPORTED / NOT NEEDED FUNCTIONS
  // =========================================================================

  // @@@ In Ralph, token balances are stored in UTXOs, not in contract storage. Balances are queried via the Alephium REST API or SDK, not contract calls.
  // UNSUPPORTED: function balanceOf(address account) external view returns (uint256)
  //
  // Instead, you can use:
  //   tokenRemaining!(address, tokenId)
  // But this only works for assets that are part of the current transaction.

  // @@@ Native token transfers in Ralph are done using built-in functions. The caller just sends tokens as part of the transaction.
  // UNSUPPORTED: function transfer(address to, uint256 value) external returns (bool)
  // Caveat: account/contract to contract transfers require a contract call to receiving contract. Assets cannot be deposited without consent of the receiving contract.

  // @@@ Ralph does not have persistent allowances. Instead, approvals are per-transaction using the brace syntax: contract.function{owner -> tokenId: amount}(params)
  // UNSUPPORTED: function allowance(address owner, address spender) external view returns (uint256)
  //
  // @@@  Ralph uses per-transaction approvals. When calling a function that needs to spend your tokens, you approve in the same call using brace syntax.
  // UNSUPPORTED: function approve(address spender, uint256 value) external returns (bool)

  // @@@ In Ralph, token transfers are native operations. The "from" address must be part of the transaction (signing or approving assets).
  // UNSUPPORTED: function transferFrom(address from, address to, uint256 value) external returns (bool)
}

// =============================================================================
// SUMMARY: ERC20 vs Ralph Native Tokens
// =============================================================================
//
// | ERC20 Function   | Ralph Equivalent                              | Supported |
// |------------------|-----------------------------------------------|-----------|
// | totalSupply()    | getTotalSupply() via IFungibleToken           | ✅ Yes    |
// | balanceOf()      | REST API / tokenRemaining!() in tx            | ❌ No     |
// | transfer()       | transferToken!() / transferTokenFromSelf!()   | ❇️ Native |
// | allowance()      | N/A - per-transaction approvals               | ❌ No     |
// | approve()        | Brace syntax {addr -> token: amt}             | ❌ No     |
// | transferFrom()   | transferToken!() with preapprovedAssets       | ❇️ Native |
// | Transfer event   | Native blockchain tracking                    | ❌ No     |
// | Approval event   | N/A - no persistent approvals                 | ❌ No     |
//
// Key Takeaways:
// 1. Tokens are first-class citizens in Alephium - transfers are native and UTXO based
// 2. Approvals are atomic and per-transaction - much safer than ERC20 pattern
// 3. Coins are in UTXOs, queried via API, not contract storage
// 4. Transfer events are redundant - blockchain natively tracks all movements and emits native events

// Ralph Translation of IERC20
// ===========================

// Metadata structure for Fungible Token
struct FungibleTokenMetadata {
  mut symbol: ByteVec,
  mut name: ByteVec,
  mut decimals: U256,
  mut totalSupply: U256
}

@std(id = #0001)
@using(methodSelector = false)
Interface IFungibleToken {
  pub fn getSymbol() -> ByteVec

  pub fn getName() -> ByteVec

  pub fn getDecimals() -> U256

  pub fn getTotalSupply() -> U256
}

Contract CPAMM(
    token0: ByteVec,
    token1: ByteVec,
    mut reserve0: U256,
    mut reserve1: U256,
    mut tokenMetadata: FungibleTokenMetadata
) extends FungibleToken(tokenMetadata) {

    enum ErrorCodes {
        InvalidToken = 0
        AmountInIsZero
        InvalidRatio
        SharesAreZero
        AmountOutIsZero
    }

    // Private helper to update reserves
    @using(updateFields = true)
    fn update_(newReserve0: U256, newReserve1: U256) -> () {
        reserve0 = newReserve0
        reserve1 = newReserve1
    }

    // Swaps one token for another
    @using(preapprovedAssets = true, assetsInContract = true, updateFields = true)
    pub fn swap(tokenInId: ByteVec, amountIn: U256) -> U256 {
        assert!(tokenInId == token0 || tokenInId == token1, ErrorCodes.InvalidToken)
        assert!(amountIn > 0, ErrorCodes.AmountInIsZero)

        let caller = callerAddress!()
        let isToken0 = tokenInId == token0
        let (tokenOutId, currentReserveIn, currentReserveOut) = if isToken0 {
            (token1, reserve0, reserve1)
        } else {
            (token0, reserve1, reserve0)
        }

        // Caller approves `amountIn` of `tokenInId` for this contract to use
        transferTokenToSelf!(caller, tokenInId, amountIn)

        // 0.3% fee
        let amountInWithFee = (amountIn * 997) / 1000
        let amountOut = (currentReserveOut * amountInWithFee) / (currentReserveIn + amountInWithFee)

        // Transfer `amountOut` of `tokenOutId` from this contract to the caller
        transferTokenFromSelf!(caller, tokenOutId, amountOut)

        // Update reserves
        if (isToken0) {
            update_(reserve0 + amountIn, reserve1 - amountOut)
        } else {
            update_(reserve0 - amountOut, reserve1 + amountIn)
        }
        // @@@ Solidity's `_update` reads balances directly, which is not possible in Ralph. Reserves are updated arithmetically.

        return amountOut
    }

    // Adds liquidity to the pool
    @using(preapprovedAssets = true, assetsInContract = true, updateFields = true)
    pub fn addLiquidity(amount0: U256, amount1: U256) -> U256 {
        let caller = callerAddress!()
        // Caller approves `amount0` of `token0` and `amount1` of `token1`
        transferTokenToSelf!(caller, token0, amount0)
        transferTokenToSelf!(caller, token1, amount1)

        if (reserve0 > 0 || reserve1 > 0) {
            // require(reserve0 * _amount1 == reserve1 * _amount0, "x / y != dx / dy");
            assert!(reserve0 * amount1 == reserve1 * amount0, ErrorCodes.InvalidRatio)
        }

        let mut shares = 0
        if (tokenMetadata.totalSupply == 0) {
            // First liquidity provider
            shares = sqrt_(amount0 * amount1)
        } else {
            shares = min_(
                (amount0 * tokenMetadata.totalSupply) / reserve0,
                (amount1 * tokenMetadata.totalSupply) / reserve1
            )
        }
        assert!(shares > 0, ErrorCodes.SharesAreZero)

        // Mint LP shares to the provider
        innerMint(caller, shares)
        // @@@ In Solidity, _mint updates a mapping. In Ralph, innerMint transfers native LP tokens to the caller.

        // Update reserves
        update_(reserve0 + amount0, reserve1 + amount1)
        // @@@ Solidity's `_update` reads balances directly. In Ralph, reserves are updated arithmetically.

        return shares
    }

    // Removes liquidity from the pool
    @using(preapprovedAssets = true, assetsInContract = true, updateFields = true)
    pub fn removeLiquidity(shares: U256) -> (U256, U256) {
        let caller = callerAddress!()

        // @@@ Solidity reads live balances; Ralph must use its tracked state variables `reserve0` and `reserve1`.
        let amount0 = (shares * reserve0) / tokenMetadata.totalSupply
        let amount1 = (shares * reserve1) / tokenMetadata.totalSupply
        assert!(amount0 > 0 && amount1 > 0, ErrorCodes.AmountOutIsZero)

        // Burn LP shares from the provider
        innerBurn{caller -> selfTokenId!(): shares}(caller, shares)
        // @@@ In Solidity, _burn updates a mapping. In Ralph, innerBurn transfers native LP tokens from the caller back to the contract.

        // Update reserves
        update_(reserve0 - amount0, reserve1 - amount1)
        // @@@ Solidity's `_update` reads balances directly. In Ralph, reserves are updated arithmetically.

        // Transfer underlying tokens back to the provider
        transferTokenFromSelf!(caller, token0, amount0)
        transferTokenFromSelf!(caller, token1, amount1)

        return amount0, amount1
    }

    // Getter for reserve0
    pub fn getReserve0() -> U256 {
        return reserve0
    }

    // Getter for reserve1
    pub fn getReserve1() -> U256 {
        return reserve1
    }

    // Getter for token0 ID
    pub fn getToken0() -> ByteVec {
        return token0
    }

    // Getter for token1 ID
    pub fn getToken1() -> ByteVec {
        return token1
    }

    // Calculates the integer square root of a number
    fn sqrt_(y: U256) -> U256 {
        let mut z = 0
        if (y > 3) {
            z = y
            let mut x = y / 2 + 1
            while (x < z) {
                z = x
                x = (y / x + x) / 2
            }
        } else if (y != 0) {
            z = 1
        } else {
            z = 0
        }
        return z
    }

    // Returns the minimum of two numbers
    fn min_(x: U256, y: U256) -> U256 {
        return if x <= y { x } else { y }
    }
}
```