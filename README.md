# HenryCoder

## Examples
See example usages and further advice in the [examples](examples) directory.

## Tips
- The whole contract suite should be provided as one file. Other dependencies will be translated with the main contract, however the translation quality is the highest with a single, self-contained contract.

## Partially supported features
Certain EVM constructs cannot be translated directly to Ralph, but can be approximated or implemented with workarounds. These include:

- **Modifiers**: Ralph does not support modifiers directly. Instead, the translator will try to immitate the modifier logic using function calls. This may not always be possible, especially for complex modifiers.
- **Multi-dimensional Mappings**: Ralph does not support multi-dimensional mappings directly. Instead, you can use a `ByteVec` as the key and encode multiple keys into a single key using `encodeToByteVec!(key1, key2)`.
- **Dynamic-length Arrays**: Ralph does not have a built-in dynamic-length array type. Instead, you can use a mapping with a `U256` index to simulate dynamic arrays. However, this may be more expensive than on some EVM chains as subcontract creation requires locking 0.1 ALPH
- **Inheritance**: Ralph supports inheritance, but it is more restrictive than EVM. A contract can only extend an `Abstract Contract`, and the fields in the parent contract must match exactly the fields in the child contract. The child contract can add additional fields, but cannot remove or change the existing ones. Multiple inheritance is supported, but methods cannot overlap and child cannot override parent methods.

## Unsupported features
Certain EVM features are completely unsupported in Ralph VM or require complex workarounds. These include:

- **Transient Storage**: EVM, especially since the Shanghai upgrade, allows for temporary storage not persisted across transactions.
- **Inline Assembly**: EVM supports low-level assembly code within Solidity for fine-grained control, while Alephium's Ralph language focuses on high-level simplicity.
- **In-memory Dynamic-length Arrays**: EVM supports variable-length arrays that can be manipulated in memory, while Ralph does not have a direct equivalent or a simple workaround.

## Security advisory
For tips and known issues regarding translation from EVM see [Security.md](Security.md).
