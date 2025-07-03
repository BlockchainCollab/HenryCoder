The list of good practices for expert EVM to Ralph translators is as follows:

### No commas in enum
In Ralph, enum definitions should end with a line break.

```ralph
Contract Roles(
  mut owner: Address
) {
  mapping[Address, U256] roles

  enum Role {
    Default = 0
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
