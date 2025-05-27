// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ContractWithList {
  struct Todo {
    string text;
    bool completed;
  }

  Todo[] public todos;

  function create(string memory _text) public {
    todos.push(Todo(_text, false));
  }

  function get(uint256 _index) public view returns (Todo memory) {
    return todos[_index];
  }
}
