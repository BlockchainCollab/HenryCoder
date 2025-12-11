# Ralph Examples

## Oracle
Alephium supports 2 native oracles:
- `IDIAOracle` (price oracle)
- `IDIARandomOracle` (randomness oracle)

### Price fetcher example:
```ralph
struct DIAOracleValue {
  mut value: U256,
  mut timestamp: U256
}

Interface IDIAOracle {
  pub fn getValue(key: ByteVec) -> DIAOracleValue
}

Contract PriceFetcher(
  oracle: IDIAOracle,
  mut btcPrice: U256,
  mut ethPrice: U256,
  mut usdcPrice: U256,
  mut alphPrice: U256,
  mut ayinPrice: U256
) {
  @using(updateFields = true, checkExternalCaller = false)
  pub fn update() -> () {
    btcPrice = oracle.getValue(b`BTC/USD`).value
    ethPrice = oracle.getValue(b`ETH/USD`).value
    usdcPrice = oracle.getValue(b`USDC/USD`).value
    alphPrice = oracle.getValue(b`ALPH/USD`).value
    ayinPrice = oracle.getValue(b`AYIN/USD`).value
  }
}
```

### Randomness fetcher example:
```ralph
struct DIARandomValue {
    mut randomness: ByteVec,
    mut signature: ByteVec,
    mut round: U256
}

Interface IDIARandomOracle {
    pub fn getLastRound() -> U256
    pub fn getRandomValue(round: U256) -> DIARandomValue
}

Contract RandomnessFetcher(
  oracle: IDIARandomOracle,
  mut randomValue: DIARandomValue
) {
  @using(updateFields = true, checkExternalCaller = false)
  pub fn update() -> () {
    let lastRound = oracle.getLastRound()
    let value = oracle.getRandomValue(lastRound)
    randomValue = value
  }
}
```

## Inheritance
In Ralph a contract can only extend an `Abstract Contract`. The fields in the parent contract must match exactly the fields in the child contract. The child contract can add additional fields, but cannot remove or change the existing ones. Multiple inheritance is supported as well but methods cannot overlap and child cannot override parent methods.

```ralph
struct ParentMetadata {
  field1: U256,
  field2: ByteVec
}

Abstract Contract ParentContract(
  mut parentMetadata: ParentMetadata
) {
  pub fn getField1() -> U256 {
    return parentMetadata.field1
  }

  pub fn getField2() -> ByteVec {
    return parentMetadata.field2
  }
}

Abstract Contract Baz(
  fieldOmega: Address
) {
  pub fn getFieldOmega() -> Address {
    return fieldOmega
  }
}

Abstract Contract Math() {
  pub fn add(a: U256, b: U256) -> U256 {
    return a + b
  }

  pub fn sub(a: U256, b: U256) -> U256 {
    return a - b
  }
}

Contract ChildContract(
  field3: Address
  mut parentMetadata: ParentMetadata,
) extends ParentContract(parentMetadata), Baz(field3), Math() {
  pub fn sumAndDiff(a: U256, b: U256) -> (U256, U256) {
    let sum = add(a, b)
    let diff = sub(a, b)
    return sum, diff
  }
}
```

## Receive and send tokens
In Ralph, contract CANNOT receive tokens from other contracts or users. Instead they have to make a transfer to themselves and the receiving function has to be explicitly prepared for that with `@using(preapprovedAssets = true, payToContractOnly = true)` annotation, which allows the contract to get tokens from approved assets and store them on its own account.

```ralph
Contract Receiver() {
  // Function to receive any token (including ALPH)
  @using(preapprovedAssets = true, checkExternalCaller = false, payToContractOnly = true)
  pub fn receive(tokenId: ByteVec, amount: U256) -> () {
    transferTokenToSelf!(callerAddress!(), tokenId, amount)
  }

  // assetsInContract allows the method to use contract's own tokens.
  @using(assetsInContract = true, checkExternalCaller = false)
  pub fn getBalance(tokenId: ByteVec) -> U256 {
    return tokenRemaining!(selfAddress!(), tokenId)
  }
}

Contract Sender(
  receiver: Receiver,
  receiverAccount: Address
) {
  // Amount of tokens to send
  const AMOUNT = 2000

  // When sending tokens to contract, a specialized method has to be designated to receive tokens, we cannot do a direct transfer
  @using(assetsInContract = true, checkExternalCaller = false)
  pub fn airdropTokensToContract() -> () {
    // Use curly braces syntax to authorize own assets
    receiver.receive{selfAddress!() -> selfTokenId!(): AMOUNT}(selfTokenId!(), AMOUNT)
  }

  // When sending tokens to a regular account we can safely transferFrom the contract
  pub fn airdropToRegularAccount() -> () {
    transferTokenFromSelf!(receiverAccount, selfTokenId!(), AMOUNT)
  }

  @using(preapprovedAssets = true, checkExternalCaller = false)
  pub fn forwardCallerTokens(tokenId: ByteVec, amount: U256) -> () {
    // Use curly braces syntax to forward approval
    receiver.receive{callerAddress!() -> tokenId: amount}(tokenId, amount)
  }
}
```

## Unary bit complement
Ralph does not have a native unary bit complement operator `~`, but it can be easily implemented:

```ralph
Contract Foo() {
  // Use unaryBitComplemenmt to implement unary bit complement for U256 type
  fn unaryBitComplemenmt(value: U256) -> U256 {
    return u256Max!() ^ value
  }
}
```
