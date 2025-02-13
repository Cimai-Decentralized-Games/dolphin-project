"""
NFT Marketplace Example
This example shows a marketplace for NFTs with listings and purchases
"""
from dolphin.prelude import *

@program("MarketProg333333333333333333333333333333333333")
class NFTMarketplace:
    @account
    class MarketConfig:
        authority: Pubkey
        fee_account: Pubkey
        fee_basis_points: u16  # 100 = 1%

    @account
    @pda("nft_mint", "seller")
    class Listing:
        seller: Pubkey
        nft_mint: Pubkey
        price: u64
        token_account: Pubkey

    @instruction
    def initialize_market(self, authority: Pubkey, fee_account: Pubkey, fee_bps: u16):
        """Initialize the marketplace"""
        assert fee_bps <= 1000, "Fee cannot exceed 10%"
        self.config.authority = authority
        self.config.fee_account = fee_account
        self.config.fee_basis_points = fee_bps

    @instruction
    def create_listing(
        self, 
        nft_mint: Pubkey,
        price: u64,
        seller_nft_account: TokenAccount
    ):
        """List an NFT for sale"""
        assert seller_nft_account.amount == 1, "Must be selling 1 NFT"
        assert seller_nft_account.owner == self.signer, "Must own the NFT"
        
        self.listing.seller = self.signer
        self.listing.nft_mint = nft_mint
        self.listing.price = price
        self.listing.token_account = seller_nft_account.pubkey

    @instruction
    def purchase(
        self,
        buyer_nft_account: TokenAccount,
        buyer_payment_account: TokenAccount,
        seller_payment_account: TokenAccount,
        fee_account: TokenAccount
    ):
        """Purchase a listed NFT"""
        # Calculate fees
        fee_amount = (self.listing.price * self.config.fee_basis_points) // 10000
        seller_amount = self.listing.price - fee_amount

        # Transfer payment
        buyer_payment_account.amount -= self.listing.price
        seller_payment_account.amount += seller_amount
        fee_account.amount += fee_amount

        # Transfer NFT
        self.token_account.amount -= 1
        buyer_nft_account.amount += 1