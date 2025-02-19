"""
NFT Program Template
This template provides a basic structure for creating Solana NFT programs.
"""

from dolphin.prelude import *

@program("PROGRAM_ID_PLACEHOLDER")
class NFTProgram:
    """A Solana program for NFT management"""
    
    @account
    class NFTMint:
        """NFT mint account storing token metadata"""
        authority: Pubkey
        supply: u64  # Always 1 for NFTs
        is_initialized: bool = True
        freeze_authority: Optional[Pubkey] = None
        
    @account
    class NFTMetadata:
        """NFT metadata account storing token attributes"""
        mint: Pubkey
        update_authority: Pubkey
        name: str
        symbol: str
        uri: str  # URI to off-chain metadata
        seller_fee_basis_points: u16
        creators: List[Pubkey]
        creator_shares: List[u8]
        is_mutable: bool = True
        
    @account
    @pda(seeds=["nft", "owner"])
    class NFTAccount:
        """NFT account storing token ownership"""
        owner: Pubkey
        mint: Pubkey
        delegate: Optional[Pubkey] = None
        is_frozen: bool = False
        
    @instruction
    def initialize_mint(
        self,
        mint: NFTMint,
        metadata: NFTMetadata,
        authority: Signer,
        name: str,
        symbol: str,
        uri: str,
        creators: List[Pubkey],
        shares: List[u8],
        fee_basis_points: u16,
        freeze_authority: Optional[Pubkey],
        system_program: Program = SYSTEM_PROGRAM_ID
    ):
        """Initialize a new NFT mint and metadata
        
        Args:
            mint: The NFT mint account to initialize
            metadata: The metadata account to initialize
            authority: The mint authority
            name: NFT name
            symbol: NFT symbol
            uri: URI to off-chain metadata
            creators: List of creator public keys
            shares: List of creator share percentages
            fee_basis_points: Royalty fee in basis points (100 = 1%)
            freeze_authority: Optional authority to freeze accounts
            system_program: The system program
        """
        assert len(creators) == len(shares), "Creator and share lists must match"
        assert sum(shares) == 100, "Creator shares must total 100"
        
        # Initialize mint
        mint.authority = authority.key()
        mint.supply = 0
        mint.freeze_authority = freeze_authority
        mint.is_initialized = True
        
        # Initialize metadata
        metadata.mint = mint.key()
        metadata.update_authority = authority.key()
        metadata.name = name
        metadata.symbol = symbol
        metadata.uri = uri
        metadata.seller_fee_basis_points = fee_basis_points
        metadata.creators = creators
        metadata.creator_shares = shares
        
    @instruction
    def mint_nft(
        self,
        mint: NFTMint,
        metadata: NFTMetadata,
        account: NFTAccount,
        authority: Signer,
        owner: Pubkey,
        system_program: Program = SYSTEM_PROGRAM_ID
    ):
        """Mint a new NFT to an account
        
        Args:
            mint: The NFT mint
            metadata: The NFT metadata
            account: The destination account
            authority: Must match the mint authority
            owner: The NFT recipient
            system_program: The system program
        """
        assert mint.authority == authority.key(), "Invalid mint authority"
        assert mint.is_initialized, "Mint not initialized"
        assert mint.supply == 0, "NFT already minted"
        
        # Mint NFT
        mint.supply = 1
        
        # Initialize account
        account.owner = owner
        account.mint = mint.key()
        account.is_initialized = True
        
    @instruction
    def transfer(
        self,
        source: NFTAccount,
        destination: NFTAccount,
        authority: Signer
    ):
        """Transfer an NFT between accounts
        
        Args:
            source: The source account
            destination: The destination account
            authority: Must match the source account owner
        """
        assert source.owner == authority.key(), "Invalid account owner"
        assert source.mint == destination.mint, "Mint mismatch"
        assert not source.is_frozen, "Source account frozen"
        assert not destination.is_frozen, "Destination account frozen"
        
        # Update ownership
        source.owner = Pubkey.default()
        destination.owner = authority.key()
        
    @instruction
    def update_metadata(
        self,
        metadata: NFTMetadata,
        authority: Signer,
        name: Optional[str] = None,
        symbol: Optional[str] = None,
        uri: Optional[str] = None
    ):
        """Update NFT metadata
        
        Args:
            metadata: The metadata account to update
            authority: Must match the update authority
            name: Optional new name
            symbol: Optional new symbol
            uri: Optional new URI
        """
        assert metadata.update_authority == authority.key(), "Invalid update authority"
        assert metadata.is_mutable, "Metadata is immutable"
        
        if name:
            metadata.name = name
        if symbol:
            metadata.symbol = symbol
        if uri:
            metadata.uri = uri
            
    @instruction
    def set_immutable(
        self,
        metadata: NFTMetadata,
        authority: Signer
    ):
        """Make NFT metadata immutable
        
        Args:
            metadata: The metadata account
            authority: Must match the update authority
        """
        assert metadata.update_authority == authority.key(), "Invalid update authority"
        metadata.is_mutable = False
        
    @instruction
    def burn(
        self,
        mint: NFTMint,
        account: NFTAccount,
        authority: Signer
    ):
        """Burn an NFT
        
        Args:
            mint: The NFT mint
            account: The account to burn from
            authority: Must match the account owner
        """
        assert account.owner == authority.key(), "Invalid account owner"
        assert not account.is_frozen, "Account is frozen"
        
        # Burn NFT
        mint.supply = 0
        account.owner = Pubkey.default()
