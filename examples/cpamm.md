# Constant Product Automated Market Maker (CPAMM) translation

## Solidity source
The solidity code is available online at: https://solidity-by-example.org/defi/constant-product-amm/
This is a simpler version of the UniswapV2 contract.

## ralph translation

### Settings
```json
{
  "optimize": false,
  "include_comments": true,
  "mimic_defaults": false,
  "translate_erc20": true,
  "smart": false
}
```

### Recommended next steps
1. Implement [IFungibleToken](https://docs.alephium.org/dapps/standards/fungible-tokens/)
2. Remove balanceOf mapping - Alephium has native support for contract tokens
3. The initial balance has to be minted to the contract during deployment ([doc](https://docs.alephium.org/dapps/tutorials/first-fungible-token))
4. Verify that the contract code is correct and that all storage variables are being set correctly

### Output code

```rust
// Constant Product Automated Market Maker (CPAMM) implementation in Ralph
// Note: In Alephium, tokens are native and don't require ERC20 interfaces

Contract CPAMM(
  token0: ByteVec,  // Token ID of token0
  token1: ByteVec,  // Token ID of token1
  mut reserve0: U256,
  mut reserve1: U256,
  mut totalSupply: U256
) {
  // Mapping to track LP token balances
  mapping[Address, U256] balanceOf

  // Error codes
  enum ErrorCodes {
    InvalidToken = 1001
    ZeroAmount = 1002
    InvalidRatio = 1003
    ZeroShares = 1004
    ZeroOutput = 1005
  }

  // Internal function to mint LP tokens
  fn mint(to: Address, amount: U256) -> () {
    if (balanceOf.contains!(to)) {
      balanceOf[to] = balanceOf[to] + amount
    } else {
      balanceOf.insert!(to, amount)
    }
    totalSupply = totalSupply + amount
  }

  // Internal function to burn LP tokens
  fn burn(from: Address, amount: U256) -> () {
    balanceOf[from] = balanceOf[from] - amount
    totalSupply = totalSupply - amount
  }

  // Internal function to update reserves
  fn update(newReserve0: U256, newReserve1: U256) -> () {
    reserve0 = newReserve0
    reserve1 = newReserve1
  }

  // Swap tokens
  @using(preapprovedAssets = true, checkExternalCaller = false)
  pub fn swap(tokenIn: ByteVec, amountIn: U256) -> U256 {
    // Validate inputs
    assert!(tokenIn == token0 || tokenIn == token1, ErrorCodes.InvalidToken)
    assert!(amountIn > 0, ErrorCodes.ZeroAmount)

    // Determine swap direction
    let isToken0 = tokenIn == token0
    let (reserveIn, reserveOut) = if (isToken0) {
      (reserve0, reserve1)
    } else {
      (reserve1, reserve0)
    }

    // Calculate output amount with 0.3% fee
    let amountInWithFee = (amountIn * 997) / 1000
    let amountOut = (reserveOut * amountInWithFee) / (reserveIn + amountInWithFee)
    assert!(amountOut > 0, ErrorCodes.ZeroOutput)

    // Transfer tokens
    if (isToken0) {
      // Transfer token0 from caller to contract
      transferTokenToSelf!(callerAddress!(), token0, amountIn)
      // Transfer token1 to caller
      transferTokenFromSelf!(callerAddress!(), token1, amountOut)
    } else {
      // Transfer token1 from caller to contract
      transferTokenToSelf!(callerAddress!(), token1, amountIn)
      // Transfer token0 to caller
      transferTokenFromSelf!(callerAddress!(), token0, amountOut)
    }

    // Update reserves
    let newReserve0 = tokenRemaining!(selfAddress!(), token0)
    let newReserve1 = tokenRemaining!(selfAddress!(), token1)
    update(newReserve0, newReserve1)

    return amountOut
  }

  // Add liquidity to the pool
  @using(preapprovedAssets = true, checkExternalCaller = false)
  pub fn addLiquidity(amount0: U256, amount1: U256) -> U256 {
    // Transfer tokens from caller to contract
    transferTokenToSelf!(callerAddress!(), token0, amount0)
    transferTokenToSelf!(callerAddress!(), token1, amount1)

    // Validate ratio if pool already has liquidity
    if (reserve0 > 0 || reserve1 > 0) {
      assert!(
        reserve0 * amount1 == reserve1 * amount0,
        ErrorCodes.InvalidRatio
      )
    }

    // Calculate shares to mint
    let shares = if (totalSupply == 0) {
      sqrt(amount0 * amount1)
    } else {
      min(
        (amount0 * totalSupply) / reserve0,
        (amount1 * totalSupply) / reserve1
      )
    }
    assert!(shares > 0, ErrorCodes.ZeroShares)

    // Mint LP tokens
    mint(callerAddress!(), shares)

    // Update reserves
    let newReserve0 = tokenRemaining!(selfAddress!(), token0)
    let newReserve1 = tokenRemaining!(selfAddress!(), token1)
    update(newReserve0, newReserve1)

    return shares
  }

  // Remove liquidity from the pool
  @using(assetsInContract = true, checkExternalCaller = false)
  pub fn removeLiquidity(shares: U256) -> (U256, U256) {
    // Calculate amounts to withdraw
    let bal0 = tokenRemaining!(selfAddress!(), token0)
    let bal1 = tokenRemaining!(selfAddress!(), token1)
    let amount0 = (shares * bal0) / totalSupply
    let amount1 = (shares * bal1) / totalSupply
    assert!(amount0 > 0 && amount1 > 0, ErrorCodes.ZeroOutput)

    // Burn LP tokens
    burn(callerAddress!(), shares)

    // Update reserves
    update(bal0 - amount0, bal1 - amount1)

    // Transfer tokens to caller
    transferTokenFromSelf!(callerAddress!(), token0, amount0)
    transferTokenFromSelf!(callerAddress!(), token1, amount1)

    return amount0, amount1
  }

  // Internal function to calculate square root (Babylonian method)
  fn sqrt(y: U256) -> U256 {
    if (y > 3) {
      let mut z = y
      let mut x = y / 2 + 1
      while (x < z) {
        z = x
        x = (y / x + x) / 2
      }
      return z
    } else if (y != 0) {
      return 1
    } else {
      return 0
    }
  }

  // Internal function to find minimum of two values
  fn min(x: U256, y: U256) -> U256 {
    return if (x <= y) x else y
  }
}
```