## Contracts

:::tip note
Each Alephium's contract has 3 forms of unique identification:

1. **Address**: each contract has a unique address
2. **Contract ID**: each contract has a unique contract ID
3. **Token ID**: each contract can issue a token with the same ID as its own contract ID

In Ralph, the contract ID is used more frequently. Contract ids can be converted from/to other forms with Ralph's built-in functions or web3 SDK.
:::

Contracts in Ralph are similar to classes in object-oriented languages. 
Each contract can contain declarations of:
0. contract fields
1. maps (must be inside contract scope)
2. events (must be inside contract or interface scope)
3. consts
4. enums
5. methods (must be inside contract or interface scope)
Furthermore, contracts can inherit from other contracts.

```ralph
// This is a comment, and currently Ralph only supports line comments.
// Contract should be named in UpperCamelCase.
// Contract fields are permanently stored in the contract storage.
// Contract fields must be named in camelCase.
Contract MyToken(supply: U256, name: ByteVec, mut owner: Address) {

  // Events should be named in UpperCamelCase.
  // Events allow for logging of activities on the blockchain.
  // Applications can listen to these events through the REST API of an Alephium client.
  event Transfer(to: Address, amount: U256)

  // Constant variables must be named in UpperCamelCase or SCREAMING_SNAKE_CASE.
  const PROGRAM_VERSION = 0

  // Enums can be used to create a finite set of constant values.
  enum ErrorCodes {
    // Enum constants must be named in UpperCamelCase or SCREAMING_SNAKE_CASE.
    InvalidCaller = 0,
    OwnerMustChange
  }

  // Functions, parameters, and local variables must be named in camelCase and must start with [a-z] (lowercase). They can end in `_` (underscore).
  @using(updateFields = true)
  pub fn changeOwner(owner_: Address) -> () {
    let callerAddr = externalCallerAddress!()
    checkCaller!(callerAddr == owner, ErrorCodes.InvalidCaller)
    assert!(owner_ != owner, ErrorCodes.OwnerMustChange)
    // ...
  }
}
```

### Fields

Contract fields are permanently stored in the contract storage, and the fields can be changed by the contract code. Applications can get the contract fields through the REST API of an Alephium client.

```ralph
// Contract `Foo` has two fields:
// `a`: immutable, it can not be changed by the contract code
// `b`: mutable, it can be changed by the contract code
Contract Foo(a: U256, mut b: Boolean) {
  // ...
}

// Contract fields can also be other contract.
// It will store the contract id of `Bar` in the contract storage of `Foo`.
Contract Foo(bar: Bar) {
  // ...
}

Contract Bar() {
  // ...
}
```

### Contract Built-In Functions

Sometimes we need to create a contract within a contract, and in such cases, we need to encode the contract fields into `ByteVec`. Ralph provides a built-in function called `encodeFields` that can be used to encode the contract fields into `ByteVec`.

The parameter type of the `encodeFields` function is a list of the types of the contract fields, arranged in the order of their definitions. And the function returns two `ByteVec` values, where the first one is the encoded immutable fields, and the second one is the encoded mutable fields.

There is an example:

```ralph
// In real-life scenario this contract will fail to compile due to some fields not being used
Contract Foo(a: U256, mut b: I256, c: ByteVec, mut d: Bool) {
  pub fn update(value: I256) -> () {
    b = value
  }
}

Contract Bar() {
  @using(preapprovedAssets = true)
  fn createFoo(caller: Address, fooBytecode: ByteVec, a: U256, b: I256, c: ByteVec, d: Bool) -> (ByteVec) {
    let (encodedImmFields, encodedMutFields) = Foo.encodeFields!(a, b, c, d)
    // This will create a contract `Foo` with initial asset `1 alph`. 
    // The minimum is `minimalContractDeposit!()`, which is 0.1 alph.
    // Multiple assets can be sent to the contract during creation ass well
    return createContract!{caller -> 1 alph}(fooBytecode, encodedImmFields, encodedMutFields)
  }
}
```

In Ralph, you can read or write contract fields within the same transaction after deploying the contract. With the above example, you can call the `foo.update` after deploying the contract `Foo`:

```ralph
@using(preapprovedAssets = true)
fn createFoo(caller: Address, fooBytecode: ByteVec, a: U256, b: I256, c: ByteVec, d: Bool) -> (ByteVec) {
  let (encodedImmFields, encodedMutFields) = Foo.encodeFields!(a, b, c, d)
  let fooId = createContract!{caller -> 1 alph}(fooBytecode, encodedImmFields, encodedMutFields)
  Foo(fooId).update(-1)
}
```

Note that after deploying the contract, you cannot utilize contract assets in the same transaction.

### Events

Events are dispatched signals that contracts can fire. Applications can listen to these events through the REST API of an Alephium client.

```ralph
Contract Token() {
  // The number of event fields cannot be greater than 8
  event Transfer(to: Address, amount: U256)

  @using(assetsInContract = true)
  pub fn transfer(to: Address) -> () {
    transferTokenFromSelf!(selfTokenId!(), to, 1)
    // Emit the event
    emit Transfer(to, 1)
  }
}
```

