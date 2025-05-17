"""
FastAPI service for minting DALL-E NFTs on the blockchain.
"""

import os
import json
import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import the necessary components from the langchain-eth-account-chatbot
from coinbase_agentkit.action_providers.erc721.erc721_action_provider import Erc721ActionProvider
from coinbase_agentkit.wallet_providers.eth_account_wallet_provider import EthAccountWalletProvider
from coinbase_agentkit.network import Network

# Create the FastAPI app
app = FastAPI(
    title="DALL-E NFT API",
    description="API for generating DALL-E images and minting them as NFTs",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Store minting tasks and their status
minting_tasks = {}

# Initialize the wallet provider
def get_wallet_provider():
    """Initialize and return the wallet provider."""
    # Load wallet data from file or create a new one
    wallet_data_file = "wallet_data_84532.txt"
    
    if os.path.exists(wallet_data_file):
        with open(wallet_data_file, "r") as f:
            wallet_data = json.load(f)
        print("Loading existing wallet from wallet_data_84532.txt")
    else:
        # Create a new wallet
        wallet_data = {
            "private_key": EthAccountWalletProvider.generate_private_key().hex(),
            "chain_id": 84532,  # Base Sepolia
        }
        with open(wallet_data_file, "w") as f:
            json.dump(wallet_data, f)
        print("Created new wallet and saved to wallet_data_84532.txt")
    
    # Create the wallet provider
    network = Network(
        name="Base Sepolia",
        protocol_family="evm",
        chain_id=wallet_data["chain_id"],
        rpc_url="https://sepolia.base.org",
        explorer_url="https://sepolia.basescan.org/",
    )
    
    wallet_provider = EthAccountWalletProvider(
        private_key=wallet_data["private_key"],
        network=network,
    )
    
    # Save wallet data
    with open(wallet_data_file, "w") as f:
        json.dump(wallet_data, f)
    print(f"Wallet data saved to {wallet_data_file}")
    
    return wallet_provider

# Request model
class MintNFTRequest(BaseModel):
    """Request model for minting a DALL-E NFT."""
    prompt: str
    destination: str
    nft_name: Optional[str] = None
    contract_address: Optional[str] = None

# Response models
class MintNFTResponse(BaseModel):
    """Response model for the mint NFT endpoint."""
    task_id: str
    status: str
    message: str

class NFTStatusResponse(BaseModel):
    """Response model for the NFT status endpoint."""
    task_id: str
    status: str
    message: str
    opensea_url: Optional[str] = None
    image_url: Optional[str] = None
    ipfs_url: Optional[str] = None
    transaction_hash: Optional[str] = None
    transaction_url: Optional[str] = None

# Background task for minting NFTs
def mint_dalle_nft_task(task_id: str, prompt: str, destination: str, nft_name: Optional[str] = None, contract_address: Optional[str] = None):
    """Background task for minting a DALL-E NFT."""
    try:
        # Update task status
        minting_tasks[task_id]["status"] = "processing"
        minting_tasks[task_id]["message"] = "Generating DALL-E image and minting NFT..."
        
        # Get wallet provider
        wallet_provider = get_wallet_provider()
        
        # Create action provider
        action_provider = Erc721ActionProvider()
        
        # Prepare arguments
        args = {
            "prompt": prompt,
            "destination": destination,
        }
        
        if nft_name:
            args["nft_name"] = nft_name
            
        if contract_address:
            args["contract_address"] = contract_address
        
        # Call the dalle_nft action
        result = action_provider.dalle_nft(wallet_provider, args)
        
        # Parse the result
        opensea_url = None
        image_url = None
        ipfs_url = None
        transaction_hash = None
        transaction_url = None
        
        for line in result.split("\n"):
            if "DALL-E Image URL:" in line:
                image_url = line.split("DALL-E Image URL:")[1].strip()
            elif "IPFS Image URL:" in line:
                ipfs_url = line.split("IPFS Image URL:")[1].strip()
            elif "Transaction Hash:" in line:
                transaction_hash = line.split("Transaction Hash:")[1].strip()
            elif "Transaction URL:" in line:
                transaction_url = line.split("Transaction URL:")[1].strip()
            elif "View on OpenSea" in line:
                opensea_url = line.split(":")[1].strip()
        
        # Update task status
        minting_tasks[task_id]["status"] = "completed"
        minting_tasks[task_id]["message"] = "NFT minted successfully!"
        minting_tasks[task_id]["opensea_url"] = opensea_url
        minting_tasks[task_id]["image_url"] = image_url
        minting_tasks[task_id]["ipfs_url"] = ipfs_url
        minting_tasks[task_id]["transaction_hash"] = transaction_hash
        minting_tasks[task_id]["transaction_url"] = transaction_url
        
    except Exception as e:
        # Update task status with error
        minting_tasks[task_id]["status"] = "failed"
        minting_tasks[task_id]["message"] = f"Error minting NFT: {str(e)}"

# API endpoints
@app.post("/mint-dalle-nft", response_model=MintNFTResponse)
async def mint_dalle_nft(request: MintNFTRequest, background_tasks: BackgroundTasks):
    """
    Mint a DALL-E NFT with the given prompt and destination address.
    
    - **prompt**: Text prompt for DALL-E image generation
    - **destination**: Destination address to mint the NFT to
    - **nft_name**: (Optional) Name for this specific NFT
    - **contract_address**: (Optional) Existing NFT contract address
    
    Returns a task ID that can be used to check the status of the minting process.
    """
    # Generate a task ID
    task_id = str(uuid.uuid4())
    
    # Initialize task status
    minting_tasks[task_id] = {
        "status": "queued",
        "message": "Task queued for processing",
        "opensea_url": None,
        "image_url": None,
        "ipfs_url": None,
        "transaction_hash": None,
        "transaction_url": None,
    }
    
    # Add task to background tasks
    background_tasks.add_task(
        mint_dalle_nft_task,
        task_id=task_id,
        prompt=request.prompt,
        destination=request.destination,
        nft_name=request.nft_name,
        contract_address=request.contract_address,
    )
    
    return MintNFTResponse(
        task_id=task_id,
        status="queued",
        message="Task queued for processing",
    )

@app.get("/nft-status/{task_id}", response_model=NFTStatusResponse)
async def get_nft_status(task_id: str):
    """
    Get the status of a DALL-E NFT minting task.
    
    - **task_id**: The ID of the minting task
    
    Returns the status of the minting task and, if completed, the OpenSea URL.
    """
    if task_id not in minting_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = minting_tasks[task_id]
    
    return NFTStatusResponse(
        task_id=task_id,
        status=task["status"],
        message=task["message"],
        opensea_url=task["opensea_url"],
        image_url=task["image_url"],
        ipfs_url=task["ipfs_url"],
        transaction_hash=task["transaction_hash"],
        transaction_url=task["transaction_url"],
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
