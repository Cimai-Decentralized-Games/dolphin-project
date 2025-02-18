"""
Hello World Game - A simple example of a Dolphin game program
with Casino of Life integration
"""

from dolphin.prelude import *
from dolphin.dolphin_games import GameConfig, AgentState

@program("HeLLo777777777777777777777777777777777777777")
class HelloWorldGame:
    """A simple game program demonstrating Dolphin's game development features"""
    
    # Game Configuration
    config = GameConfig(
        name="Hello World Game",
        version="1.0.0",
        max_players=2,
        min_stake=1_000_000,  # 0.001 SOL
        max_stake=1_000_000_000,  # 1 SOL
        game_duration=300,  # 5 minutes
        commission_rate=0.05,  # 5%
    )
    
    @account
    class GameAccount(GameState):
        """Main game state account"""
        current_round: u64
        total_games: u64
        treasury: Pubkey
        
    @account
    @pda(seeds=["player"])
    class PlayerAccount:
        """Player state account"""
        owner: Pubkey
        games_played: u64
        wins: u64
        losses: u64
        last_game: i64
        stake_account: Pubkey
        
    @account
    @pda(seeds=["agent"])
    class AgentAccount:
        """AI agent account"""
        owner: Pubkey
        mint: Pubkey
        state: AgentState
        metadata_uri: str
        
    @instruction
    def initialize(
        self,
        game: GameAccount,
        authority: Signer,
        treasury: Pubkey,
        system_program: Program = SYSTEM_PROGRAM_ID
    ):
        """Initialize the game program"""
        game.authority = authority.key
        game.treasury = treasury
        game.current_round = 0
        game.total_games = 0
        game.is_initialized = True
        
    @instruction
    def create_player(
        self,
        player: PlayerAccount,
        owner: Signer,
        stake_account: Pubkey,
        system_program: Program = SYSTEM_PROGRAM_ID
    ):
        """Create a new player account"""
        player.owner = owner.key
        player.games_played = 0
        player.wins = 0
        player.losses = 0
        player.last_game = 0
        player.stake_account = stake_account
        
    @instruction
    def register_agent(
        self,
        agent: AgentAccount,
        owner: Signer,
        mint: Pubkey,
        metadata_uri: str,
        system_program: Program = SYSTEM_PROGRAM_ID
    ):
        """Register a new AI agent"""
        agent.owner = owner.key
        agent.mint = mint
        agent.metadata_uri = metadata_uri
        agent.state = AgentState(
            version=1,
            is_active=True,
            owner=owner.key,
            mint=mint
        )
        
    @instruction
    def start_game(
        self,
        game: GameAccount,
        player: PlayerAccount,
        agent: AgentAccount,
        authority: Signer,
        clock: Sysvar = CLOCK_SYSVAR_ID
    ):
        """Start a new game between player and agent"""
        assert game.is_initialized, "Game not initialized"
        assert player.owner == authority.key, "Invalid player"
        assert agent.state.is_active, "Agent not active"
        
        # Update game state
        game.current_round += 1
        player.last_game = clock.unix_timestamp
        
    @instruction
    def end_game(
        self,
        game: GameAccount,
        player: PlayerAccount,
        agent: AgentAccount,
        authority: Signer,
        player_won: bool
    ):
        """End a game and update scores"""
        assert game.is_initialized, "Game not initialized"
        assert player.owner == authority.key, "Invalid player"
        
        # Update stats
        game.total_games += 1
        player.games_played += 1
        
        if player_won:
            player.wins += 1
            agent.state.stats.losses += 1
        else:
            player.losses += 1
            agent.state.stats.wins += 1
            
        agent.state.stats.total_games += 1
        
    @instruction
    def claim_rewards(
        self,
        game: GameAccount,
        player: PlayerAccount,
        authority: Signer,
        amount: u64,
        system_program: Program = SYSTEM_PROGRAM_ID
    ):
        """Claim rewards from winning games"""
        assert player.owner == authority.key, "Invalid player"
        assert amount > 0, "Invalid amount"
        
        # Transfer rewards logic here
        pass

# Example usage:
if __name__ == "__main__":
    from dolphin.dolphin_games import compile_game, train_agent, deploy_to_casino
    
    # Compile the game
    game = compile_game(
        file_path=__file__,
        name="Hello World Game",
        program_id="HeLLo777777777777777777777777777777777777777",
        training_config={
            "episodes": 1000,
            "learning_rate": 0.001
        }
    )
    
    # Train an agent
    agent = train_agent(
        game=game,
        training_params={
            "model_type": "dqn",
            "hidden_layers": [64, 64]
        }
    )
    
    # Deploy to Casino
    deploy_to_casino(
        game=game,
        agent=agent,
        casino_program_id="Casino111111111111111111111111111111111111"
    )