### SubContract

Alephium's virtual machine supports subcontract. Subcontracts can be used as map-like data structure but they are less prone to the state bloat issue. A subcontract can be created by a parent contract with a unique subcontract path.

```ralph
Contract Bar(value: U256) {
  pub fn getValue() -> U256 {
    return value
  }
}

Contract Foo(barTemplateId: ByteVec) {
  event SubContractCreated(key: U256, contractId: ByteVec)

  @using(preapprovedAssets = true, checkExternalCaller = false)
  pub fn set(caller: Address, key: U256, value: U256) -> () {
    let path = toByteVec!(key)
    let (encodedImmFields, encodedMutFields) = Bar.encodeFields!(value) // Contract `Bar` has only one field
    // Create a sub contract from the given key and value.
    // The sub contract id is `blake2b(blake2b(selfContractId!() ++ path))`.
    // It will fail if the sub contract already exists.
    let contractId = copyCreateSubContract!{caller -> ALPH: minimalContractDeposit!()}(
      path,
      barTemplateId,
      encodedImmFields,
      encodedMutFields
    )
    emit SubContractCreated(key, contractId)
  }

  pub fn get(key: U256) -> U256 {
    let path = toByteVec!(key)
    // Get the sub contract id by the `subContractId!` built-in function
    let contractId =  subContractId!(path)
    return Bar(contractId).getValue()
  }
}
```

:::tip note
Deploying a contract requires depositing a certain amount of ALPH in the contract(currently 0.1 alph), so creating a large number of sub-contracts is not practical.
:::

### Contract Creation inside a Contract

