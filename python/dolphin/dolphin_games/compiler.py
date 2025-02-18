"""Dolphin Casino Game Compiler and Integration Module"""
from typing import Optional, Dict, Any
from pathlib import Path
import json
import logging

from ..core.types import GameState, TokenAccount
from ..prelude import Pubkey, Amount
from ..ir_gen import DolphinCLI

logger = logging.getLogger(__name__)

class GameProgram:
    """Represents a compiled game program ready for deployment"""
    def __init__(
        self,
        name: str,
        program_id: Pubkey,
        metadata: Dict[str, Any],
        state: GameState
    ):
        self.name = name
        self.program_id = program_id
        self.metadata = metadata
        self.state = state
        self.agent_pool: Dict[Pubkey, 'GameAgent'] = {}

    @property
    def total_agents(self) -> int:
        """Get total number of agents in the pool"""
        return len(self.agent_pool)

    def add_agent(self, agent: 'GameAgent') -> None:
        """Add an agent to the pool"""
        self.agent_pool[agent.pubkey] = agent

    def get_agent(self, pubkey: Pubkey) -> Optional['GameAgent']:
        """Get an agent by its pubkey"""
        return self.agent_pool.get(pubkey)

class GameAgent:
    """Represents a trained game agent"""
    def __init__(
        self,
        pubkey: Pubkey,
        owner: Pubkey,
        model_uri: str,
        metadata: Dict[str, Any]
    ):
        self.pubkey = pubkey
        self.owner = owner
        self.model_uri = model_uri
        self.metadata = metadata
        self.token_account: Optional[TokenAccount] = None
        self.stats = GameStats()

class GameStats:
    """Track agent performance statistics"""
    def __init__(self):
        self.total_games = 0
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.total_earnings: Amount = 0

    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage"""
        if self.total_games == 0:
            return 0.0
        return (self.wins / self.total_games) * 100

def compile_game(
    file_path: str,
    name: str,
    program_id: Pubkey,
    training_config: Optional[Dict[str, Any]] = None
) -> GameProgram:
    """Compile a game to a Dolphin GameProgram
    
    Args:
        file_path: Path to the game source code
        name: Name of the game program
        program_id: Solana program ID for deployment
        training_config: Optional configuration for agent training

    Returns:
        GameProgram: The compiled game program ready for deployment
    """
    logger.info(f"Compiling game: {name}")
    
    # Validate inputs
    source_path = Path(file_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Game source not found: {file_path}")

    # Load metadata
    metadata = {
        "name": name,
        "source": str(source_path),
        "training_config": training_config or {},
        "version": "1.0.0"
    }

    # Initialize game state
    state = GameState(
        version=1,
        authority=program_id,
        is_initialized=True
    )

    # Create game program
    game = GameProgram(
        name=name,
        program_id=program_id,
        metadata=metadata,
        state=state
    )

    # Compile using Dolphin CLI
    try:
        cli = DolphinCLI()
        cli.init(name, str(program_id))
        
        # Copy game source
        target_path = Path(f"{name}/src/lib.rs")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(source_path.read_text())
        
        # Build
        cli.build()
        logger.info(f"Successfully compiled game: {name}")
        
        # Save metadata
        metadata_path = Path(f"{name}/game_metadata.json")
        metadata_path.write_text(json.dumps(metadata, indent=2))
        
    except Exception as e:
        logger.error(f"Failed to compile game: {str(e)}")
        raise

    return game

def train_agent(
    game: GameProgram,
    training_params: Dict[str, Any]
) -> GameAgent:
    """Train a new agent for the game
    
    Args:
        game: The compiled game program
        training_params: Parameters for agent training

    Returns:
        GameAgent: The trained agent
    """
    logger.info(f"Training new agent for game: {game.name}")
    
    try:
        # Initialize training environment
        # TODO: Implement training logic
        
        # Create agent
        agent = GameAgent(
            pubkey=Pubkey.default(),  # Generate new pubkey
            owner=training_params.get("owner", Pubkey.default()),
            model_uri="",  # Set after training
            metadata={
                "training_params": training_params,
                "created_at": "",  # Set timestamp
                "version": "1.0.0"
            }
        )
        
        # Add to game's agent pool
        game.add_agent(agent)
        
        logger.info(f"Successfully trained new agent for {game.name}")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to train agent: {str(e)}")
        raise

def deploy_to_casino(
    game: GameProgram,
    agent: GameAgent,
    casino_program_id: Pubkey
) -> bool:
    """Deploy a trained agent to the Casino of Life
    
    Args:
        game: The compiled game program
        agent: The trained agent to deploy
        casino_program_id: Program ID of the Casino of Life

    Returns:
        bool: True if deployment was successful
    """
    logger.info(f"Deploying agent {agent.pubkey} to Casino of Life")
    
    try:
        # TODO: Implement casino integration
        # - Mint agent NFT
        # - Register with casino program
        # - Initialize betting pool
        
        logger.info(f"Successfully deployed agent to casino")
        return True
        
    except Exception as e:
        logger.error(f"Failed to deploy to casino: {str(e)}")
        raise
