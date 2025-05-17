"""Schemas for ERC721 action provider."""

from pydantic import BaseModel, Field
from typing import Optional


class GetBalanceSchema(BaseModel):
    """Input schema for get NFT (ERC721) balance action."""

    contract_address: str = Field(description="The NFT contract address to check balance for")
    address: str | None = Field(
        None,
        description="The address to check NFT balance for. If not provided, uses the wallet's default address",
    )


class MintSchema(BaseModel):
    """Input schema for mint NFT (ERC721) action."""

    contract_address: str = Field(description="The contract address of the NFT to mint")
    destination: str = Field(
        description="The onchain destination address that will receive the NFT"
    )


class TransferSchema(BaseModel):
    """Input schema for NFT (ERC721) transfer action."""

    contract_address: str = Field(description="The NFT contract address to interact with")
    token_id: str = Field(description="The ID of the NFT to transfer")
    destination: str = Field(
        description=(
            "The destination to transfer the NFT, e.g. `0x58dBecc0894Ab4C24F98a0e684c989eD07e4e027`, "
            "`example.eth`, `example.base.eth`"
        )
    )
    from_address: str | None = Field(
        None,
        description="The address to transfer from. If not provided, defaults to the wallet's default address",
    )


class DalleNftSchema(BaseModel):
    """Input schema for DALL-E NFT generation and minting."""

    prompt: str = Field(
        description="Text prompt for DALL-E image generation",
        example="A majestic dragon soaring through a cyberpunk city",
    )
    destination: str = Field(
        description="Destination address to mint the NFT to",
        example="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    )
    nft_name: Optional[str] = Field(
        None,
        description="Optional: Name for this specific NFT",
        example="Dragon #1",
    )
    contract_address: Optional[str] = Field(
        None,
        description="Optional: Existing NFT contract address. If not provided, a new collection will be deployed",
    )
    collection_name: Optional[str] = Field(
        None,
        description="Required if contract_address is not provided: Name of the NFT collection",
        example="Xoxo NFT Collection",
    )
    collection_symbol: Optional[str] = Field(
        None,
        description="Required if contract_address is not provided: Symbol of the NFT collection",
        example="XOXO",
    )
