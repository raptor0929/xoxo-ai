# XOXO AI - Dating Simulation Experiment

![XOXO AI Banner](./public/xoxo-ai.png)

## Overview

XOXO AI is an experimental dating simulation platform that combines modern web technologies with blockchain to create immersive, AI-powered dating experiences. The application allows users to create profiles, match with AI-generated personalities, and interact through simulated conversations.

## Features

- **Profile Creation**: Create your dating profile with preferences and interests
- **AI Matching**: Get matched with AI-generated personalities based on compatibility
- **Interactive Chat**: Engage in conversations with your AI matches
- **NFT Minting**: Mint your favorite connections as NFTs on the blockchain
- **Conversation Transcripts**: Download conversation logs for memorable interactions

## Technology Stack

- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **Styling**: Shadcn UI components
- **Blockchain**: Ethereum (Base Sepolia Testnet)
- **Smart Contract**: ERC-721 NFT standard

## Smart Contract

The XOXO AI dating simulation uses an ERC-721 smart contract deployed on the Base Sepolia testnet:

- **Contract Address**: [0xb944C6eAFb3b76FCF54aEE0d821b755dFBA17250](https://sepolia.basescan.org/address/0xb944C6eAFb3b76FCF54aEE0d821b755dFBA17250)
- **View NFTs**: [OpenSea Testnet Collection](https://testnets.opensea.io/collection/xoxo-ai-dating)

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- npm or pnpm

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/raptor0929/xoxo-ai.git
   cd xoxo-ai
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   pnpm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   # or
   pnpm dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser to see the application.

## User Flow

1. Create your dating profile
2. System matches you with compatible AI personalities
3. Interact with your matches through chat
4. Mint your favorite connections as NFTs
5. Download conversation transcripts

## Project Structure

```
xoxo-ai/
├── app/                  # Next.js app directory
│   ├── matching/         # Matching animation page
│   ├── matches/          # Matches display page
│   ├── profile/          # Profile creation page
│   └── ...
├── components/           # UI components
├── public/               # Static assets
├── styles/               # Global styles
├── action_providers/     # Backend action providers
│   └── erc721/           # NFT minting functionality
└── ...
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This project is an experimental concept exploring the intersection of AI, dating, and blockchain technology
- Special thanks to the Base Sepolia testnet for providing the blockchain infrastructure
