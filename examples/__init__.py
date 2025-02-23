"""
Dolphin Framework Examples
========================

This package contains example programs demonstrating various features of the Dolphin framework:

1. Hello World Game
-----------------
A basic example showing how to:
- Create a Solana program with game state
- Integrate with Casino of Life for game environments
- Train and deploy game agents
- Use IR generation and compilation

Usage:
    from examples.hello_world_game import HelloWorldGame, setup_game_environment, train_game_agent

    # Create and train a game agent
    bridge = setup_game_environment()
    results = train_game_agent(bridge)

See hello_world_game.py for the complete implementation.
"""

from .hello_world_game import HelloWorldGame, setup_game_environment, train_game_agent

__all__ = [
    'HelloWorldGame',
    'setup_game_environment',
    'train_game_agent'
]
