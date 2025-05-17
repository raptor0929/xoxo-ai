// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title XoxoNFT
 * @dev A dynamic NFT collection where each token has its own unique metadata URI
 * This allows for individual DALL-E generated images per NFT
 */
contract XoxoNFT is ERC721URIStorage, Ownable {
    // Token ID counter - using a simple uint256 instead of Counters
    uint256 private _nextTokenId;
    
    // Events
    event NFTMinted(address indexed to, uint256 indexed tokenId, string tokenURI);
    
    // Constructor
    constructor() ERC721("Xoxo NFT Collection", "XOXO") Ownable(msg.sender) {}
    
    /**
     * @dev Mint a new NFT with a specific tokenURI
     * @param to The address that will receive the minted token
     * @param tokenURI The token URI containing metadata for this specific NFT
     * @return The ID of the newly minted token
     */
    function mint(address to, string memory tokenURI) public onlyOwner returns (uint256) {
        // Get the current token ID
        uint256 tokenId = _nextTokenId;
        
        // Increment the counter for the next mint
        unchecked {
            _nextTokenId++;
        }
        
        // Mint the token to the specified address
        _safeMint(to, tokenId);
        
        // Set the token URI (metadata)
        _setTokenURI(tokenId, tokenURI);
        
        // Emit event
        emit NFTMinted(to, tokenId, tokenURI);
        
        return tokenId;
    }
    
    /**
     * @dev Simple mint function that only takes a recipient address
     * This is for compatibility with existing mint function signatures
     * Note: This will mint a token without metadata, which should be set later
     * @param to The address that will receive the minted token
     * @return The ID of the newly minted token
     */
    function mint(address to) public onlyOwner returns (uint256) {
        // Get the current token ID
        uint256 tokenId = _nextTokenId;
        
        // Increment the counter for the next mint
        unchecked {
            _nextTokenId++;
        }
        
        // Mint the token to the specified address
        _safeMint(to, tokenId);
        
        // Emit event with empty tokenURI
        emit NFTMinted(to, tokenId, "");
        
        return tokenId;
    }
    
    /**
     * @dev Set the token URI for an existing token
     * This is useful for updating metadata after minting
     * @param tokenId The ID of the token to update
     * @param tokenURI The new token URI
     */
    function setTokenURI(uint256 tokenId, string memory tokenURI) public onlyOwner {
        _setTokenURI(tokenId, tokenURI);
    }
    
    /**
     * @dev Get the total number of tokens minted
     * @return The total supply of tokens
     */
    function totalSupply() public view returns (uint256) {
        return _nextTokenId;
    }
}
