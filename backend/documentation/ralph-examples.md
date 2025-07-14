# Ralph Examples

## Ralph NFT
```ralph
import "std/nft_interface"

Contract NFT(
  tokenUri: ByteVec,
  collectionId: ByteVec,
  nftIndex: U256
) implements INFT {
  pub fn getTokenUri() -> ByteVec {
    return tokenUri
  }

  pub fn getNFTIndex() -> U256 {
    return nftIndex
  }

  pub fn getCollectionIndex() -> (ByteVec, U256) {
    return collectionId, nftIndex
  }
}
```

## Ralph NFT Collection
```ralph
import "std/nft_collection_interface"

Abstract Contract NFTCollectionBase(
    collectionUri: ByteVec,
    collectionOwner: Address,
    mut totalSupply: U256
) implements INFTCollection {
    enum ErrorCodes {
        NFTNotFound = 0
        CollectionOwnerAllowedOnly = 1
        NFTNotPartOfCollection = 2
    }

    pub fn getCollectionUri() -> ByteVec {
        return collectionUri
    }

    pub fn totalSupply() -> U256 {
        return totalSupply
    }

    @using(checkExternalCaller = false)
    pub fn nftByIndex(index: U256) -> INFT {
        let nftTokenId = subContractId!(toByteVec!(index))
        assert!(contractExists!(nftTokenId), ErrorCodes.NFTNotFound)

        return INFT(nftTokenId)
    }

    @using(assetsInContract = true)
    pub fn withdraw(to: Address, amount: U256) -> () {
        checkCaller!(callerAddress!() == collectionOwner, ErrorCodes.CollectionOwnerAllowedOnly)
        transferTokenFromSelf!(to, ALPH, amount)
    }

    @using(checkExternalCaller = false)
    pub fn validateNFT(nftId: ByteVec, nftIndex: U256) -> () {
      let expectedTokenContract = nftByIndex(nftIndex)
      assert!(nftId == contractId!(expectedTokenContract), ErrorCodes.NFTNotPartOfCollection)
    }
}
```


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
Abstract Contract ParentContract(
  field1: U256,
  field2: ByteVec
) {
  pub fn getField1() -> U256 {
    return field1
  }

  pub fn getField2() -> ByteVec {
    return field2
  }
}

Abstract Contract ParentContract2(
  field3: Address
) {
  pub fn getField3() -> Address {
    return field3
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
  field1: U256,
  field2: ByteVec,
  field3: Address
) extends ParentContract(field1, field2), ParentContract2(field3), Math() {
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
