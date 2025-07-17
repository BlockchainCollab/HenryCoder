# Token Lock translation

## Solidity source
The solidity code is available online at: https://solidity-by-example.org/defi/token-lock/

## ralph translation

### Settings
```json
{
  "optimize": false,
  "include_comments": true,
  "mimic_defaults": false,
  "translate_erc20": true,
  "smart": true
}
```

### Recommended next steps
1. Check if the `sync` function is necessary - it has been removed by Henry and is probably not needed because Alephium doesn't allow unsolicited token deposits
2. Make sure that the `Auth` contract is `Abstract Contract` so that it can be inherited from. If you need to make instances of both `Auth` and `TokenLock`, you will have to create a common abstract contract ex. `Abstract Contract AuthBase` and then inherit from it in both `Auth` and `TokenLock`.
3. Verify that the `checkAuth` modifier's logic is translated correctly
3. Verify that the contract code is correct and that all storage variables are being set correctly

### Output code

```rust
Contract Auth(initialOwner: Address, mut initialized: Bool) {  
    mapping[Address, Bool] authorized

    // Initialize authorization with contract deployer
    @using(updateFields = true)
    pub fn init() -> () {
        assert!(!initialized, 1001)
        authorized[initialOwner] = true
        initialized = true
    }

    // Internal authorization check
    fn checkAuth() -> () {
        let caller = callerAddress!()
        assert!(authorized[caller], 1002)
    }

    // Add authorized user
    @using(updateFields = true)
    pub fn allow(user: Address) -> () {
        checkAuth()
        authorized[user] = true
    }

    // Remove authorized user
    @using(updateFields = true)
    pub fn deny(user: Address) -> () {
        checkAuth()
        authorized[user] = false
    }
}

// Lock structure for token vesting
struct Lock {
    mut amount: U256,       // Locked token amount
    mut updatedAt: U256,    // Last update timestamp (seconds)
    mut expiresAt: U256,    // Lock expiry timestamp (seconds)
    mut duration: U256      // Lock duration (seconds)
}

Contract TokenLock(initialOwner: Address, mut initialized: Bool) extends Auth(initialOwner, initialized) {
    mapping[ByteVec, Lock] locks      // TokenID -> Lock details
    mapping[ByteVec, U256] freed      // TokenID -> Amount already freed

    // Initialize authorization
    @using(updateFields = true)
    pub fn initAuth() -> () {
        assert!(!initialized, 1001)
        authorized[initialOwner] = true
        initialized = true
    }

    // Get lock details for token
    pub fn get(tokenId: ByteVec) -> Lock {
        return locks[tokenId]
    }

    // Set lock duration for token
    @using(updateFields = true)
    pub fn set(tokenId: ByteVec, duration: U256) -> () {
        checkAuth()
        let mut lock = locks[tokenId]
        lock.duration = duration
        locks[tokenId] = lock
    }

    // Calculate unlocked amount for token
    pub fn unlocked(tokenId: ByteVec) -> U256 {
        let lock = locks[tokenId]
        let currentTime = blockTimeStamp!() / 1000  // Convert ms to seconds
        
        if currentTime >= lock.expiresAt {
            return lock.amount
        }
        return lock.amount * (currentTime - lock.updatedAt) / (lock.expiresAt - lock.updatedAt)
    }

    // Calculate claimable amount (freed + unlocked)
    pub fn claimable(tokenId: ByteVec) -> U256 {
        return freed[tokenId] + unlocked(tokenId)
    }

    // Lock tokens
    @using(updateFields = true, preapprovedAssets = true)
    pub fn lock(tokenId: ByteVec, amount: U256) -> () {
        checkAuth()
        let caller = callerAddress!()
        let free = unlocked(tokenId)
        let mut lock = locks[tokenId]
        
        // Update lock state
        lock.amount = lock.amount - free
        lock.updatedAt = blockTimeStamp!() / 1000
        lock.expiresAt = lock.updatedAt + lock.duration
        freed[tokenId] = freed[tokenId] + free
        
        // Add new tokens to lock
        if amount > 0 {
            // Native token transfer (replaces ERC20 transferFrom)
            transferTokenToSelf!(caller, tokenId, amount)
            lock.amount = lock.amount + amount
        }
        
        locks[tokenId] = lock
    }

    // Unlock tokens
    @using(updateFields = true, assetsInContract = true)
    pub fn unlock(tokenId: ByteVec) -> U256 {
        checkAuth()
        let caller = callerAddress!()
        let free = unlocked(tokenId)
        let mut lock = locks[tokenId]
        
        // Update lock state
        lock.amount = lock.amount - free
        lock.updatedAt = blockTimeStamp!() / 1000
        let amount = freed[tokenId] + free
        freed[tokenId] = 0
        
        // Transfer unlocked tokens
        if amount > 0 {
            // Native token transfer (replaces ERC20 transfer)
            transferTokenFromSelf!(caller, tokenId, amount)
        }
        
        locks[tokenId] = lock
        return amount
    }

    // Sync token balances (not directly portable - commented out)
    /*
    pub fn sync(tokenId: ByteVec) -> () {
        checkAuth()
        // Not implemented - Alephium doesn't have direct balanceOf equivalent
        // Original functionality relied on ERC20 balanceOf which isn't available
    }
    */
}
```