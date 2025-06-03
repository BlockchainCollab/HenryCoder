Alephium's unique stateful UTXO model completely reworks the way transfers and tokens work on-chain. On Alephium, tokens are a native concept so there is no need to use a contract to transact.

## Transfers
Transfers in Alephium are done by using any of the transfer functions. Note that ALPH is also a native token, and can be transacted in exactly the same manner.

```ralph
Contract EscrowExample(
  tokenId: ByteVec,
  recipient: Address
) {
  // Pay to contract only allows the contract to receive tokens, but not send them
  // Preapproved assets allows anyone to make the deposit
  // Check external caller = false allows anyone to call the deposit function
  @using(checkExternalCaller = false, preapprovedAssets = true, payToContractOnly = true)
  pub fn deposit(amount: U256) -> () {
    transferTokenToSelf!(callerAddress!(), tokenId, amount)
  }

  // Assets in contract allows the contract to send its own tokens to another address
  @using(assetsInContract = true)
  pub fn withdraw() -> () {
    checkCaller!(callerAddress!() == recipient, 1001)
    transferTokenFromSelf!(recipient, tokenId, tokenRemaining!(selfAddress!(), tokenId))
  }
}
```

## Approvals
Approvals in Alephium are managed on a per-transaction basis. So if you want to pass approved assets to another contract you have to use the curly braces syntax.

```ralph
Interface DexExample {
  @using(preapprovedAssets = true, assetsInContract = true)
  pub fn swap(
    tokenIn: ByteVec,
    amountIn: U256,
    tokenOut: ByteVec,
    recipient: Address
  ) -> ()

  pub fn tokens() -> (ByteVec, ByteVec)
}

Contract SwapManager(
  dex: DexExample
) {
  // Make the swap using user's assets
  @using(checkExternalCaller = false, preapprovedAssets = true)
  pub fn swap(caller: Address, amountIn: U256) -> () {
    let (tokenIn, tokenOut) = dex.tokens()

    // Use the curly braces syntax to pass the approved assets
    dex.swap{caller -> tokenIn: amountIn}(tokenIn, amountIn, tokenOut, caller)
  }
}
```
