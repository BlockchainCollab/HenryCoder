Ralph is a statically typed language, but you don't need to specify the type for local variables and constants thanks to type inference.
All types of Ralph are value types, i.e. they are always copied when they are used as function arguments or assigned.
Currently, Ralph only supports the following data types:

### Primitive Types

#### U256

```ralph
// The type of `a` ... `d` is U256.
let a = 10
let b = 10u
let c = 1_000_000_000
let d = 1e18
```

#### I256

```ralph
// The type of `a` ... `d` is I256.
let a = -10
let b = 10i
let c = -1_000_000_000
let d = -1e18
```

#### Bool

```ralph
// The type of `a` and `b` is Bool.
let a = false
let b = true
```

#### ByteVec

```ralph
// ByteVec literals must start with `#` followed by a hex string.
let a = #00112233
// ByteVec concatenation
let b = #0011 ++ #2233 // `b` is #00112233
// Empty ByteVec
let c = #
```

#### Address

```ralph
// Address literals must start with `@` followed by a valid base58 encoded Alephium address.
let a = @1DrDyTr9RpRsQnDnXo2YRiPzPW4ooHX5LLoqXrqfMrpQH
```

#### String

Ralph does not have a native type for strings, but you can define string literals which are encoded in `ByteVec`.

```ralph
// String literals starts with `b`.
let a = b`Hello`
let b = b`World`
let c = a ++ b` ` ++ b
```

### Tuple

Ralph supports tuples, which are values that contain fixed number of
elements, each with its own type.

```ralph
// Function that returns a tuple of 3 elements
fn foo() -> (U256, Boolean, ByteVec) {
  return 1, false, #00
}

// Destructure the tuple, `a` is immutable, `b` is mutable.
// `_` is the anonymous variable to ignore the unnecessary variable
let (a, mut b, _) = foo()
```

### Fixed Size Array

The syntax for fixed-size arrays is influenced by Rust.

```ralph
// The type of `a0` is [U256; 4]
let a0 = [0, 1, 2, 3]

// The type of `a1` is [[U256, 2]; 2]
let a1 = [[0, 1], [2, 3]]

// The type of `a2` is [I256; 3]
let a2 = [0i; 3]

