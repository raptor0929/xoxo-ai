use anchor_lang::prelude::*;
use anchor_spl::associated_token::AssociatedToken;
use anchor_spl::token::{self, Mint, MintTo, Token, TokenAccount};

// Direct imports for old Metaplex CPI functions
use mpl_token_metadata::ID as METADATA_PROGRAM_ID;
use mpl_token_metadata::instruction::{create_metadata_accounts_v3, create_master_edition_v3};

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod xoxo_nft {
    use super::*;

    pub fn mint_nft(ctx: Context<MintNFT>, uri: String) -> Result<()> {
        let name = "Xoxo NFT".to_string();
        let symbol = "XOXO".to_string();

        // Mint the token to the user's token account
        let cpi_accounts = MintTo {
            mint: ctx.accounts.mint.to_account_info(),
            to: ctx.accounts.token_account.to_account_info(),
            authority: ctx.accounts.authority.to_account_info(),
        };
        let cpi_ctx = CpiContext::new(ctx.accounts.token_program.to_account_info(), cpi_accounts);
        token::mint_to(cpi_ctx, 1)?;

        // Create metadata
        let metadata_ix = create_metadata_accounts_v3(
            METADATA_PROGRAM_ID,
            ctx.accounts.metadata.key(),
            ctx.accounts.mint.key(),
            ctx.accounts.authority.key(),
            ctx.accounts.authority.key(),
            ctx.accounts.authority.key(),
            name,
            symbol,
            uri,
            Some(vec![mpl_token_metadata::state::Creator {
                address: ctx.accounts.authority.key(),
                verified: true,
                share: 100,
            }]),
            0,
            true,
            true,
            None,
            None,
            None,
        );

        anchor_lang::solana_program::program::invoke(
            &metadata_ix,
            &[
                ctx.accounts.metadata.to_account_info(),
                ctx.accounts.mint.to_account_info(),
                ctx.accounts.authority.to_account_info(),
                ctx.accounts.system_program.to_account_info(),
                ctx.accounts.rent.to_account_info(),
            ],
        )?;

        // Create master edition
        let edition_ix = create_master_edition_v3(
            METADATA_PROGRAM_ID,
            ctx.accounts.master_edition.key(),
            ctx.accounts.mint.key(),
            ctx.accounts.authority.key(),
            ctx.accounts.authority.key(),
            ctx.accounts.metadata.key(),
            ctx.accounts.authority.key(),
            Some(0),
        );

        anchor_lang::solana_program::program::invoke(
            &edition_ix,
            &[
                ctx.accounts.master_edition.to_account_info(),
                ctx.accounts.mint.to_account_info(),
                ctx.accounts.authority.to_account_info(),
                ctx.accounts.metadata.to_account_info(),
                ctx.accounts.token_program.to_account_info(),
                ctx.accounts.system_program.to_account_info(),
                ctx.accounts.rent.to_account_info(),
            ],
        )?;

        Ok(())
    }
}

#[derive(Accounts)]
pub struct MintNFT<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,

    #[account(
        init,
        payer = authority,
        mint::decimals = 0,
        mint::authority = authority,
        mint::freeze_authority = authority
    )]
    pub mint: Account<'info, Mint>,

    #[account(
        init_if_needed,
        payer = authority,
        associated_token::mint = mint,
        associated_token::authority = authority,
    )]
    pub token_account: Account<'info, TokenAccount>,

    /// CHECK: Metaplex validates this
    #[account(mut)]
    pub metadata: UncheckedAccount<'info>,

    /// CHECK: Metaplex validates this
    #[account(mut)]
    pub master_edition: UncheckedAccount<'info>,

    pub token_program: Program<'info, Token>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub system_program: Program<'info, System>,
    pub rent: Sysvar<'info, Rent>,
}
