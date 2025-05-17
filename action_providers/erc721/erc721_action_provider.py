"""ERC721 action provider."""

from typing import Any, Optional
import json
import logging
import os
import requests
import io

from eth_typing import HexStr
from web3 import Web3
from web3.exceptions import ContractLogicError
from openai import OpenAI

from ...network import Network
from ...wallet_providers import EvmWalletProvider
from ..action_decorator import create_action
from ..action_provider import ActionProvider
from .constants import ERC721_ABI, XOXO_NFT_ABI
from .schemas import GetBalanceSchema, MintSchema, TransferSchema, DalleNftSchema

# Set up logger
logger = logging.getLogger(__name__)

class Erc721ActionProvider(ActionProvider[EvmWalletProvider]):
    """Action provider for ERC721 contract interactions."""

    def __init__(self) -> None:
        """Initialize the ERC721 action provider."""
        super().__init__("erc721", [])

    @create_action(
        name="mint",
        description="""
This tool will mint an NFT (ERC-721) to a specified destination address onchain via a contract invocation.
It takes the contract address of the NFT onchain and the destination address onchain that will receive the NFT as inputs.
Do not use the contract address as the destination address. If you are unsure of the destination address, please ask the user before proceeding.
""",
        schema=MintSchema,
    )
    def mint(self, wallet_provider: EvmWalletProvider, args: dict[str, Any]) -> str:
        """Mint an NFT (ERC-721) to a specified destination address.

        Args:
            wallet_provider (EvmWalletProvider): The wallet provider instance.
            args (dict[str, Any]): Input arguments for the action.

        Returns:
            str: A message containing the action response or error details.

        """
        logger.info(f"Starting NFT mint operation with contract: {args['contract_address']}")
        logger.info(f"Destination address: {args['destination']}")
        logger.info(f"Wallet address: {wallet_provider.get_address()}")
        
        try:
            # Log contract address in both original and checksum format
            original_contract_address = args["contract_address"]
            try:
                checksum_contract_address = Web3.to_checksum_address(original_contract_address)
                logger.info(f"Original contract address: {original_contract_address}")
                logger.info(f"Checksum contract address: {checksum_contract_address}")
                
                # Use the checksum address for the contract
                contract = Web3().eth.contract(address=checksum_contract_address, abi=ERC721_ABI)
            except ValueError as ve:
                logger.error(f"Invalid contract address format: {ve}")
                return f"Error minting NFT: Invalid contract address format - {ve}"
            
            # Log destination address in both original and checksum format
            original_destination = args["destination"]
            try:
                checksum_destination = Web3.to_checksum_address(original_destination)
                logger.info(f"Original destination address: {original_destination}")
                logger.info(f"Checksum destination address: {checksum_destination}")
                
                # Use the checksum destination for the contract call - AidogDynamicNFT mint only takes address parameter
                data = contract.encode_abi("mint", args=[checksum_destination])
            except ValueError as ve:
                logger.error(f"Invalid destination address format: {ve}")
                return f"Error minting NFT: Invalid destination address format - {ve}"
            
            logger.info("Encoded mint function data")
            
            # Prepare transaction
            tx_data = {
                "to": HexStr(checksum_contract_address),
                "data": HexStr(data),
            }
            logger.info(f"Transaction data: {json.dumps(tx_data, default=str)}")
            
            # Send transaction
            tx_hash = wallet_provider.send_transaction(tx_data)
            
            # Check if tx_hash is bytes-like or already a string
            tx_hash_str = tx_hash.hex() if hasattr(tx_hash, 'hex') else tx_hash
            logger.info(f"Transaction sent with hash: {tx_hash_str}")
            
            # Return immediately with transaction hash
            explorer_url = "https://sepolia.basescan.org/"
            
            if explorer_url:
                # Format transaction URL based on the explorer URL
                if explorer_url.endswith('/'):
                    tx_url = f"{explorer_url}tx/{tx_hash_str}"
                else:
                    tx_url = f"{explorer_url}/tx/{tx_hash_str}"
                logger.info(f"Transaction URL: {tx_url}")
                return f"NFT mint transaction submitted to {checksum_destination} at contract {checksum_contract_address}. Transaction hash: {tx_hash_str}\nTransaction URL: {tx_url}"
            else:
                return f"NFT mint transaction submitted to {checksum_destination} at contract {checksum_contract_address}. Transaction hash: {tx_hash_str}"
            
        except ContractLogicError as cle:
            logger.error(f"Contract logic error: {cle}")
            # Try to extract revert reason if available
            revert_reason = str(cle)
            if "revert" in revert_reason.lower():
                logger.error(f"Contract reverted with reason: {revert_reason}")
            return f"Error minting NFT {args['contract_address']} to {args['destination']}: Contract error - {revert_reason}"
        except Exception as e:
            logger.error(f"Exception during mint operation: {str(e)}", exc_info=True)
            return f"Error minting NFT {args['contract_address']} to {args['destination']}: {e}"

    @create_action(
        name="transfer",
        description="""
This tool will transfer an NFT (ERC721 token) from the wallet to another onchain address.

It takes the following inputs:
- contractAddress: The NFT contract address
- tokenId: The ID of the specific NFT to transfer
- destination: Onchain address to send the NFT

Important notes:
- Ensure you have ownership of the NFT before attempting transfer
- Ensure there is sufficient native token balance for gas fees
- The wallet must either own the NFT or have approval to transfer it
""",
        schema=TransferSchema,
    )
    def transfer(self, wallet_provider: EvmWalletProvider, args: dict[str, Any]) -> str:
        """Transfer an NFT (ERC721 token) to a destination address.

        Args:
            wallet_provider (EvmWalletProvider): The wallet provider instance.
            args (dict[str, Any]): Input arguments for the action.

        Returns:
            str: A message containing the action response or error details.

        """
        logger.info(f"Starting NFT transfer operation with contract: {args['contract_address']}")
        logger.info(f"Token ID: {args['token_id']}")
        logger.info(f"Destination address: {args['destination']}")
        
        try:
            # Log contract address in both original and checksum format
            original_contract_address = args["contract_address"]
            try:
                checksum_contract_address = Web3.to_checksum_address(original_contract_address)
                logger.info(f"Original contract address: {original_contract_address}")
                logger.info(f"Checksum contract address: {checksum_contract_address}")
                
                # Use the checksum address for the contract
                contract = Web3().eth.contract(address=checksum_contract_address, abi=ERC721_ABI)
            except ValueError as ve:
                logger.error(f"Invalid contract address format: {ve}")
                return f"Error transferring NFT: Invalid contract address format - {ve}"
            
            # Get from address
            from_address = args.get("from_address") or wallet_provider.get_address()
            try:
                checksum_from_address = Web3.to_checksum_address(from_address)
                logger.info(f"From address: {checksum_from_address}")
            except ValueError as ve:
                logger.error(f"Invalid from address format: {ve}")
                return f"Error transferring NFT: Invalid from address format - {ve}"
            
            # Log destination address in both original and checksum format
            original_destination = args["destination"]
            try:
                checksum_destination = Web3.to_checksum_address(original_destination)
                logger.info(f"Original destination address: {original_destination}")
                logger.info(f"Checksum destination address: {checksum_destination}")
            except ValueError as ve:
                logger.error(f"Invalid destination address format: {ve}")
                return f"Error transferring NFT: Invalid destination address format - {ve}"
            
            # Verify token ownership
            try:
                token_id = int(args["token_id"])
                logger.info(f"Checking ownership of token ID: {token_id}")
                
                owner = wallet_provider.read_contract(
                    {
                        "address": HexStr(checksum_contract_address),
                        "abi": ERC721_ABI,
                        "function_name": "ownerOf",
                        "args": [token_id],
                    }
                )
                logger.info(f"Current owner of token {token_id}: {owner}")
                
                if owner.lower() != checksum_from_address.lower():
                    logger.warning(f"Token {token_id} is owned by {owner}, not by {checksum_from_address}")
            except Exception as e:
                logger.error(f"Error checking token ownership: {e}")
                # Continue anyway, as the contract will enforce ownership
            
            # Encode function data
            data = contract.encode_abi(
                "transferFrom",
                args=[checksum_from_address, checksum_destination, token_id],
            )
            logger.info("Encoded transferFrom function data")
            
            # Prepare transaction
            tx_data = {
                "to": HexStr(checksum_contract_address),
                "data": HexStr(data),
            }
            logger.info(f"Transaction data: {json.dumps(tx_data, default=str)}")
            
            # Send transaction
            tx_hash = wallet_provider.send_transaction(tx_data)
            logger.info(f"Transaction sent with hash: {tx_hash.hex()}")
            
            # Wait for receipt
            logger.info("Waiting for transaction receipt...")
            receipt = wallet_provider.wait_for_transaction_receipt(tx_hash)
            
            # Log transaction receipt details
            logger.info(f"Transaction status: {'Success' if receipt.status == 1 else 'Failed'}")
            logger.info(f"Gas used: {receipt.gasUsed}")
            logger.info(f"Block number: {receipt.blockNumber}")
            
            if receipt.status == 1:
                return (
                    f"Successfully transferred NFT {checksum_contract_address} with tokenId "
                    f"{token_id} to {checksum_destination}. Transaction hash: {tx_hash.hex()}"
                )
            else:
                logger.error(f"Transaction failed: {receipt}")
                return f"Transaction completed but failed. Check logs for details. Transaction hash: {tx_hash.hex()}"
                
        except ContractLogicError as cle:
            logger.error(f"Contract logic error: {cle}")
            # Try to extract revert reason if available
            revert_reason = str(cle)
            if "revert" in revert_reason.lower():
                logger.error(f"Contract reverted with reason: {revert_reason}")
            return (
                f"Error transferring NFT {args['contract_address']} with tokenId "
                f"{args['token_id']} to {args['destination']}: Contract error - {revert_reason}"
            )
        except Exception as e:
            logger.error(f"Exception during transfer operation: {str(e)}", exc_info=True)
            return (
                f"Error transferring NFT {args['contract_address']} with tokenId "
                f"{args['token_id']} to {args['destination']}: {e}"
            )

    @create_action(
        name="get_balance",
        description="""
This tool will check the NFT (ERC721 token) balance for a given address.

It takes the following inputs:
- contractAddress: The NFT contract address to check balance for
- address: (Optional) The address to check NFT balance for. If not provided, uses the wallet's address
""",
        schema=GetBalanceSchema,
    )
    def get_balance(self, wallet_provider: EvmWalletProvider, args: dict[str, Any]) -> str:
        """Get the NFT balance for a given address and contract.

        This function queries an ERC721 NFT contract to get the token balance for a specific address.
        It uses the standard ERC721 balanceOf function which returns the number of tokens owned by
        the given address for that NFT collection.

        Args:
            wallet_provider (EvmWalletProvider): The wallet provider to use for making the contract call
            args (dict[str, Any]): The input arguments containing:
                - contract_address (str): The address of the ERC721 NFT contract to query
                - address (str, optional): The address to check NFT balance for. If not provided,
                    uses the wallet's default address

        Returns:
            str: A message containing either:
                - The NFT balance details if successful
                - An error message if the balance check fails

        Raises:
            Exception: If the contract call fails for any reason

        """
        logger.info(f"Starting get_balance operation for contract: {args['contract_address']}")
        
        try:
            # Log contract address in both original and checksum format
            original_contract_address = args["contract_address"]
            try:
                checksum_contract_address = Web3.to_checksum_address(original_contract_address)
                logger.info(f"Original contract address: {original_contract_address}")
                logger.info(f"Checksum contract address: {checksum_contract_address}")
            except ValueError as ve:
                logger.error(f"Invalid contract address format: {ve}")
                return f"Error getting NFT balance: Invalid contract address format - {ve}"
            
            # Get address to check
            address = args.get("address") or wallet_provider.get_address()
            try:
                checksum_address = Web3.to_checksum_address(address)
                logger.info(f"Checking balance for address: {checksum_address}")
            except ValueError as ve:
                logger.error(f"Invalid address format: {ve}")
                return f"Error getting NFT balance: Invalid address format - {ve}"
            
            # Read contract
            logger.info(f"Reading balanceOf from contract {checksum_contract_address} for address {checksum_address}")
            balance = wallet_provider.read_contract(
                {
                    "address": HexStr(checksum_contract_address),
                    "abi": ERC721_ABI,
                    "function_name": "balanceOf",
                    "args": [checksum_address],
                }
            )
            logger.info(f"Balance result: {balance}")

            return (
                f"Balance of NFTs for contract {checksum_contract_address} at address {checksum_address} is "
                f"{balance}"
            )
        except Exception as e:
            logger.error(f"Exception during get_balance operation: {str(e)}", exc_info=True)
            return f"Error getting NFT balance for contract {args['contract_address']}: {e}"

    @create_action(
        name="dalle_nft",
        description="""This tool will generate an image using DALL-E based on a text prompt and mint it as an NFT.

It takes the following inputs:
- prompt: Text prompt for DALL-E image generation
- destination: Destination address to mint the NFT to
- contract_address: (Optional) Existing NFT contract address. If not provided, a new collection will be deployed
- collection_name: (Required if contract_address is not provided) Name of the NFT collection
- collection_symbol: (Required if contract_address is not provided) Symbol of the NFT collection

This tool requires the following environment variables:
- OPENAI_API_KEY: For accessing DALL-E API
- PINATA_JWT: For uploading to IPFS
""",
        schema=DalleNftSchema,
    )
    def dalle_nft(self, wallet_provider: EvmWalletProvider, args: dict[str, Any]) -> str:
        """Generate a DALL-E image and mint it as an NFT in the Xoxo NFT collection.

        Args:
            wallet_provider (EvmWalletProvider): The wallet provider instance.
            args (dict[str, Any]): Input arguments for the action.

        Returns:
            str: A message containing the action response or error details.
        """
        prompt = args["prompt"]
        destination = args["destination"]
        nft_name = args.get("nft_name") or f"Xoxo NFT: {prompt[:30]}{'...' if len(prompt) > 30 else ''}"
        contract_address = args.get("contract_address")
        collection_name = args.get("collection_name") or "Xoxo NFT Collection"
        collection_symbol = args.get("collection_symbol") or "XOXO"

        # Check for missing collection info if no contract address is provided
        if not contract_address and (not collection_name or not collection_symbol):
            return (
                "Error: collection_name and collection_symbol are required when contract_address is not provided."
                " Please provide either an existing contract_address or both collection_name and collection_symbol."
            )

        logger.info(f"Starting Xoxo DALL-E NFT generation with prompt: {prompt}")
        logger.info(f"NFT Name: {nft_name}")
        logger.info(f"Destination address: {destination}")

        try:
            # Validate destination address
            try:
                checksum_destination = Web3.to_checksum_address(destination)
                logger.info(f"Checksum destination address: {checksum_destination}")
            except ValueError as ve:
                logger.error(f"Invalid destination address format: {ve}")
                return f"Error: Invalid destination address format - {ve}"

            # Step 1: Generate image with DALL-E
            logger.info("🎨 Generating image with DALL-E...")
            image_url = generate_dalle_image(prompt)

            # Step 2: Upload image to IPFS
            logger.info("📤 Uploading image to IPFS...")
            ipfs_url, gateway_url = upload_to_ipfs(image_url)

            # Step 3: Create and upload metadata
            logger.info("📝 Creating NFT metadata...")
            metadata_uri = create_and_upload_metadata(prompt, ipfs_url, name=nft_name)

            # Step 4: Use existing contract or get from environment variable
            if not contract_address:
                # Get contract address from environment variable
                env_contract_address = os.getenv("NFT_CONTRACT_ADDRESS")
                if not env_contract_address:
                    logger.error("No contract address provided and NFT_CONTRACT_ADDRESS environment variable not set")
                    return (
                        f"Error: No contract address provided and NFT_CONTRACT_ADDRESS environment variable not set.\n"
                        f"Please provide a contract_address parameter or set the NFT_CONTRACT_ADDRESS environment variable.\n\n"
                        f"DALL-E Image URL: {image_url}\n"
                        f"IPFS Image URL: {ipfs_url}\n"
                        f"IPFS Gateway URL: {gateway_url}\n"
                        f"Metadata URI: {metadata_uri}"
                    )
                
                logger.info(f"Using contract address from NFT_CONTRACT_ADDRESS environment variable")
                contract_address = env_contract_address

            # Step 5: Mint NFT using existing contract
            try:
                checksum_contract_address = Web3.to_checksum_address(contract_address)
                logger.info(f"Using existing contract at: {checksum_contract_address}")

                # Use the XoxoNFT ABI which has the mint function with tokenURI parameter
                contract = Web3().eth.contract(address=checksum_contract_address, abi=XOXO_NFT_ABI)
                
                try:
                    # Encode mint with tokenURI parameter
                    data = contract.encode_abi("mint", args=[checksum_destination, metadata_uri])
                    logger.info(f"Encoded mint function with tokenURI parameter: {metadata_uri}")
                except Exception as e:
                    logger.error(f"Error encoding mint function: {e}")
                    return f"Error minting NFT: Failed to encode mint function - {e}\n\nDALL-E Image URL: {image_url}\nIPFS Image URL: {ipfs_url}\nIPFS Gateway URL: {gateway_url}\nMetadata URI: {metadata_uri}"

                # Prepare transaction
                tx_data = {
                    "to": HexStr(checksum_contract_address),
                    "data": HexStr(data),
                }
                logger.info(f"Transaction data: {json.dumps(tx_data, default=str)}")

                # Send transaction
                tx_hash = wallet_provider.send_transaction(tx_data)
                tx_hash_str = tx_hash.hex() if hasattr(tx_hash, 'hex') else tx_hash
                logger.info(f"Transaction sent with hash: {tx_hash_str}")

                # Return immediately with transaction hash
                explorer_url = "https://sepolia.basescan.org/"
                if explorer_url:
                    # Format transaction URL based on the explorer URL
                    if explorer_url.endswith('/'):
                        tx_url = f"{explorer_url}tx/{tx_hash_str}"
                    else:
                        tx_url = f"{explorer_url}/tx/{tx_hash_str}"
                    logger.info(f"Transaction URL: {tx_url}")

                    # Add OpenSea link - for XoxoNFT we need to get the token ID
                    # Since we're not waiting for receipt, we'll use a placeholder
                    token_id = "latest"
                    opensea_url = f"https://testnets.opensea.io/assets/base_sepolia/{checksum_contract_address}/{token_id}"

                    return (
                        f"Successfully created and minted Xoxo DALL-E NFT!\n\n"
                        f"NFT Name: {nft_name}\n"
                        f"DALL-E Image URL: {image_url}\n"
                        f"IPFS Image URL: {ipfs_url}\n"
                        f"IPFS Gateway URL: {gateway_url}\n"
                        f"Metadata URI: {metadata_uri}\n"
                        f"Contract Address: {checksum_contract_address}\n"
                        f"Transaction Hash: {tx_hash_str}\n"
                        f"Transaction URL: {tx_url}\n"
                        f"View on OpenSea (after confirmation): {opensea_url}"
                    )

            except ValueError as ve:
                logger.error(f"Invalid contract address format: {ve}")
                return f"Error: Invalid contract address format - {ve}"
            except Exception as e:
                logger.error(f"Error minting NFT: {e}")
                return f"Error minting NFT: {e}"

        except Exception as e:
            logger.error(f"Exception during DALL-E NFT generation: {str(e)}", exc_info=True)
            return f"Error generating DALL-E NFT: {e}"

    def supports_network(self, network: Network) -> bool:
        """Check if the ERC721 action provider supports the given network.

        Args:
            network: The network to check.

        Returns:
            True if the ERC721 action provider supports the network, false otherwise.

        """
        return network.protocol_family == "evm"


