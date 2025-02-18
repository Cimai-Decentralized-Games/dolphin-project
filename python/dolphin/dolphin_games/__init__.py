"""
Dolphin Game Development Framework

This module provides tools and utilities for developing games on Solana
using the Dolphin framework, with specific support for Casino of Life integration.
"""

from .compiler import (
    GameProgram,
    GameAgent,
    GameStats,
    compile_game,
    train_agent,
    deploy_to_casino,
)

from .format import (
    AgentMetadata,
    AgentStats,
    AgentState,
    BettingPool,
    GameConfig,
    MatchResult,
    create_agent_metadata,
)

__all__ = [
    # Compiler module
    'GameProgram',
    'GameAgent',
    'GameStats',
    'compile_game',
    'train_agent',
    'deploy_to_casino',
    
    # Format module
    'AgentMetadata',
    'AgentStats',
    'AgentState',
    'BettingPool',
    'GameConfig',
    'MatchResult',
    'create_agent_metadata',
]

__version__ = "0.1.0"
__author__ = "Caballo Loko"
__email__ = "caballoloko@cimai.biz"

# Example usage in docstring
__doc__ += """
Example usage:

from dolphin.dolphin_games import compile_game, train_agent, deploy_to_casino
from dolphin.prelude import Pubkey

# Initialize a new game
game = compile_game(
    file_path="path/to/game.py",
    name="My Retro Game",
    program_id=Pubkey.default(),
    training_config={
        "episodes": 1000,
        "learning_rate": 0.001
    }
)

# Train an agent
agent = train_agent(
    game=game,
    training_params={
        "owner": Pubkey.default(),
        "model_type": "dqn",
        "hidden_layers": [64, 64]
    }
)

# Deploy to Casino of Life
success = deploy_to_casino(
    game=game,
    agent=agent,
    casino_program_id=Pubkey("Casino1111111111111111111111111111111111111")
)
"""
