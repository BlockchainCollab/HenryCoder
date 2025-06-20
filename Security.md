# Security advisory

## Tips

### Integer Overflows
Use newer versions of Solidity to match the logic more accurately, the translator assumes that math operations are checked by default.

## Findings and issues
### Finding 1: Enums are left unchecked
Solidity functions that accept an enum as an argument are checked by default at runtime (it is impossible to pass an invalid enum value). Ralph does not allow enums as arguments, so the enum value is passed as an `U256` type. This means that the enum value is not checked at runtime, and it is possible to pass an invalid enum value. This can lead to unexpected behavior in the contract.

### Finding 2: Blockchain timestamp resolution
Solidity's `block.timestamp` resolution is 1 second, while Ralph's `block.timestamp` resolution is 1 millisecond. This means that if you use `block.timestamp` in your contract, you need to be careful about the granularity of the timestamp. If you are using `block.timestamp` to calculate a time difference, you need to make sure that the time difference is in milliseconds.
