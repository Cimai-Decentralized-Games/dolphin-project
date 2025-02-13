"""
Staking Program Example
This example demonstrates a staking program with rewards
"""
from dolphin.prelude import *

@program("StakeProg4444444444444444444444444444444444444")
class StakingProgram:
    @account
    class StakePool:
        authority: Pubkey
        stake_mint: Pubkey
        reward_mint: Pubkey
        total_staked: u64
        rewards_per_token: u64
        last_update_time: UnixTimestamp

    @account
    @pda("owner", "pool")
    class UserStake:
        owner: Pubkey
        pool: Pubkey
        amount: u64
        reward_debt: u64
        last_claim_time: UnixTimestamp

    @instruction
    def initialize_pool(
        self,
        authority: Pubkey,
        stake_mint: Pubkey,
        reward_mint: Pubkey
    ):
        """Initialize a new staking pool"""
        self.pool.authority = authority
        self.pool.stake_mint = stake_mint
        self.pool.reward_mint = reward_mint
        self.pool.total_staked = 0
        self.pool.rewards_per_token = 0
        self.pool.last_update_time = self.clock.unix_timestamp

    @instruction
    def stake(self, amount: u64, user_token_account: TokenAccount):
        """Stake tokens into the pool"""
        assert user_token_account.mint == self.pool.stake_mint, "Invalid token mint"
        
        # Update rewards
        self._update_rewards()
        
        # Transfer tokens to stake
        user_token_account.amount -= amount
        self.pool.total_staked += amount
        
        # Update user stake
        self.user_stake.amount += amount
        self.user_stake.reward_debt = (
            self.user_stake.amount * self.pool.rewards_per_token
        )

    @instruction
    def claim_rewards(self, user_reward_account: TokenAccount):
        """Claim accumulated rewards"""
        assert user_reward_account.mint == self.pool.reward_mint, "Invalid reward mint"
        
        # Update rewards
        self._update_rewards()
        
        # Calculate pending rewards
        pending_reward = (
            self.user_stake.amount * self.pool.rewards_per_token
        ) - self.user_stake.reward_debt
        
        # Transfer rewards
        if pending_reward > 0:
            user_reward_account.amount += pending_reward
            self.user_stake.reward_debt = (
                self.user_stake.amount * self.pool.rewards_per_token
            )
            self.user_stake.last_claim_time = self.clock.unix_timestamp

    def _update_rewards(self):
        """Internal helper to update reward calculations"""
        if self.pool.total_staked == 0:
            return

        time_elapsed = self.clock.unix_timestamp - self.pool.last_update_time
        if time_elapsed > 0:
            rewards = time_elapsed * self.REWARD_RATE
            self.pool.rewards_per_token += rewards // self.pool.total_staked
            self.pool.last_update_time = self.clock.unix_timestamp