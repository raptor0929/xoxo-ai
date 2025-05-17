// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/XoxoNFT.sol";

/**
 * @title XoxoNFTDeployScript
 * @dev Script to deploy the XoxoNFT contract
 */
contract XoxoNFTDeployScript is Script {
    function setUp() public {}

    function run() public {
        // Get the private key from the environment variable
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        // Start broadcasting transactions
        vm.startBroadcast(deployerPrivateKey);
        
        // Deploy the XoxoNFT contract
        XoxoNFT xoxoNFT = new XoxoNFT();
        
        // Log the deployed contract address
        console.log("XoxoNFT deployed at:", address(xoxoNFT));
        
        // Stop broadcasting transactions
        vm.stopBroadcast();
    }
}