import pytest
from agent_service import (
    RalphSource, Contract, Field, MapDef, RalphEvent, Constant, RalphEnum, EnumValue, Struct, Interface,
    _extract_ralph_code, _safe_parse_fields, fields_validator
)

def test_extract_ralph_code():
    # Test with markdown fences
    code = "```ralph\nTxId txId\n```"
    assert _extract_ralph_code(code) == "TxId txId"
    
    # Test with generic fences
    code = "```\nTxId txId\n```"
    assert _extract_ralph_code(code) == "TxId txId"
    
    # Test without fences
    code = "  TxId txId  "
    assert _extract_ralph_code(code) == "TxId txId"
    
    # Test with text before/after
    code = "Here is some code:\n```ralph\nTxId txId\n```\nHope it helps!"
    assert _extract_ralph_code(code) == "TxId txId"

def test_safe_parse_fields():
    # Test valid dicts
    fields = [{"name": "foo", "type": "U256"}, {"name": "bar", "type": "Address"}]
    parsed = _safe_parse_fields(fields)
    assert len(parsed) == 2
    assert parsed[0].name == "foo"
    assert parsed[1].type == "Address"
    
    # Test colon strings
    fields = ["foo: U256", "bar : Address"]
    parsed = _safe_parse_fields(fields)
    assert len(parsed) == 2
    assert parsed[0].name == "foo"
    assert parsed[1].type == "Address"
    
    # Test mixed and invalid
    fields = [{"name": "foo", "type": "U256"}, "broken string", 123]
    parsed = _safe_parse_fields(fields)
    assert len(parsed) == 1
    assert parsed[0].name == "foo"

def test_fields_validator():
    contract = Contract(
        name="Test",
        abstract=False,
        fields_immutable=[Field(name="owner", type="Address")],
        fields_mutable=[Field(name="count", type="U256")]
    )
    
    # Test valid new field
    new_fields = [Field(name="newField", type="Bool")]
    err, added, ignored = fields_validator(contract, new_fields)
    assert err is None
    assert len(added) == 1
    assert len(ignored) == 0
    
    # Test duplicate field (existing)
    new_fields = [Field(name="owner", type="Address")]
    err, added, ignored = fields_validator(contract, new_fields)
    assert err is None
    assert len(added) == 0
    assert "owner" in ignored
    
    # Test duplicate within batch
    new_fields = [Field(name="f1", type="U256"), Field(name="f1", type="U256")]
    err, added, ignored = fields_validator(contract, new_fields)
    assert err is None
    assert len(added) == 1
    assert "f1" in ignored
    
    # Test invalid name (must start with lowercase)
    new_fields = [Field(name="Invalid", type="U256")]
    err, added, ignored = fields_validator(contract, new_fields)
    assert err is not None
    assert "must start with a lowercase letter" in err

def test_ralph_source_render_basic():
    source = RalphSource()
    source.global_consts.append(Constant(name="VERSION", type="U256", value="1"))
    
    contract = Contract(
        name="Basic",
        abstract=False,
        fields_immutable=[Field(name="owner", type="Address")],
        methods="fn getOwner() -> Address { return owner }"
    )
    source.contracts["Basic"] = contract
    
    rendered = source.render()
    assert "const VERSION: U256 = 1" in rendered
    assert "Contract Basic(\n  owner: Address\n)" in rendered
    assert "fn getOwner() -> Address { return owner }" in rendered

def test_ralph_source_render_inheritance():
    source = RalphSource()
    parent = Contract(
        name="Parent",
        abstract=True,
        fields_immutable=[Field(name="p1", type="U256")],
        fields_mutable=[Field(name="m1", type="Address")]
    )
    source.contracts["Parent"] = parent
    
    child = Contract(
        name="Child",
        abstract=False,
        parent_contracts=["Parent"],
        fields_immutable=[Field(name="c1", type="Bool")]
        # Note: Child MUST have p1 and m1 if it extends Parent and they aren't explicitly provided, 
        # but RalphSource.render handles the inference.
    )
    source.contracts["Child"] = child
    
    rendered = source.render()
    # Check inheritance call
    assert "Contract Child(" in rendered
    assert "extends Parent(p1, m1)" in rendered
    # Check inferred fields in child constructor
    assert "p1: U256  // required by Parent" in rendered
    assert "mut m1: Address  // required by Parent" in rendered
    assert "c1: Bool" in rendered

def test_ralph_source_render_complex():
    source = RalphSource()
    
    # Structs and Enums
    source.global_structs.append(Struct(name="MyStruct", fields=[Field(name="a", type="U256")]))
    source.global_enums.append(RalphEnum(name="MyEnum", values=[EnumValue(name="Val1", value=0)]))
    
    # Interface
    iface = Interface(name="IFace", parents=["IOther"], public_methods="fn foo() -> ()")
    source.interfaces["IFace"] = iface
    
    # Contract with Map and Event
    contract = Contract(
        name="Complex",
        abstract=False,
        maps={"balances": MapDef(key_type="Address", value_type="U256")},
        events=[RalphEvent(name="Transfer", fields=[Field(name="from", type="Address"), Field(name="to", type="Address")])]
    )
    source.contracts["Complex"] = contract
    
    rendered = source.render()
    assert "struct MyStruct {" in rendered
    assert "enum MyEnum {" in rendered
    assert "Interface IFace extends IOther {" in rendered
    assert "mapping[Address, U256] balances" in rendered
    assert "event Transfer(from: Address, to: Address)" in rendered
