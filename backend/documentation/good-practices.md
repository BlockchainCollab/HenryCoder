The list of good practices for expert EVM to Ralph translators is as follows:

### No commas in enum
In Ralph, enum definitions must end with a line break. Commas will result in a compilation error.

```ralph
Contract Roles(
  mut owner: Address
) {
  mapping[Address, U256] roles

  // Enums in Ralph must always be defined without commas
  enum Role {
    NotDefined = 0
    Admin = 1
    User = 2
  }

  enum ErrorCodes {
    NotOwner = 1
    NotAdmin = 2
  }

  @using(updateFields = true)
  pub fn changeOwner(newOwner: Address) -> () {
    checkCaller!(externalCallerAddress!() == owner, ErrorCodes.NotOwner)
    owner = newOwner
  }

  pub fn getRole() -> U256 {
    // add below code if mimic solidity defaults is set to true:
    // if (!roles.exists!(externalCallerAddress!())) {
    //   return Role.Default
    // }
    return roles[externalCallerAddress!()]
  }

  pub fn setRole(user: Address, role: U256) -> () {
    checkCaller!(getRole() == Role.Admin, ErrorCodes.NotAdmin)
    if (roles.contains!(user)) {
      roles[user] = role
    } else {
      roles.insert!(user, role)
    }
  }
}
```


### No underscores at beginning of names
Ralph doesn't support names that start with underscores.
You can only use underscore `_` as a suffix.
Best practice is to use names such as innerBurn, innerMint, etc.

```ralph
import "std/fungible_token_interface"

Contract SimpleToken(
  owner: Address,
  mut supply: U256
) implements IFungibleToken {
  enum ErrorCodes {
    NotOwner = 1
    InvalidAmount = 2
  }

  pub fn getSymbol() -> ByteVec {
    return b`STK`
  }

  pub fn getName() -> ByteVec {
    return b`SimpleToken`
  }

  pub fn getDecimals() -> U256 {
    return 8
  }
  pub fn getTotalSupply() -> U256 {
    return supply
  }

  @using(updateFields = true, assetsInContract = true)
  fn innerMint(to_: Address, amount_: U256) -> () {
    transferTokenFromSelf!(to_, selfTokenId!(), amount_)
    supply = supply + amount_
  }

  @using(updateFields = true, preapprovedAssets = true, payToContractOnly = true)
  fn innerBurn(from: Address, amount_: U256) -> () {
    transferTokenToSelf!(from_, selfTokenId!(), amount_)
    supply = supply - amount_
  }

  pub fn mint(to: Address, amount: U256) -> () {
    checkCaller!(externalCallerAddress!() == owner, ErrorCodes.NotOwner)
    // Make sure the amount is valid
    assert!(amount > 0, ErrorCodes.InvalidAmount)
    
    // Mint the tokens
    mint_(to, amount)
  }

  @using(preapprovedAssets = true, checkExternalCaller = false)
  pub fn burn(from: Address, amount: U256) -> () {
    // Make sure the amount is valid
    assert!(amount > 0, ErrorCodes.InvalidAmount)
    // Burn the tokens
    burn_{from -> selfTokenId!(): amount}(from, amount)
  }
}
```
