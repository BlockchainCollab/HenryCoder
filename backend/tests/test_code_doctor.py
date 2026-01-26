from code_doctor import fix_common_errors


class TestEnumFixes:
    """Tests for enum comma removal."""
    
    def test_removes_trailing_commas_from_enum(self):
        code = """Contract Test() {
  enum State {
    Init = 0,
    Active = 1,
  }
}"""
        expected = """Contract Test() {
  enum State {
    Init = 0
    Active = 1
  }
}"""
        result = fix_common_errors(code)
        assert result == expected
    
    def test_preserves_enum_without_commas(self):
        code = """Contract Test() {
  enum State {
    Init = 0
    Active = 1
  }
}"""
        result = fix_common_errors(code)
        assert result == code


class TestUnderscoreFixes:
    """Tests for underscore prefix to suffix conversion."""
    
    def test_converts_underscore_prefix_to_suffix(self):
        code = """fn test(_param: U256) -> () {
  let _local = _param
}"""
        result = fix_common_errors(code)
        assert "param_" in result
        assert "local_" in result
        assert "_param" not in result
        assert "_local" not in result
    
    def test_preserves_underscores_in_strings(self):
        code = """fn test() -> () {
  let msg = "_hello_world"
}"""
        result = fix_common_errors(code)
        assert '"_hello_world"' in result
    
    def test_preserves_underscores_in_comments(self):
        code = """fn test() -> () {
  // _this_is_a_comment
  let x = 1
}"""
        result = fix_common_errors(code)
        assert "// _this_is_a_comment" in result
    
    def test_preserves_underscores_in_backtick_strings(self):
        code = """fn test() -> () {
  let msg = b`_hello`
}"""
        result = fix_common_errors(code)
        assert "b`_hello`" in result


class TestMapInsertFixes:
    """Tests for map.insert! brace syntax removal."""
    
    def test_removes_braces_from_map_insert(self):
        code = """fn test() -> () {
  myMap.insert!{depositorAddress = caller}(key, value)
}"""
        result = fix_common_errors(code)
        assert "myMap.insert!(key, value)" in result
        assert "insert!{" not in result
    
    def test_preserves_correct_map_insert(self):
        code = """fn test() -> () {
  myMap.insert!(key, value)
}"""
        result = fix_common_errors(code)
        assert "myMap.insert!(key, value)" in result


