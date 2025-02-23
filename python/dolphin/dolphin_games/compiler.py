"""Dolphin Casino Game Compiler and Integration Module"""
from typing import Optional, Dict, Any
from pathlib import Path
import json
import logging
import gym
import numpy as np

from ..core.types import GameState, TokenAccount
from ..prelude import Pubkey, Amount
from ..ir_gen import DolphinCLI
from .retro_support import RetroGameWrapper, create_retro_game

logger = logging.getLogger(__name__)

# Supported game types
GAME_TYPE_SOLANA = "solana" 
GAME_TYPE_RETRO = "retro"

class GameProgram:
    """Represents a compiled game program ready for deployment"""
    def __init__(
        self,
        name: str,
        program_id: Pubkey,
        metadata: Dict[str, Any],
        state: GameState,
        game_type: str = GAME_TYPE_SOLANA
    ):
        self.name = name
        self.program_id = program_id
        self.metadata = metadata
        self.state = state
        self.game_type = game_type
        self.agent_pool: Dict[Pubkey, 'GameAgent'] = {}
        
        # Retro game specific attributes
        self.env: Optional[RetroGameWrapper] = None
        self.observation_space: Optional[gym.Space] = None
        self.action_space: Optional[gym.Space] = None

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
    game_type: str = GAME_TYPE_SOLANA,
    training_config: Optional[Dict[str, Any]] = None,
    retro_config: Optional[Dict[str, Any]] = None
) -> GameProgram:
    """Compile a game to a Dolphin GameProgram
    
    Args:
        file_path: Path to the game source code or ROM
        name: Name of the game program
        program_id: Solana program ID for deployment
        game_type: Type of game (solana or retro)
        training_config: Optional configuration for agent training
        retro_config: Optional configuration for retro games

    Returns:
        GameProgram: The compiled game program ready for deployment
    """
    logger.info(f"Compiling game: {name} (type: {game_type})")
    
    # Initialize metadata
    metadata = {
        "name": name,
        "game_type": game_type,
        "training_config": training_config or {},
        "version": "1.0.0"
    }

    if game_type == GAME_TYPE_SOLANA:
        # Validate Solana program source
        source_path = Path(file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Game source not found: {file_path}")
            
        metadata["source"] = str(source_path)
        
        # Initialize Solana game state
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
            state=state,
            game_type=game_type
        )
        
        # Compile Solana program
        try:
            cli = DolphinCLI()
            cli.init(name, str(program_id))
            
            # Copy game source
            target_path = Path(f"{name}/src/lib.rs")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(source_path.read_text())
            
            # Build
            cli.build()
            logger.info(f"Successfully compiled Solana program: {name}")
            
        except Exception as e:
            logger.error(f"Failed to compile Solana program: {str(e)}")
            raise
            
    elif game_type == GAME_TYPE_RETRO:
        if not retro_config:
            raise ValueError("retro_config required for retro games")
            
        # Create retro game environment
        env = create_retro_game(
            game_name=file_path,  # ROM name for retro games
            program_id=program_id,
            **retro_config
        )
        
        # Update metadata with retro config
        metadata.update({
            "retro_config": retro_config,
            "observation_space": str(env.observation_space),
            "action_space": str(env.action_space)
        })
        
        # Create game program with retro environment
        game = GameProgram(
            name=name,
            program_id=program_id,
            metadata=metadata,
            state=env.game_state,
            game_type=game_type
        )
        game.env = env
        game.observation_space = env.observation_space
        game.action_space = env.action_space
        
        logger.info(f"Successfully initialized retro game: {name}")
        
    else:
        raise ValueError(f"Unsupported game type: {game_type}")

    # Save metadata
    metadata_path = Path(f"{name}/game_metadata.json")
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2))

    return game

def train_agent(
    game: GameProgram,
    training_params: Dict[str, Any],
    model_type: str = "dqn"
) -> GameAgent:
    """Train a new agent for the game
    
    Args:
        game: The compiled game program
        training_params: Parameters for agent training
        model_type: Type of model to use (dqn, ppo, etc)

    Returns:
        GameAgent: The trained agent
    """
    logger.info(f"Training new agent for game: {game.name}")
    
    try:
        if game.game_type == GAME_TYPE_RETRO:
            if not game.env:
                raise ValueError("Retro game environment not initialized")
                
            # Initialize training environment
            from stable_baselines3 import DQN, PPO, A2C
            
            # Select algorithm based on model type
            if model_type == "dqn":
                model = DQN(
                    "CnnPolicy",
                    game.env,
                    learning_rate=training_params.get("learning_rate", 0.0001),
                    verbose=1
                )
            elif model_type == "ppo":
                model = PPO(
                    "CnnPolicy",
                    game.env,
                    learning_rate=training_params.get("learning_rate", 0.0003),
                    verbose=1
                )
            elif model_type == "a2c":
                model = A2C(
                    "CnnPolicy",
                    game.env,
                    learning_rate=training_params.get("learning_rate", 0.0007),
                    verbose=1
                )
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
                
            # Train model
            total_timesteps = training_params.get("total_timesteps", 100000)
            model.learn(total_timesteps=total_timesteps)
            
            # Save model
            model_path = f"{game.name}/models/agent_{model_type}"
            Path(model_path).parent.mkdir(parents=True, exist_ok=True)
            model.save(model_path)
            
            # Create agent
            agent = GameAgent(
                pubkey=Pubkey.default(),  # Generate new pubkey
                owner=training_params.get("owner", Pubkey.default()),
                model_uri=model_path,
                metadata={
                    "model_type": model_type,
                    "training_params": training_params,
                    "observation_space": str(game.observation_space),
                    "action_space": str(game.action_space),
                    "version": "1.0.0"
                }
            )
            
        else:
            # TODO: Implement Solana program agent training
            agent = GameAgent(
                pubkey=Pubkey.default(),
                owner=training_params.get("owner", Pubkey.default()),
                model_uri="",
                metadata={
                    "training_params": training_params,
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