Ralph supports creating contracts programmatically within contracts, Ralph provides some builtin functions to create contracts, you can find more information at [here](/ralph/built-in-functions#contract-functions).

If you want to create multiple instances of a contract, then you should use the `copyCreateContract!` builtin functions, which will reduce a lot of on-chain storage and transaction gas fee.

```ralph
Contract Foo(a: ByteVec, b: Address, mut c: U256) {
  // ...
}

// We want to create multiple instances of contract `Foo`.
// First we need to deploy a template contract of `Foo`, which contract id is `fooTemplateId`.
// Then we can use `copyCreateContract!` to create multiple instances.
TxScript CreateFoo(fooTemplateId: ByteVec, a: ByteVec, b: Address, c: U256) {
  let (encodedImmFields, encodedMutFields) = Foo.encodeFields!(a, b, c)
  copyCreateContract!(fooTemplateId, encodedImmFields, encodedMutFields)
}
```

### Migration

Alephium's contracts can be upgraded with two migration functions: [migrate!](/ralph/built-in-functions#migrate) and [migrateWithFields!](/ralph/built-in-functions#migratewithfields). Here are the three typical ways to use them:

```ralph
fn upgrade(newCode: ByteVec) -> () {
  checkOwner(...)
  migrate!(newCode)
}

fn upgrade(newCode: ByteVec, newImmFieldsEncoded: ByteVec, newMutFieldsEncoded: ByteVec) -> () {
  checkOwner(...)
  migrateWithFields!(newCode, newImmFieldsEncoded, newMutFieldsEncoded)
}

fn upgrade(newCode: ByteVec) -> () {
  checkOwner(...)
  let (newImmFieldsEncoded, newMutFieldsEncoded) = ContractName.encodeFields!(newFields...)
  migrateWithFields!(newCode, newImmFieldsEncoded, newMutFieldsEncoded)
}
```

## Inheritance

Ralph also supports multiple inheritance, when a contract inherits from other contracts, only a single contract is created on the blockchain, and the code from all the parent contracts is compiled into the created contract. `Contract` can ONLY "extend" `Abstract Contract`.

```ralph
Abstract Contract Foo(a: U256) {
  pub fn foo() -> () {
    // ...
  }
}

Abstract Contract Bar(b: ByteVec) {
  pub fn bar() -> () {
    // ...
  }
}

// The field name of the child contract must be the same as the field name of parnet contracts.
Contract Baz(a: U256, b: ByteVec) extends Foo(a), Bar(b) {
  pub fn baz() -> () {
    foo()
    bar()
  }
}
```

:::tip note
In Ralph, abstract contracts are not instantiable, which means the following code is invalid:

```ralph
let bazId = // The contract id of `Baz`
Foo(bazId).foo() // ERROR
```

:::

## Interface

Interfaces are similar to abstract contracts with the following restrictions:

- They cannot have any functions implemented.
- They cannot inherit from other contracts, but they can inherit from other interfaces.
- They cannot declare contract fields.

```ralph
Interface Foo {
  event E(a: U256)

  @using(assetsInContract = true)
  pub fn foo() -> ()
}

Interface Bar extends Foo {
  pub fn bar() -> U256
}

Contract Baz() implements Bar {
  // The function signature must be the same as the function signature declared in the interface.
  @using(assetsInContract = true)
  pub fn foo() -> () {
    // Inherit the event from `Foo`
    emit E(0)
    // ...
  }

  pub fn bar() -> U256 {
    // ...
  }
}
```

And you can instantiate a contract with interface:

```ralph
let bazId = // The contract id of `Baz`
Foo(bazId).foo()
let _ = Bar(bazId).bar()
```

Ralph also supports inheritance from multiple interfaces:

```ralph
Interface Foo {
  pub fn foo() -> ()
}

Interface Bar {
  pub fn bar() -> ()
}

Contract Baz() implements Foo, Bar {
  pub fn foo() -> () {}
  pub fn bar() -> () {}
}
```

## TxScript

A transaction script is a piece of code to interact with contracts on the blockchain. Transaction scripts can use the input assets of transactions in general. A script is disposable and will only be executed once along with the holder transaction.

```ralph
Contract Foo() {
  pub fn foo(v: U256) -> () {
    // ...
  }
}

// The `preapprovedAssets` is true by default for `TxScript`.
// We set the `preapprovedAssets` to false because the script does not need assets.
@using(preapprovedAssets = false)
// `TxScript` fields are more like function parameters, and these
// fields need to be specified every time the script is executed.
TxScript Main(foo: Foo) {
  // The body of `TxScript` consists of statements
  bar()
  foo.foo(0)

  // You can also define functions in `TxScript`
  fn bar() -> () {
    // ...
  }
}
```

### Implicit and Explicit Main Function

The `main` function in `TxScript` serves as the entry point for contract code execution. TxScript supports both implicit and explicit definitions of the `main` function:

1. Implicit definition: When Ralph statements are present in the script body,, the compiler automatically generates a `main` function for the `TxScript`.
2. Explicit definition:

```ralph
TxScript Main(foo: Foo) {
  @using(preapprovedAssets = false)
  pub fn main() -> () {
    bar()
    foo.foo(0)
  }
}
```

In an explicit definition, the `main` function cannot accept parameters directly. If parameters are needed, they should be passed as fields of the `TxScript`.

## Gasless Transaction

In Ralph, you can use the built-in `payGasFee` to pay transaction gas fees on behalf of the user, for example:

```ralph
Contract Foo() {
  @using(assetsInContract = true, checkExternalCaller = false)
  pub fn foo() -> () {
    payGasFee!(selfAddress!(), txGasFee!())
  }
}
```

The built-in `payGasFee` has two parameters:

1. The first parameter is the payer address, in the example above, the contract paid the gas fee. But the payer address can also be the user address.
2. The second parameter is the amount of gas to be paid, in the above example, the contract paid all the gas fees. You can choose to pay part of the gas fees.

Note that gasless transactions do not mean that transactions do not require gas fees, but that others pay the gas fees on your behalf. You still need to have ALPH to send transactions.


## Limitations of Ralph
- The maximum number of event fields is 8.
- Contract statements must be in the order of `maps`, `events`, `consts`, `enums` and `methods`.
- Contract fields CANNOT have defaults. The initial field values are set during contract creation.
- Contract fields must be daclared in the order of `immutable`, then `mutable`.
- Contract field declarations aare NOT allowed inside the contract body

```ralph
// Structs must always be declared outside of contract scope
struct Book {
  mut title: ByteVec,
  mut status: U256  // BookStatus
}

// First value of enum must be set explicitly
enum ErrorCodes {
  BookNotFound = 0
  BookBorrowed
  BookListFull
  OnlyMasterCanAdd
}

// Example of a contract that cotains a structure mimicking a list
Contract BookShelf(
  master: Address,  // The address of the account that can add new books
  mut bookListLength: U256  // field representing the current number of books in the list
) {
  mapping[U256, Book] bookList

  event BookAdded(index: U256, title: ByteVec)
  event BookBorrowed(index: U256, title: ByteVec)

  const MAX_BOOKS = 20

  // First value of enum must be set explicitly
  enum BookStatus {
    Available = 0
    Borrowed
  }

  @using(checkExternalCaller = false, updateFields = true)
  pub fn borrowBook(index: U256) -> Book {
    assert!(bookList.contains!(index), ErrorCodes.BookNotFound)
    let mut book = bookList[index]
    assert!(book.status != BookStatus.Borrowed, ErrorCodes.BookBorrowed)
    book.status = BookStatus.Borrowed
    bookList[index] = book
    emit BookBorrowed(index, book.title)
    return book
  }

  @using(updateFields = true)
  pub fn addNewBook(bookTitle: ByteVec) -> () {
    checkCaller!(callerAddress!() == master, ErrorCodes.OnlyMasterCanAdd)
    assert!(bookListLength < MAX_BOOKS, ErrorCodes.BookListFull)
    let book = Book { title: bookTitle, status: BookStatus.Available }
    bookList.insert!(bookListLength, book)
    bookListLength = bookListLength + 1
    emit BookAdded(bookListLength, bookTitle)
  }
}
```