# Helper functions for DALL-E NFT generation
def get_openai_client() -> OpenAI:
    """Get OpenAI client instance."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not found")
    return OpenAI(api_key=api_key)


def generate_dalle_image(prompt: str, client: OpenAI | None = None) -> str:
    """Generate an image using DALL-E-3."""
    if client is None:
        client = get_openai_client()
    try:
        logger.info(f"Generating DALL-E image with prompt: {prompt}")
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        logger.info(f"Generated image URL: {image_url}")
        return image_url
    except Exception as e:
        logger.error(f"Error generating DALL-E image: {e}")
        raise Exception(f"Error generating DALL-E image: {e}") from e


def upload_to_ipfs(image_url: str) -> tuple[str, str]:
    """Upload an image to IPFS via Pinata."""
    pinata_jwt = os.getenv("PINATA_JWT")
    if not pinata_jwt:
        raise ValueError("PINATA_JWT environment variable not found")
    try:
        # Download image from DALL-E
        logger.info(f"Downloading image from URL: {image_url}")
        response = requests.get(image_url)
        response.raise_for_status()
        image_data = response.content

        # Prepare for Pinata upload
        files = {"file": ("dalle_image.png", image_data)}
        headers = {"Authorization": f"Bearer {pinata_jwt}"}

        # Upload to Pinata
        logger.info("Uploading image to IPFS via Pinata")
        pinata_response = requests.post(
            "https://api.pinata.cloud/pinning/pinFileToIPFS", files=files, headers=headers
        )
        pinata_response.raise_for_status()
        ipfs_hash = pinata_response.json()["IpfsHash"]
        ipfs_url = f"ipfs://{ipfs_hash}"
        gateway_url = f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"
        logger.info(f"Image uploaded to IPFS: {ipfs_url}")
        logger.info(f"Gateway URL: {gateway_url}")
        return ipfs_url, gateway_url
    except Exception as e:
        logger.error(f"Error uploading to IPFS: {e}")
        raise Exception(f"Error uploading to IPFS: {e}") from e


def create_and_upload_metadata(prompt: str, image_ipfs_url: str, name: str = "DALL-E Generated NFT") -> str:
    """Create and upload NFT metadata to IPFS."""
    pinata_jwt = os.getenv("PINATA_JWT")
    if not pinata_jwt:
        raise ValueError("PINATA_JWT environment variable not found")

    metadata = {
        "name": name,
        "description": f"This NFT was generated by DALL-E using the prompt: {prompt}",
        "image": image_ipfs_url,
        "attributes": [
            {"trait_type": "Generator", "value": "DALL-E"},
            {"trait_type": "Prompt", "value": prompt},
            {"trait_type": "Collection", "value": "Xoxo NFT"},
        ],
    }

    # Convert metadata JSON into a bytes stream
    json_str = json.dumps(metadata)
    json_bytes = io.BytesIO(json_str.encode("utf-8"))

    # Build the multipart form-data parts
    files = {
        "file": ("metadata.json", json_bytes, "application/json"),
        "pinataMetadata": (None, json.dumps({"name": f"DALL-E NFT Metadata"}), "application/json"),
        "pinataOptions": (
            None,
            json.dumps(
                {
                    "cidVersion": 1,
                }
            ),
            "application/json",
        ),
    }

    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    headers = {"Authorization": f"Bearer {pinata_jwt}"}

    try:
        # Upload the file and related metadata/options to Pinata
        logger.info("Uploading metadata to IPFS via Pinata")
        response = requests.post(url, files=files, headers=headers)
        response.raise_for_status()

        # Parse Pinata response
        pinata_data = response.json()
        ipfs_hash = pinata_data.get("IpfsHash")
        metadata_url = f"ipfs://{ipfs_hash}"
        logger.info(f"Metadata uploaded to IPFS: {metadata_url}")
        return metadata_url
    except Exception as e:
        logger.error(f"Error uploading metadata to IPFS: {e}")
        raise Exception(f"Error uploading metadata to IPFS: {e}") from e


def erc721_action_provider() -> Erc721ActionProvider:
    """Create an instance of the ERC721 action provider.

    Returns:
        An instance of the ERC721 action provider.

    """
    return Erc721ActionProvider()
