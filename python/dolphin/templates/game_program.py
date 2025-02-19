"""
Game Program Template
This template provides a basic structure for creating Solana games.
"""

from dolphin.prelude import *

@program("PROGRAM_ID_PLACEHOLDER")
class GameProgram:
    """A Solana program for game development"""
    
    @account
    class GameState(GameState):
        """Main game state account"""
        player: Pubkey
        score: u64
        level: u8
        last_play: UnixTimestamp
        
    @account
    @pda(seeds=["player"])
    class PlayerState:
        """Player state account storing player data"""
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
        player: PlayerState,
        authority: Signer,
        system_program: Program = SYSTEM_PROGRAM_ID
    ):
        """Initialize a new game
        
        Args:
            game: The game state account to initialize
            player: The player's state account
            authority: The game authority (usually the player)
            system_program: The system program
        """
        game.authority = authority.key()
        game.player = authority.key()
        game.score = 0
        game.level = 1
        game.last_play = 0
        game.is_initialized = True
        
        # Initialize player state if new
        if not player.is_initialized:
            player.owner = authority.key()
            player.games_played = 0
            player.wins = 0
            player.losses = 0
            player.total_score = 0
            player.highest_level = 1
            player.is_initialized = True
    
    @instruction
    def update_score(
        self,
        game: GameState,
        player: PlayerState,
        authority: Signer,
        points: u64,
        clock: Clock = CLOCK_SYSVAR_ID
    ):
        """Update the game score
        
        Args:
            game: The game state to update
            player: The player's state
            authority: Must match the game's authority
            points: Points to add to the score
            clock: The clock sysvar for timestamp
        """
        assert game.authority == authority.key(), "Invalid authority"
        assert game.is_initialized, "Game not initialized"
        
        game.score += points
        game.last_play = clock.unix_timestamp
        
        # Update player stats
        player.total_score += points
        if game.level > player.highest_level:
            player.highest_level = game.level
    
    @instruction
    def level_up(
        self,
        game: GameState,
        player: PlayerState,
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
