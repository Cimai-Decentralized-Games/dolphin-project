"""
Game Program Template
This template provides a basic structure for creating Solana games.
"""

from dolphin.prelude import *

@program("PROGRAM_ID_PLACEHOLDER")
class GameProgram:
    """A Solana program for agent training to play retro games"""
    
    @account
    class GameState(GameState):
        """Main game state account"""
        agent: Pubkey
        score: u64
        level: u8
        last_play: UnixTimestamp
        
    @account
    @pda(seeds=["agent"])
    class TrainingState:
        """Training state account storing training data"""
        owner: Pubkey
        games_played: u64
        wins: u64
        losses: u64
        total_score: u64
        highest_level: u8
        
    @instruction
    def initialize_game(
        self,
        game: GameState,
        agent: TrainingState,
        authority: Signer,
        system_program: Program = SYSTEM_PROGRAM_ID
    ):
        """Initialize a new retro game"""
        
        Args:
            game: The game state account to initialize
            agent The agent's state account
            authority: The game authority (usually the agents owner)
            system_program: The system program
        """
        game.authority = authority.key()
        game.agent = authority.key()
        game.score = 0
        game.level = 1
        game.last_play = 0
        game.is_initialized = True
        
        # Initialize training state if new
        if not agent.is_initialized:
            agent.owner = authority.key()
            agent.games_played = 0
            agent.wins = 0
            agent.losses = 0
            agent.total_score = 0
            agent.highest_level = 1
            agent.is_initialized = True
    
    @instruction
    def update_score(
        self,
        game: GameState,
        agent: TrainingState,
        authority: Signer,
        points: u64,
        clock: Clock = CLOCK_SYSVAR_ID
    ):
        """Update the game score
        
        Args:
            game: The game state to update
            agent: The agent's state
            authority: Must match the game's authority
            points: Points to add to the score
            clock: The clock sysvar for timestamp
        """
        assert game.authority == authority.key(), "Invalid authority"
        assert game.is_initialized, "Game not initialized"
        
        game.score += points
        game.last_play = clock.unix_timestamp
        
        # Update agents stats
        agent.total_score += points
        if game.level > agent.highest_level:
            agent.highest_level = game.level
    
    @instruction
    def level_up(
        self,
        game: GameState,
        agent: TrainingState,
        authority: Signer
    ):
        """Advance to the next level
        
        Args:
            game: The game state to update
            player: The player's state
            authority: Must match the game's authority
        """
        assert game.authority == authority.key(), "Invalid authority"
        assert game.is_initialized, "Game not initialized"
        
        # Add level up logic here
        game.level += 1
        if game.level > player.highest_level:
            player.highest_level = game.level
    
    @instruction
    def end_game(
        self,
        game: GameState,
        player: PlayerState,
        authority: Signer,
        won: bool
    ):
        """End the current game
        
        Args:
            game: The game state to update
            player: The player's state
            authority: Must match the game's authority
            won: Whether the player won the game
        """
        assert game.authority == authority.key(), "Invalid authority"
        assert game.is_initialized, "Game not initialized"
        
        # Update player stats
        player.games_played += 1
        if won:
            player.wins += 1
        else:
            player.losses += 1
        
        # Reset game state
        game.is_initialized = False
