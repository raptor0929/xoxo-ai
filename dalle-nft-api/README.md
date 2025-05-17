# DALL-E NFT API

A FastAPI service for generating DALL-E images and minting them as NFTs on the blockchain.

## Features

- Generate images using DALL-E based on text prompts
- Upload images to IPFS via Pinata
- Mint NFTs with the generated images and metadata
- Asynchronous processing with background tasks
- Status tracking for minting tasks
- Simple client for interacting with the API

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
4. Edit the `.env` file with your API keys and contract address:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   PINATA_JWT=your_pinata_jwt_here
   NFT_CONTRACT_ADDRESS=your_contract_address_here
   ```

## Running the API

### Local Development

```bash
uvicorn main:app --reload
```

### Docker

```bash
# Build the Docker image
docker build -t dalle-nft-api .

# Run the Docker container
docker run -p 8000:8000 --env-file .env dalle-nft-api
```

## API Endpoints

### Mint DALL-E NFT

```
POST /mint-dalle-nft
```

Request body:
```json
{
  "prompt": "A pineapple character laying on the beach drinking caipirinha",
  "destination": "0x2656C60B79A3376beC507453978af5Ac73a8b5fC",
  "nft_name": "Beach Pineapple",
  "contract_address": "0xb944C6eAFb3b76FCF54aEE0d821b755dFBA17250"
}
```

Response:
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "queued",
  "message": "Task queued for processing"
}
```

### Check NFT Status

```
GET /nft-status/{task_id}
```

Response:
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "message": "NFT minted successfully!",
  "opensea_url": "https://testnets.opensea.io/assets/base_sepolia/0xb944C6eAFb3b76FCF54aEE0d821b755dFBA17250/1",
  "image_url": "https://oaidalleapiprodscus.blob.core.windows.net/...",
  "ipfs_url": "ipfs://QmSt9oAQnmqqc4Pg5FXyRDwvKtdtZRdysTgnjiMyhg9YxK",
  "transaction_hash": "0x123...",
  "transaction_url": "https://sepolia.basescan.org/tx/0x123..."
}
```

## Using the Client

```bash
python client.py --prompt "A pineapple character laying on the beach drinking caipirinha" --destination "0x2656C60B79A3376beC507453978af5Ac73a8b5fC"
```

Optional arguments:
- `--api-url`: Base URL of the API (default: http://localhost:8000)
- `--nft-name`: Name for this specific NFT
- `--contract-address`: Existing NFT contract address (can also be set in .env)

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key for DALL-E image generation
- `PINATA_JWT`: Your Pinata JWT for uploading to IPFS
- `NFT_CONTRACT_ADDRESS`: (Optional) Your NFT contract address

## Documentation

API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