// The type of `a3` is [ByteVec; 4]
let a3 = [#00, #11, #22, #33]
```

Fixed-size arrays can be used as Contract fields, example:

```ralph
Contract Foo(
  owners: [Address; 4],
  mut balances: [U256; 4]
) {
  // ...
}
```

### Struct

In Ralph, Structs can be globally defined and can contain fields that are either mutable or immutable. However, to assign a value to a field, all of the field selectors must be mutable.
E.g. in order to set `foo.x.y.z = 123`, all `foo`, `x`, `y`, and `z` must be mutable.

```ralph
// Structs have to be defined globally
struct Foo { x: U256, mut y: U256 }
struct Bar { z: U256, mut foo: Foo }

Contract Baz() {
  ...

  pub fn baz() -> () {
    // f.y = 3 won't work as f is immutable despite the field y being mutable
    let f = Foo { x: 1, y: 2 }

    // ff = f won't work as ff.x is immutable despite ff and ff.y being mutable
    let mut ff = Foo { x: 1, y: 2 }
    ff.y = 3 // This works as both ff and y are mutable

    // b.foo.y = 5 won't work as b is immutable
    let b = Bar { z: 4, foo: f }

    let mut bb = Bar { z: 5, foo: f }
    bb.foo.y = 6 // This works as bb, foo, and y are all mutable
  }

  ...
}
```

In Ralph, structs are value types, not reference types. When assigned to a new struct variable, it copies all fields to the new struct variable:

```ralph
struct Foo { mut x: U256, mut y: U256 }
Contract Bar() {
  pub fn bar() -> () {
    let foo0 = Foo { x: 0, y: 1 }
    let mut foo1 = foo0
    foo1.x = 1 // modifying foo1.x will not change foo0.x
    assert!(foo0.x == 0, 0)
    assert!(foo1.x == 1, 0)
  }
}
```

Ralph also supports destructuring struct, and the syntax is similar to TypeScript:

```ralph
struct Foo { x: U256, y: U256 }
Contract Bar() {
  pub fn bar() -> () {
    let foo = Foo { x: 0, y: 1 }
    let Foo { mut x, y } = foo
    x = 1

    // the variables `x` and `y` already exist, we create two new variables `x1` and `y1`
    let Foo { x: x1, y: y1 } = foo
  }
}
```

### Map

In Ralph, Maps are defined as global contract attributes, eliminating the need for initialization. The syntax is `mapping[KeyType, ValueType] mapName` where the `KeyType` can be any primitive types (Bool, U256, I256, Address, ByteVec), and the `ValueType` can be any type.

Under the hood, each Map entry is constructed as a subcontract of the current contract. Therefore, creating a map entry entails a minimal contract deposit, easily done using the built-in function `mapEntryDeposit!()`.

There are 3 essential built-in map methods `insert!, remove!, contains!` (see [doc](https://docs.alephium.org/ralph/built-in-functions/#map-functions)). Map values can be accessed and updated with the bracket syntax `map[key] = newValue`. Below are some examples illustrating their usage. For more comprehensive examples, refer to the [blind-auction](https://github.com/alephium/ralph-example/tree/master/blind-auction) repository and the [unit tests here](https://github.com/alephium/alephium-web3/blob/master/test/contract.test.ts#L448-L477).

```ralph
Contract Counters() {
  // All maps must be defined here with `mapping[KeyType, ValueType]`, before events and constants
  mapping[Address, U256] counters

  @using(preapprovedAssets = true, checkExternalCaller = false, updateFields = true)
  pub fn create() -> () {
    let key = callerAddress!()
    let depositor = key
    // The depositor will deposit a minimal ALPH deposit for the new map entry which is a subcontract
    counters.insert!(depositor, key, 0)
  }

  @using(checkExternalCaller = false, updateFields = true)
  pub fn count() -> () {
    let key = callerAddress!()
    let value = counters[key]
    // Update the map entry value
    counters[key] = value + 1
  }

  @using(checkExternalCaller = false, updateFields = true)
  pub fn clear() -> U256 {
    let key = callerAddress!()
    let depositRecipient = key
    let value = counters[key]
    // Each map entry removal redeems the map entry deposit
    counters.remove!(depositRecipient, key)
    return value
  }

  pub fn contains() -> Bool {
    // Check the existence of map entry
    return counters.contains!(callerAddress!())
  }
}
```

Ralph's mappings cannot be nested, one way to work around this is to use a ByteVec as the key and use `encodeToByteVec!(key1, key2)` to encode the keys into a single key.

```ralph
Contract NestedMap() {
  // This is an efficient way to do manage multi dimensional maps
  // In solidity this would be `mapping(Address => mapping(Address => String)) messages`
  // Ralph must use `ByteVec` type for text
  mapping[ByteVec, ByteVec] messages

  @inline fn getMessagesKey(a: Address, b: Address) -> ByteVec {
    return encodeToByteVec!(a, b)
  }

  pub fn setMessage(to: Address, message: ByteVec) -> () {
    // Don't allow sending messages to self
    checkCaller!(to != callerAddress!(), 1001)
    let key = getMessagesKey(callerAddress!(), to)
    // When state changes happen inside a conditional block `@using(updateFields = true)` is not needed
    if messages.contains!(key) {
      messages[key] = message
    } else {
      messages.insert!(key, message)
    }
  }
}
```

### Constants

Ralph supports defining constants of primitive types. Constant names must start with an uppercase letter. We recommend using the SCREAMING_SNAKE_CASE naming convention for constants:

```ralph
const TOTAL_SUPPLY = 1e18
```

Ralph also supports compile-time evaluation of constants:

```ralph
const A = 10
const B = 20
const C = A * B // A and B must be defined before C
```

Ralph allows you to define global constants that can be used in any contracts or scripts:

```ralph
const TOTAL_SUPPLY = 1e18
const ERROR_CODE = 0

Contract Token() {
  pub fn getTotalSupply() -> U256 {
    return TOTAL_SUPPLY
  }
}

TxScript Main(token: Token) {
  assert!(token.getTotalSupply() == TOTAL_SUPPLY, ERROR_CODE)
}
```

You can also define contract-specific local constants. These constants can only be used within the contract and **must not** have the same names as global constants:

```ralph
Contract Token() {
  const TOTAL_SUPPLY = 1e18

  pub fn getTotalSupply() -> U256 {
    return TOTAL_SUPPLY
  }
}
```

#### Enum

Similar to constant definitions, Ralph supports both global and local enum definitions:
The underlying type of enum is `U256`. Enums are not a concrete type, so you will have to use an `U256` if you want to store the enum value or pass it as an argument.\
NOTE that `enum`s don't use commas `,` after each element.

```ralph
enum GlobalErrorCode {
  INVALID_CALLER_CONTRACT = 0
  INVALID_CALLER_ADDRESS = 1
}

enum Refrigerable {
  FRIDGE = 0
  FREEZER = 1
  OTHER = 2
}

Contract Foo(owner: Address, parentId: ByteVec, mut refrigerable: U256) {
  enum LocalErrorCode {
    INVALID_OWNER = 1
  }

  pub fn foo(caller: Address) -> () {
    assert!(callerContractId!() == parentId, GlobalErrorCode.INVALID_CALLER_CONTRACT)
    assert!(caller == owner, LocalErrorCode.INVALID_OWNER)
  }

  @using(updateFields = true)
  pub setRefrigerable(refrigerable: U256) -> () {
    self.refrigerable = refrigerable
  }
}
```
