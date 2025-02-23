from dolphin.prelude import (
    program, account, instruction,
    Pubkey, Signer, Program, Clock,
    SYSTEM_PROGRAM_ID, CLOCK_SYSVAR_ID,
    u64, i64
)
from dolphin.dolphin_games.casino_bridge import CasinoBridge
from pathlib import Path
import json

@program("HeLLo777777777777777777777777777777777777777")
class HelloWorldGame:
    """A simple game program that tracks player scores and integrates with Casino of Life"""
    
    @account
    class GameState:
        """Game state account storing player data and scores"""
        authority: Pubkey  # Game authority
        player: Pubkey    # Current player
        score: u64       # Player's score
        high_score: u64  # All-time high score
        last_play: i64   # Timestamp of last play
        is_initialized: bool  # Using Python's built-in bool
        
    @instruction
    def initialize(
        self,
        state: GameState,
        authority: Signer,
        system_program: Program = SYSTEM_PROGRAM_ID
    ):
        """Initialize the game state"""
        state.authority = authority.key()
        state.player = authority.key()
        state.score = 0
        state.high_score = 0
        state.last_play = 0
        state.is_initialized = True
        
    @instruction
    def update_score(
        self,
        state: GameState,
        player: Signer,
        new_score: u64,
        clock: Clock = CLOCK_SYSVAR_ID
    ):
        """Update player's score"""
        # Verify player authority
        assert state.player == player.key(), "Invalid player"
        assert state.is_initialized, "Game not initialized"
        
        # Update score
        state.score = new_score
        if new_score > state.high_score:
            state.high_score = new_score
            
        # Update last play timestamp
        state.last_play = clock.unix_timestamp

def setup_game_environment():
    """Set up the game environment with Casino of Life integration"""
    # Create scenario configuration
    scenario = {
        "name": "Hello World Training",
        "metadata": {
            "version": "1.0",
            "type": "training",
            "difficulty": "normal",
            "players": 1,
            "mode": "training"
        },
        "game_files": {
            "rom": "Airstriker-Genesis",  # Using built-in ROM
            "state": "Level1",
            "metadata": str(Path.cwd() / "metadata.json")
        }
    }
    
    # Save scenario configuration
    scenario_path = Path.cwd() / "scenario.json"
    with open(scenario_path, "w") as f:
        json.dump(scenario, f)
        
    # Initialize Casino bridge with program ID
    bridge = CasinoBridge(Pubkey("HeLLo777777777777777777777777777777777777777"))
    bridge.initialize_env(
        state_name="Level1",
        scenario_path=scenario_path
    )
    
    return bridge

def train_game_agent(bridge: CasinoBridge, training_steps: int = 100000):
    """Train an agent using the Casino of Life integration"""
    # Create agent with PPO policy
    bridge.create_agent(policy='PPO')
    
    # Train the agent
    results = bridge.train_agent(
        timesteps=training_steps,
        save_interval=10000,
        checkpoint_dir=Path.cwd() / "checkpoints"
    )
    
    return results

def main():
    """Main function demonstrating the complete workflow"""
    print("🎮 Setting up Hello World Game environment...")
    bridge = setup_game_environment()
    
    print("🤖 Training game agent...")
    results = train_game_agent(bridge)
    
    print("✨ Training complete!")
    print(f"Final score: {results.get('final_score', 0)}")
    print(f"High score: {results.get('high_score', 0)}")
    
if __name__ == "__main__":
    main()
