"""
Token Program Template
This template provides a basic structure for creating Solana token programs.
"""

from dolphin.prelude import *

@program("PROGRAM_ID_PLACEHOLDER")
class TokenProgram:
    """A Solana program for token management"""
    
    @account
    class TokenMint:
        """Token mint account storing token metadata"""
        authority: Pubkey
        supply: u64
        decimals: u8
        is_initialized: bool = True
        freeze_authority: Optional[Pubkey] = None
        
    @account
    @pda(seeds=["token", "owner"])
    class TokenAccount:
        """Token account storing token balances"""
        owner: Pubkey
        mint: Pubkey
        amount: u64
        delegate: Optional[Pubkey] = None
        is_frozen: bool = False
        delegate_amount: u64 = 0
        
    @instruction
    def initialize_mint(
        self,
        mint: TokenMint,
        authority: Signer,
        decimals: u8,
        freeze_authority: Optional[Pubkey],
        system_program: Program = SYSTEM_PROGRAM_ID
    ):
        """Initialize a new token mint
        
        Args:
            mint: The mint account to initialize
            authority: The mint authority
            decimals: Number of decimal places
            freeze_authority: Optional authority to freeze accounts
            system_program: The system program
        """
        mint.authority = authority.key()
        mint.supply = 0
        mint.decimals = decimals
        mint.freeze_authority = freeze_authority
        mint.is_initialized = True
        
    @instruction
    def initialize_account(
        self,
        account: TokenAccount,
        mint: TokenMint,
        owner: Signer,
        system_program: Program = SYSTEM_PROGRAM_ID
    ):
        """Initialize a new token account
        
        Args:
            account: The token account to initialize
            mint: The token mint
            owner: The account owner
            system_program: The system program
        """
        assert mint.is_initialized, "Mint not initialized"
        
        account.owner = owner.key()
        account.mint = mint.key()
        account.amount = 0
        account.is_initialized = True
        
    @instruction
    def mint_to(
        self,
        mint: TokenMint,
        account: TokenAccount,
        authority: Signer,
        amount: u64
    ):
        """Mint tokens to an account
        
        Args:
            mint: The token mint
            account: The destination account
            authority: Must match the mint authority
            amount: Amount to mint
        """
        assert mint.authority == authority.key(), "Invalid mint authority"
        assert mint.is_initialized, "Mint not initialized"
        assert account.mint == mint.key(), "Account mint mismatch"
        assert not account.is_frozen, "Account is frozen"
        
        mint.supply += amount
        account.amount += amount
        
    @instruction
    def transfer(
        self,
        source: TokenAccount,
        destination: TokenAccount,
        authority: Signer,
        amount: u64
    ):
        """Transfer tokens between accounts
        
        Args:
            source: The source account
            destination: The destination account
            authority: Must match the source account owner
            amount: Amount to transfer
        """
        assert source.owner == authority.key(), "Invalid account owner"
        assert source.mint == destination.mint, "Mint mismatch"
        assert source.amount >= amount, "Insufficient funds"
        assert not source.is_frozen, "Source account frozen"
        assert not destination.is_frozen, "Destination account frozen"
        
        source.amount -= amount
        destination.amount += amount
        
    @instruction
    def burn(
        self,
        mint: TokenMint,
        account: TokenAccount,
        authority: Signer,
        amount: u64
    ):
        """Burn tokens from an account
        
        Args:
            mint: The token mint
            account: The account to burn from
            authority: Must match the account owner
            amount: Amount to burn
        """
        assert account.owner == authority.key(), "Invalid account owner"
        assert account.amount >= amount, "Insufficient funds"
        assert not account.is_frozen, "Account is frozen"
        
        account.amount -= amount
        mint.supply -= amount
        
    @instruction
    def freeze_account(
        self,
        mint: TokenMint,
        account: TokenAccount,
        authority: Signer
    ):
        """Freeze a token account
        
        Args:
            mint: The token mint
            account: The account to freeze
            authority: Must match the mint's freeze authority
        """
        assert mint.freeze_authority == Some(authority.key()), "Invalid freeze authority"
        assert account.mint == mint.key(), "Account mint mismatch"
        
        account.is_frozen = True
        
    @instruction
    def thaw_account(
        self,
        mint: TokenMint,
        account: TokenAccount,
        authority: Signer
    ):
        """Thaw a frozen token account
        
        Args:
            mint: The token mint
            account: The account to thaw
            authority: Must match the mint's freeze authority
        """
        assert mint.freeze_authority == Some(authority.key()), "Invalid freeze authority"
        assert account.mint == mint.key(), "Account mint mismatch"
        
        account.is_frozen = False
