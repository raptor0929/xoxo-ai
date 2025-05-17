"""
Client script to demonstrate how to use the DALL-E NFT API.
"""

import requests
import json
import time
import argparse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def mint_dalle_nft(api_url, prompt, destination, nft_name=None, contract_address=None):
    """
    Mint a DALL-E NFT using the API.
    
    Args:
        api_url: The base URL of the API
        prompt: Text prompt for DALL-E image generation
        destination: Destination address to mint the NFT to
        nft_name: (Optional) Name for this specific NFT
        contract_address: (Optional) Existing NFT contract address
        
    Returns:
        The OpenSea URL of the minted NFT
    """
    # Prepare the request payload
    payload = {
        "prompt": prompt,
        "destination": destination,
    }
    
    if nft_name:
        payload["nft_name"] = nft_name
        
    if contract_address:
        payload["contract_address"] = contract_address
    
    # Make the request to mint the NFT
    print(f"Minting NFT with prompt: {prompt}")
    response = requests.post(f"{api_url}/mint-dalle-nft", json=payload)
    response.raise_for_status()
    
    # Get the task ID
    task_id = response.json()["task_id"]
    print(f"Task ID: {task_id}")
    
    # Poll for the status of the task
    print("Waiting for NFT to be minted...")
    while True:
        status_response = requests.get(f"{api_url}/nft-status/{task_id}")
        status_response.raise_for_status()
        
        status_data = status_response.json()
        status = status_data["status"]
        
        if status == "completed":
            print("NFT minted successfully!")
            print(f"OpenSea URL: {status_data['opensea_url']}")
            print(f"DALL-E Image URL: {status_data['image_url']}")
            print(f"IPFS URL: {status_data['ipfs_url']}")
            print(f"Transaction Hash: {status_data['transaction_hash']}")
            print(f"Transaction URL: {status_data['transaction_url']}")
            return status_data
        elif status == "failed":
            print(f"Error: {status_data['message']}")
            return None
        else:
            print(f"Status: {status} - {status_data['message']}")
            time.sleep(5)  # Wait for 5 seconds before checking again

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Mint a DALL-E NFT using the API")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--prompt", required=True, help="Text prompt for DALL-E image generation")
    parser.add_argument("--destination", required=True, help="Destination address to mint the NFT to")
    parser.add_argument("--nft-name", help="Name for this specific NFT")
    parser.add_argument("--contract-address", help="Existing NFT contract address")
    
    args = parser.parse_args()
    
    # Use environment variables as defaults if not provided
    contract_address = args.contract_address or os.getenv("NFT_CONTRACT_ADDRESS")
    
    # Mint the NFT
    mint_dalle_nft(
        api_url=args.api_url,
        prompt=args.prompt,
        destination=args.destination,
        nft_name=args.nft_name,
        contract_address=contract_address,
    )

if __name__ == "__main__":
    main()