class TestAnnotationFixes:
    """Tests for @using annotation fixes."""
    
    def test_adds_assets_in_contract_for_transfer_from_self(self):
        code = """Contract Test() {
  pub fn withdraw(to: Address) -> () {
    transferTokenFromSelf!(to, tokenId, 100)
  }
}"""
        result = fix_common_errors(code)
        assert "assetsInContract = true" in result
    
    def test_adds_preapproved_assets_for_transfer_to_self(self):
        code = """Contract Test() {
  pub fn deposit(from: Address) -> () {
    transferTokenToSelf!(from, tokenId, 100)
  }
}"""
        result = fix_common_errors(code)
        assert "preapprovedAssets = true" in result
    
    def test_adds_assets_in_contract_for_token_remaining_self(self):
        code = """Contract Test() {
  pub fn getBalance() -> U256 {
    return tokenRemaining!(selfAddress!(), tokenId)
  }
}"""
        result = fix_common_errors(code)
        assert "assetsInContract = true" in result
    
    def test_adds_update_fields_for_mutable_field_assignment(self):
        code = """Contract Test(mut counter: U256) {
  pub fn increment() -> () {
    counter = counter + 1
  }
}"""
        result = fix_common_errors(code)
        assert "updateFields = true" in result
    
    def test_adds_update_fields_for_mapping_assignment(self):
        code = """Contract Test() {
  mapping[Address, U256] balances
  
  pub fn withdraw(amount: U256) -> () {
    let sender = callerAddress!()
    balances[sender] = balances[sender] - amount
  }
}"""
        result = fix_common_errors(code)
        assert "updateFields = true" in result
    
    def test_simple_bank_deposit_no_update_fields_nested(self):
        """Test that deposit function with mapping assignment INSIDE if block does NOT get updateFields.
        
        updateFields is only required when the assignment is at the main scope of the function,
        not inside conditionals or other nested blocks.
        """
        code = """Contract SimpleBank() {
  mapping[Address, U256] balances

  @using(preapprovedAssets = true, checkExternalCaller = false, payToContractOnly = true)
  pub fn deposit(amount: U256) -> () {
    transferTokenToSelf!(callerAddress!(), ALPH, amount)
    let sender = callerAddress!()
    if (balances.contains!(sender)) {
      balances[sender] = balances[sender] + amount
    } else {
      balances.insert!(sender, sender, amount)
    }
  }
}"""
        result = fix_common_errors(code)
        # updateFields NOT needed because assignment is inside if block
        assert "updateFields = true" not in result
        # Check indentation is preserved (2 spaces)
        lines = result.split('\n')
        for line in lines:
            if 'pub fn deposit' in line:
                assert line.startswith('  '), f"Expected 2-space indent, got: '{line}'"
    
    def test_main_scope_mapping_assignment_gets_update_fields(self):
        """Test that mapping assignment at MAIN SCOPE does get updateFields = true."""
        code = """Contract SimpleBank() {
  mapping[Address, U256] balances

  pub fn transfer(to: Address, amount: U256) -> () {
    let sender = callerAddress!()
    balances[sender] = balances[sender] - amount
    balances[to] = balances[to] + amount
  }
}"""
        result = fix_common_errors(code)
        # updateFields IS needed because assignments are at main scope
        assert "updateFields = true" in result
    
    def test_adds_preapproved_assets_for_map_insert(self):
        code = """Contract Test() {
  mapping[Address, U256] balances
  
  pub fn setBalance(addr: Address, amount: U256) -> () {
    balances.insert!(addr, amount)
  }
}"""
        result = fix_common_errors(code)
        assert "preapprovedAssets = true" in result
    
    def test_adds_check_external_caller_false_for_public_without_check_caller(self):
        code = """Contract Test(mut val: U256) {
  pub fn update(newVal: U256) -> () {
    val = newVal
  }
}"""
        result = fix_common_errors(code)
        assert "checkExternalCaller = false" in result
    
    def test_no_check_external_caller_for_private_function(self):
        code = """Contract Test(mut val: U256) {
  fn innerUpdate(newVal: U256) -> () {
    val = newVal
  }
}"""
        result = fix_common_errors(code)
        assert "checkExternalCaller = false" not in result
        assert "updateFields = true" in result
    
    def test_no_check_external_caller_when_check_caller_present(self):
        code = """Contract Test(mut val: U256, owner: Address) {
  pub fn update(newVal: U256) -> () {
    checkCaller!(callerAddress!() == owner, 1)
    val = newVal
  }
}"""
        result = fix_common_errors(code)
        assert "checkExternalCaller = false" not in result
        assert "updateFields = true" in result
    
    def test_adds_pay_to_contract_only_when_preapproved_with_transfer_to_self(self):
        code = """Contract Test() {
  pub fn deposit(from: Address) -> () {
    transferTokenToSelf!(from, tokenId, 100)
  }
}"""
        result = fix_common_errors(code)
        assert "preapprovedAssets = true" in result
        assert "payToContractOnly = true" in result
    
    def test_no_pay_to_contract_only_for_map_insert(self):
        # map.insert! requires preapprovedAssets but should NOT have payToContractOnly
        code = """Contract Test() {
  mapping[Address, U256] balances
  
  pub fn setBalance(addr: Address, amount: U256) -> () {
    balances.insert!(addr, amount)
  }
}"""
        result = fix_common_errors(code)
        assert "preapprovedAssets = true" in result
        assert "payToContractOnly = true" not in result
    
    def test_no_pay_to_contract_only_when_both_preapproved_and_assets_in_contract(self):
        code = """Contract Test() {
  pub fn swap(from: Address, to: Address) -> () {
    transferTokenToSelf!(from, tokenId, 100)
    transferTokenFromSelf!(to, tokenId, 50)
  }
}"""
        result = fix_common_errors(code)
        assert "preapprovedAssets = true" in result
        assert "assetsInContract = true" in result
        assert "payToContractOnly = true" not in result
    
    def test_adds_preapproved_assets_for_transfer_token(self):
        code = """Contract Test() {
  pub fn transfer(from: Address, to: Address) -> () {
    transferToken!(from, to, tokenId, 100)
  }
}"""
        result = fix_common_errors(code)
        assert "preapprovedAssets = true" in result
    
    def test_adds_preapproved_assets_for_create_contract(self):
        code = """Contract Test() {
  pub fn deploy(caller: Address, bytecode: ByteVec) -> ByteVec {
    return createContract!{caller -> ALPH: 1 alph}(bytecode, #, #)
  }
}"""
        result = fix_common_errors(code)
        assert "preapprovedAssets = true" in result
    
    def test_preserves_indentation(self):
        code = """Contract Test(mut val: U256) {
  pub fn update() -> () {
    val = 10
  }
}"""
        result = fix_common_errors(code)
        # Check that the annotation is properly indented
        lines = result.split('\n')
        for i, line in enumerate(lines):
            if '@using' in line:
                # The next line should have the same indentation (2 spaces)
                assert line.startswith('  ')


