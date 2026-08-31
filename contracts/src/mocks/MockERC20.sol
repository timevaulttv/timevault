// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

/// Test double for $TV. feeBps burns a slice on every transfer, which is how
/// the escrow's balance-delta accounting gets exercised: a token that takes a
/// cut in transit must not leave the contract owing more than it holds.
contract MockERC20 {
    string public name = "Mock Time Vault";
    string public symbol = "mTV";
    uint8 public constant decimals = 18;

    uint256 public totalSupply;
    uint16 public feeBps;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    constructor(uint16 feeBps_) {
        feeBps = feeBps_;
    }

    function setFee(uint16 feeBps_) external {
        feeBps = feeBps_;
    }

    function mint(address to, uint256 value) external {
        totalSupply += value;
        balanceOf[to] += value;
        emit Transfer(address(0), to, value);
    }

    function approve(address spender, uint256 value) external returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transfer(address to, uint256 value) external returns (bool) {
        _move(msg.sender, to, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) external returns (bool) {
        uint256 allowed = allowance[from][msg.sender];
        if (allowed != type(uint256).max) {
            require(allowed >= value, "allowance");
            allowance[from][msg.sender] = allowed - value;
        }
        _move(from, to, value);
        return true;
    }

    function _move(address from, address to, uint256 value) private {
        require(balanceOf[from] >= value, "balance");
        uint256 fee = (value * feeBps) / 10_000;
        balanceOf[from] -= value;
        balanceOf[to] += value - fee;
        totalSupply -= fee;
        emit Transfer(from, to, value - fee);
    }
}

/// Plenty of real tokens return nothing at all instead of a bool. The escrow
/// has to treat an empty return as success, and this is what proves it.
contract MockNoReturnERC20 {
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    function mint(address to, uint256 value) external {
        balanceOf[to] += value;
    }

    function approve(address spender, uint256 value) external {
        allowance[msg.sender][spender] = value;
    }

    function transfer(address to, uint256 value) external {
        require(balanceOf[msg.sender] >= value, "balance");
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
    }

    function transferFrom(address from, address to, uint256 value) external {
        require(allowance[from][msg.sender] >= value, "allowance");
        require(balanceOf[from] >= value, "balance");
        allowance[from][msg.sender] -= value;
        balanceOf[from] -= value;
        balanceOf[to] += value;
    }
}

/// Returns false rather than reverting. The escrow must refuse to record an
/// order it was never actually paid for.
contract MockFalseERC20 {
    function balanceOf(address) external pure returns (uint256) {
        return 0;
    }

    function transfer(address, uint256) external pure returns (bool) {
        return false;
    }

    function transferFrom(address, address, uint256) external pure returns (bool) {
        return false;
    }
}
