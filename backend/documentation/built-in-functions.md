The built-in functions are divided into several categories: 
[Contract](#contract-functions),
[SubContract](#subcontract-functions),
[Map](#map-functions),
[Asset](#asset-functions),
[Utils](#utils-functions),
[Chain](#chain-functions),
[Conversion](#conversion-functions),
[ByteVec](#bytevec-functions),
[Cryptography](#cryptography-functions).
All built-in functions are suffixed with `!`.
All of the byte encoding use Big Endian byte order.

## Contract Functions
---
### externalCallerAddress
```ralph
fn externalCallerAddress!() -> (Address)
```

Returns the address which called the smart contract

> @returns *the address of the external caller*

---

## Map Functions
---
### map.insert

```ralph
fn <map>.insert!(value: Any) -> ()
```

Insert a key/value pair into the map. No brace syntax is required, as the minimal storage deposit will be deducted from the approved assets by the VM

> @param **depositorAddress** *the address to pay the minimal storage deposit (0.1 ALPH) for the new map entry. If not provided, minimal storage deposit will be paid by the transaction caller*
>
> @param **key** *the key to insert*
>
> @param **value** *the value to insert*
>
> @returns

---

### map.remove

```ralph
fn <map>.remove!(key: <Bool | U256 | I256 | Address | ByteVec>) -> ()
```

Remove a key from the map

> @param **key** *the key to remove*
>
> @returns

---

### map.contains

```ralph
fn <map>.contains!(key: <Bool | U256 | I256 | Address | ByteVec>) -> Bool
```

Check whether the map contains a bindiing for the key

> @param **key** *the key to check*
>
> @returns *true if there is a binding for key in this map, false otherwise*

---

## Asset Functions
---
### approveToken

```ralph
fn approveToken!(fromAddress: Address, tokenId: ByteVec, amount: U256) -> ()
```

Approves the usage of certain amount of token from the given address

> @param **fromAddress** *the address to approve token from*
>
> @param **tokenId** *the token to be approved*
>
> @param **amount** *the amount of the token to be approved*
>
> @returns

---

### tokenRemaining

```ralph
fn tokenRemaining!(address: Address, tokenId: ByteVec) -> (U256)
```

Returns the amount of the remaining token amount in the input assets of the function. The calling function must have @using(assetsInContract=true) or @using(preapprovedAssets=true) or both specified

> @param **address** *the input address*
>
> @param **tokenId** *the token id*
>
> @returns *the amount of the remaining token amount in the input assets of the function*

---

### transferToken

```ralph
fn transferToken!(fromAddress: Address, toAddress: Address, tokenId: ByteVec, amount: U256) -> ()
```

Transfers token from the input assets of the function.

> @param **fromAddress** *the address to transfer token from*
>
> @param **toAddress** *the address to transfer token to*
>
> @param **tokenId** *the token to be transferred*
>
> @param **amount** *the amount of token to be transferred*
>
> @returns

---

### transferTokenFromSelf

```ralph
fn transferTokenFromSelf!(toAddress: Address, tokenId: ByteVec, amount: U256) -> ()
```

Transfers the contract's token from the input assets of the function. The toAddress must not be the same as the contract address. The calling function must specify @using(assetsInContract = true) for this to work

> @param **toAddress** *the address to transfer token to*
>
> @param **tokenId** *the token to be transferred*
>
> @param **amount** *the amount of token to be transferred*
>
> @returns

---

### transferTokenToSelf

```ralph
fn transferTokenToSelf!(fromAddress: Address, tokenId: ByteVec, amount: U256) -> ()
```

Transfers token to the contract from the input assets of the function. The fromAddress must not be the same as the contract address.

> @param **fromAddress** *the address to transfer token from*
>
> @param **tokenId** *the token to be transferred*
>
> @param **amount** *the amount of token to be transferred*
>
> @returns

---

### burnToken

```ralph
fn burnToken!(address: Address, tokenId: ByteVec, amount: U256) -> ()
```

Burns token from the input assets of the function.

> @param **address** *the address to burn token from*
>
> @param **tokenId** *the token to be burnt*
>
> @param **amount** *the amount of token to be burnt*
>
> @returns

---

### lockApprovedAssets

```ralph
fn lockApprovedAssets!(address: Address, timestamp: U256) -> ()
```

Locks the current approved assets.

> @param **address** *the address to lock assets to*
>
> @param **timestamp** *the timestamp that the assets will be locked until*
>
> @returns

---

### payGasFee

```ralph
fn payGasFee!(payer: Address, amount: U256) -> ()
```

Pay gas fee.

> @param **payer** *payer of the gas*
>
> @param **amount** *the amount of gas to be paid in ALPH*
>
> @returns

---

## Utils Functions
---
### assert

```ralph
fn assert!(condition: Bool, errorCode: U256) -> ()
```

Tests the condition or checks invariants.

> @param **condition** *the condition to be checked*
>
> @param **errorCode** *the error code to throw if the check fails*
>
> @returns

---

### checkCaller

```ralph
fn checkCaller!(condition: Bool, errorCode: U256) -> ()
```

Checks conditions of the external caller of the function.

> @param **condition** *the condition to be checked*
>
> @param **errorCode** *the error code to throw if the check fails*
>
> @returns

---

### isContractAddress

```ralph
fn isContractAddress!(address: Address) -> (Bool)
```

Returns whether an address is a contract address.

> @param **address** *the input address to be tested*
>
> @returns *true if the address is a contract address, false otherwise*

---

### zeros

```ralph
fn zeros!(n: U256) -> (ByteVec)
```

Returns a ByteVec of zeros.

> @param **n** *the number of zeros*
>
> @returns *a ByteVec of zeros*

---

### panic

```ralph
fn panic!(errorCode?: U256) -> (Never)
```

Terminates the application immediately.

> @param **errorCode** *(optional) the error code to be thrown when the panic!(...) is called*
>
> @returns

---

### mulModN

```ralph
fn mulModN!(x: U256, y: U256, n: U256) -> (U256)
```

Returns compute the x * y % n.

> @param **x** *x*
>
> @param **y** *y*
>
> @param **n** *n*
>
> @returns *compute the x * y % n*

---

### addModN

```ralph
fn addModN!(x: U256, y: U256, n: U256) -> (U256)
```

Returns compute the (x + y) % n.

> @param **x** *x*
>
> @param **y** *y*
>
> @param **n** *n*
>
> @returns *compute the (x + y) % n*

---

### u256Max

```ralph
fn u256Max!() -> (U256)
```

Returns the max value of U256.

> @returns *the max value of U256*

---

### i256Max

```ralph
fn i256Max!() -> (I256)
```

Returns the max value of I256.

> @returns *the max value of I256*

---

### i256Min

```ralph
fn i256Min!() -> (I256)
```

Returns the min value of I256.

> @returns *the min value of I256*

---

### groupOfAddress

```ralph
fn groupOfAddress!(address: Address) -> (U256)
```

Returns the group of the input address.

> @param **address** *the input address*
>
> @returns *the group of the input address*

---

### len

```ralph
fn len!(array) -> (U256)
```

Get the length of an array

> @param **an** *array*
>
> @returns *the length of an array*

---

### nullContractAddress

```ralph
fn nullContractAddress!() -> (Address)
```

Returns the null contract address with contract id being zeros.

> @returns *the null contract address with contract id being zeros*

---

### minimalContractDeposit

```ralph
fn minimalContractDeposit!() -> (U256)
```

The minimal contract deposit

> @returns *the minimal ALPH amount for contract deposit*

---

### mapEntryDeposit

```ralph
fn mapEntryDeposit!() -> (U256)
```

The amount of ALPH required to create a map entry, which is '0.1 ALPH' since Rhone upgrade

> @returns *the amount of ALPH required to create a map entry*

---


## Conversion Functions
---
### toI256

```ralph
fn toI256!(from: U256) -> (I256)
```

Converts U256 to I256.

> @param **from** *a U256 to be converted*
>
> @returns *a I256*

---

### toU256

```ralph
fn toU256!(from: I256) -> (U256)
```

Converts I256 to U256.

> @param **from** *a I256 to be converted*
>
> @returns *a U256*

---

### toByteVec

```ralph
fn toByteVec!(from: Bool|I256|U256|Address) -> (ByteVec)
```

Converts Bool/I256/U256/Address to ByteVec

> @param **from** *a Bool|I256|U256|Address to be converted*
>
> @returns *a ByteVec*

---

### contractIdToAddress

```ralph
fn contractIdToAddress!(contractId: ByteVec) -> (Address)
```

Converts contract id (ByteVec) to contract address (Address).

> @param **contractId** *the input contract id*
>
> @returns *a contract Address*

---

### addressToContractId

```ralph
fn addressToContractId!(contractAddress: Address) -> (ByteVec)
```

Converts contract address (Address) to contract id (ByteVec)

> @param **contractAddress** *the input contract address*
>
> @returns *a contract id*

---

## Cryptography Functions
---
### blake2b

```ralph
fn blake2b!(data: ByteVec) -> (ByteVec)
```

---

### keccak256

```ralph
fn keccak256!(data: ByteVec) -> (ByteVec)
```

---

### sha256

```ralph
fn sha256!(data: ByteVec) -> (ByteVec)
```

---

### sha3

```ralph
fn sha3!(data: ByteVec) -> (ByteVec)
```

---

### verifyTxSignature

```ralph
fn verifyTxSignature!(publicKey: ByteVec) -> ()
```

---

### getSegregatedSignature

```ralph
fn getSegregatedSignature!() -> (ByteVec)
```

---

### verifySecP256K1

```ralph
fn verifySecP256K1!(data: ByteVec, publicKey: ByteVec, signature: ByteVec) -> ()
```

---

### verifyED25519

```ralph
fn verifyED25519!(data: ByteVec, publicKey: ByteVec, signature: ByteVec) -> ()
```

---

### verifyBIP340Schnorr

```ralph
fn verifyBIP340Schnorr!(data: ByteVec, publicKey: ByteVec, signature: ByteVec) -> ()
```
---

### ethEcRecover

```ralph
fn ethEcRecover!(data: ByteVec, signature: ByteVec) -> (ByteVec)
```

---

### verifySignature

```ralph
fn verifySignature!(data: ByteVec, publicKey: ByteVec, signature: ByteVec, publicKeyType: ByteVec) -> ()
```

---

### verifySecP256R1

```ralph
fn verifySecP256R1!(data: ByteVec, publicKey: ByteVec, signature: ByteVec) -> ()
```

---

### verifyWebAuthn

```ralph
fn verifyWebAuthn!(challenge: ByteVec, publicKey: ByteVec, payload: ByteVec) -> ()
```

---

### getSegregatedWebAuthnSignature

```ralph
fn getSegregatedWebAuthnSignature!() -> (ByteVec)
```

---
