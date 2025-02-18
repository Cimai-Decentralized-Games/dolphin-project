"""
Multisig Wallet Example
This example shows a multisig wallet implementation
"""
from dolphin.prelude import *

@program("MultiSig5555555555555555555555555555555555555")
class MultisigWallet:
    @account
    class WalletConfig:
        owners: List[Pubkey]  
        threshold: u8         
        nonce: u32           

    @account
    @pda("wallet", "nonce")
    class Transaction:
        wallet: Pubkey
        nonce: u32
        program_id: Pubkey
        accounts: List[Pubkey]
        data: List[u8]
        signers: List[bool]
        executed: bool
        
    @instruction
    def initialize_wallet(self, owners: List[Pubkey], threshold: u8):
        """Initialize a new multisig wallet"""
        assert 1 <= threshold <= len(owners)
        assert len(owners) <= 10
        
        self.config.owners = owners
        self.config.threshold = threshold
        self.config.nonce = 0

    @instruction
    def propose_transaction(
        self,
        program_id: Pubkey,
        accounts: List[Pubkey],
        data: List[u8]
    ):
        """Propose a new transaction"""
        assert self.signer in self.config.owners
        
        nonce = self.config.nonce
        self.config.nonce += 1
        
        self.transaction.wallet = self.config.pubkey
        self.transaction.nonce = nonce
        self.transaction.program_id = program_id
        self.transaction.accounts = accounts
        self.transaction.data = data
        self.transaction.signers = [False] * len(self.config.owners)
        self.transaction.executed = False
        
        # Auto-approve by proposer
        owner_index = self.config.owners.index(self.signer)
        self.transaction.signers[owner_index] = True

    @instruction
    def approve_transaction(self):
        """Approve a proposed transaction"""
        assert self.signer in self.config.owners
        assert not self.transaction.executed
        
        owner_index = self.config.owners.index(self.signer)
        self.transaction.signers[owner_index] = True

    @instruction
    def execute_transaction(self):
        """Execute a transaction that has enough approvals"""
        assert not self.transaction.executed
        
        # Count approvals
        approval_count = sum(1 for approved in self.transaction.signers if approved)
        assert approval_count >= self.config.threshold
        
        # Mark as executed
        self.transaction.executed = True
        
        # Execute the transaction (in practice, this would use CPI)
        print(f"Executing transaction to program {self.transaction.program_id}")