class TestComplexScenarios:
    """Tests for complex real-world scenarios."""
    
    def test_full_contract_fix(self):
        code = """Contract Token(mut supply: U256, owner: Address) {
  enum ErrorCodes {
    NotOwner = 1,
    InvalidAmount = 2,
  }
  
  pub fn mint(_to: Address, _amount: U256) -> () {
    checkCaller!(callerAddress!() == owner, ErrorCodes.NotOwner)
    transferTokenFromSelf!(_to, selfTokenId!(), _amount)
    supply = supply + _amount
  }
  
  pub fn deposit(_from: Address, _amount: U256) -> () {
    transferTokenToSelf!(_from, selfTokenId!(), _amount)
  }
  
  fn _innerBurn(amount: U256) -> () {
    supply = supply - amount
  }
}"""
        result = fix_common_errors(code)
        
        # Enum commas removed
        assert "NotOwner = 1," not in result
        assert "NotOwner = 1" in result
        
        # Underscores fixed
        assert "to_" in result or "to:" in result  # param renamed
        assert "amount_" in result or "amount:" in result
        assert "_to" not in result
        assert "_amount" not in result
        assert "_from" not in result
        
        # innerBurn should not have leading underscore
        assert "innerBurn_" in result or "fn innerBurn" in result
        
        # Annotations added
        assert "assetsInContract = true" in result
        assert "updateFields = true" in result
        assert "preapprovedAssets = true" in result


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_empty_contract(self):
        code = """Contract Empty() {
}"""
        result = fix_common_errors(code)
        assert result == code
    
    def test_contract_with_only_fields(self):
        code = """Contract OnlyFields(owner: Address, mut count: U256) {
}"""
        result = fix_common_errors(code)
        assert result == code
    
    def test_multiple_contracts(self):
        code = """Contract First(mut val: U256) {
  pub fn update() -> () {
    val = 1
  }
}

Contract Second(mut count: U256) {
  pub fn increment() -> () {
    count = count + 1
  }
}"""
        result = fix_common_errors(code)
        assert result.count("updateFields = true") == 2
    
    def test_nested_braces_mut_field_requires_update_fields(self):
        """Test that mut field assignments inside if/else blocks DO require updateFields.
        
        Mutable fields always require updateFields regardless of scope.
        Only mapping assignments have the main-scope-only rule.
        """
        code = """Contract Test(mut val: U256) {
  pub fn complex() -> () {
    if (true) {
      val = 1
    } else {
      val = 2
    }
  }
}"""
        result = fix_common_errors(code)
        # Mut field assignments ALWAYS require updateFields, even in nested blocks
        assert "updateFields = true" in result
    
    def test_does_not_match_comparison_as_assignment(self):
        code = """Contract Test(mut val: U256) {
  pub fn check() -> Bool {
    return val == 10
  }
}"""
        result = fix_common_errors(code)
        # Should NOT have updateFields since val == 10 is comparison, not assignment
        assert "updateFields = true" not in result

    def test_simple_bank_scope(self):
        """Test scenario to ensure updateFields is only added to main scope assignments."""
        code = """  @using(checkExternalCaller = false, preapprovedAssets = true, payToContractOnly = true)
  pub fn deposit(amount: U256) -> () {
    assert!(amount > 0, DEPOSIT_AMOUNT_MUST_BE_GREATER_THAN_ZERO)
    // @@@ Native assets are transferred to the contract using transferTokenToSelf! with preapprovedAssets.
    transferTokenToSelf!(callerAddress!(), ALPH, amount)

    let sender = callerAddress!()
    if (balances.contains!(sender)) {
      balances[sender] = balances[sender] + amount
    } else {
      // @@@ Ralph requires a storage deposit of 0.1 ALPH for each entry in the mapping.
      balances.insert!(sender, sender, amount)
    }
    emit Deposit(sender, amount)
  }

  @using(checkExternalCaller = false, assetsInContract = true)
  pub fn withdraw(amount: U256) -> () {
    let sender = callerAddress!()
    assert!(balances.contains!(sender), INSUFFICIENT_BALANCE)
    let currentBalance = balances[sender]
    assert!(currentBalance >= amount, INSUFFICIENT_BALANCE)
    
    balances[sender] = currentBalance - amount
    // @@@ Reentrancy is prevented at the VM level in Alephium, so manual guards are unnecessary.
    transferTokenFromSelf!(sender, ALPH, amount)
    
    emit Withdrawal(sender, amount)
  }

  @using(checkExternalCaller = false, preapprovedAssets = true)
  pub fn transfer(to: Address, amount: U256) -> () {
    assert!(to != nullContractAddress!(), INVALID_RECIPIENT)
    let sender = callerAddress!()
    assert!(balances.contains!(sender), INSUFFICIENT_BALANCE)
    
    let senderBalance = balances[sender]
    assert!(senderBalance >= amount, INSUFFICIENT_BALANCE)
    
    balances[sender] = senderBalance - amount
    
    if (balances.contains!(to)) {
      balances[to] = balances[to] + amount
    } else {
      // @@@ In simple logic, the sender pays the storage deposit for the recipient's map entry.
      balances.insert!(sender, to, amount)
    }
    
    emit Transfer(sender, to, amount)
  }
"""
        # Pass mapping names to simulate the agent service behavior
        result = fix_common_errors(code, mappings={'balances'})
        
        # Extract each function's @using annotation
        import re
        functions = re.findall(r'(@using\([^)]+\)\s+pub fn \w+)', result)
        
        # Check that withdraw and transfer got updateFields = true
        assert "updateFields = true" in functions[1], f"withdraw missing updateFields: {functions[1]}"
        assert "updateFields = true" in functions[2], f"transfer missing updateFields: {functions[2]}"
        
        # Check that deposit did NOT get updateFields = true
        assert "updateFields = true" not in functions[0], f"deposit should NOT have updateFields: {functions[0]}"

    def test_multiline_contract_parameters_field_detection(self):
        """Test that mutable field assignments are detected in contracts with multiline parameters."""
        code = """Abstract Contract NFTCollectionRoyalty(
  mut defaultRoyaltyRecipient: Address,
  mut defaultRoyaltyBps: U256
) {
  fn setDefaultRoyalty(recipient: Address, bps: U256) -> () {
    defaultRoyaltyRecipient = recipient
    defaultRoyaltyBps = bps
  }
}"""
        result = fix_common_errors(code)
        
        # Should add updateFields annotation since it modifies mutable fields
        assert "@using(updateFields = true)" in result, "Should detect field assignments in multiline contract parameters"
        assert "fn setDefaultRoyalty" in result

    def test_indentation(self):
        """Test that mutable field assignments are detected in contracts with multiline parameters."""
        code = """\
  @using(preapprovedAssets = true)
  pub fn mint(uri: ByteVec) -> ByteVec {
    let caller = callerAddress!()
    tokenURIs.insert!(caller, index, uri)
  }
 

  pub fn getTotalSupply() -> U256 {
    return totalSupply()
  }"""
        expected = """\
  @using(preapprovedAssets = true, updateFields = true, checkExternalCaller = false)
  pub fn mint(uri: ByteVec) -> ByteVec {
    let caller = callerAddress!()
    tokenURIs.insert!(caller, index, uri)
  }
 

  pub fn getTotalSupply() -> U256 {
    return totalSupply()
  }"""
        result = fix_common_errors(code, mappings={'tokenURIs'})
        
        # Should add updateFields and checkExternalCaller=false since it modifies mappings and is public
        assert result == expected
