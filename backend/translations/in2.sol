// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

interface IStack {
  event Popped(uint256 value);
  event Pushed(uint256 value);

  function push(uint256 value) external;
  function pop() external;
}

contract Array is IStack {
  // Several ways to initialize an array
  uint256[] public arr;
  uint256[] public arr2 = [1, 2, 3];
  // Fixed sized array, all elements initialize to 0
  uint256[10] public myFixedSizeArr;

  function setFixed(uint256 index, uint256 value) public {
    // Set value at index in fixed size array
    myFixedSizeArr[index] = value;
  }

  function get(uint256 i) public view returns (uint256) {
    return arr[i];
  }

  // Solidity can return the entire array.
  function getArr() public view returns (uint256[] memory) {
    return arr;
  }

  function push(uint256 i) public {
    // Append to array
    // This will increase the array length by 1.
    arr.push(i);
  }

  function push2(uint256 i) external {
    emit Pushed(i);
    arr2.push(i);
  }

  function pop() external {
    // Remove last element from array
    // This will decrease the array length by 1
    // This will revert if the array is empty
    arr.pop();
  }

  function getLength() public view returns (uint256) {
    return arr.length;
  }

  function remove(uint256 index) public {
    // Delete does not change the array length.
    // It resets the value at index to it's default value,
    // in this case 0
    delete arr[index];
  }

  function examples() external pure returns (uint256) {
    // create array in memory, only fixed size can be created
    uint256[] memory a = new uint256[](5);

    // create a nested array in memory
    // b = [[1, 2, 3], [4, 5, 6]]
    uint256[][] memory b = new uint256[][](2);
    for (uint256 i = 0; i < b.length; i++) {
      b[i] = new uint256[](3);
    }
    b[0][0] = 1;
    b[0][1] = 2;
    b[0][2] = 3;
    b[1][0] = 4;
    b[1][1] = 5;
    b[1][2] = 6;

    return a[0] + b[0][0];
  }
}