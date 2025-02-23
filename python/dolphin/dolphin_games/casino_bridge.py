from typing import Dict, Any, Optional, List
from pathlib import Path
import json
from casino_of_life import RetroEnv, DynamicAgent
from casino_of_life.client_bridge import RewardEvaluatorManager, ActionMapper
from ..core.casino_types import CasinoGameState
from ..core.types import Pubkey
from .casino_config import CasinoTrainingConfig
from .metadata import CasinoMetadataManager

class CasinoBridge:
    """Main integration bridge between Dolphin and Casino of Life 
    
    Handles full lifecycle of game environment setup, agent training,
    and IR-compatible state management.
    """
    
    def __init__(self, program_id: Pubkey, game_name: str = 'Airstriker-Genesis'):
        self.program_id = program_id
        self.game_name = game_name
        self.env: Optional[RetroEnv] = None
        self.agent: Optional[DynamicAgent] = None
        self.reward_manager = RewardEvaluatorManager()
        self.game_state: Optional[CasinoGameState] = None
        self.metadata_manager = CasinoMetadataManager(program_id)
        self.action_mapper: Optional[ActionMapper] = None
        self.current_scenario: Optional[Dict] = None

    def initialize_env(self, 
                     state_name: str = 'tournament',
                     scenario_path: Optional[Path] = None) -> None:
        """Initialize game environment with IR-compatible state
        
        Args:
            state_name: Initial game state name
            scenario_path: Path to scenario JSON file
        """
        # Close any existing environment
        self.close()

        # Load scenario if provided
        if scenario_path:
            self.metadata_manager.load_scenario(scenario_path)
            with open(scenario_path) as f:
                self.current_scenario = json.load(f)
            state_name = self.current_scenario.get('initial_state', state_name)

        # Initialize environment
        self.env = RetroEnv(
            game=self.game_name,
            state=state_name,
            players=2,
            scenario=self.current_scenario
        )

        # Initialize action mapper with game controls
        game_controls = self.env.get_game_controls()
        self.action_mapper = ActionMapper(game_controls=game_controls, game=self.game_name)

        # Initialize game state with metadata
        self.game_state = CasinoGameState(
            version=1,
            authority=self.program_id,
            is_initialized=True
        )
        # Get metadata from metadata manager
        ir_metadata = self.metadata_manager.get_ir_metadata()
        self.game_state.metadata = ir_metadata['metadata']

    def create_agent(self, 
                    policy: str = 'PPO',
                    action_map: Optional[Dict] = None) -> None:
        """Create agent with IR-compatible configuration
        
        Args:
            policy: RL policy to use (PPO, A2C, DQN)
            action_map: Custom action mapping for game controls
        """
        if not self.env:
            raise RuntimeError("Environment not initialized")

        # Configure action mapping
        if action_map and self.action_mapper:
            self.action_mapper.load_mapping(action_map)
            self.env.set_action_mapper(self.action_mapper)

        # Create agent with scenario-specific rewards if available
        reward_evaluator = "default"
        if self.current_scenario:
            reward_evaluator = self.current_scenario.get('reward_system', 'default')
            
        self.agent = DynamicAgent(
            retro_api=self.env,  # Pass the environment as retro_api
            rl_algorithm=policy,  # Pass the policy as rl_algorithm
            training_params={
                'learning_rate': 0.0003,
                'frame_stack': 4,
                'use_lstm': True
            },
            reward_evaluators={self.game_name: self.reward_manager.get_evaluator(reward_evaluator)}
        )

    def train_agent(self, 
                  timesteps: int = 100000,
                  save_interval: int = 10000,
                  checkpoint_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Execute training with IR state tracking
        
        Args:
            timesteps: Total training timesteps
            save_interval: Steps between auto-saves
            checkpoint_dir: Directory for model checkpoints
        """
        if not self.agent or not self.game_state:
            raise RuntimeError("Agent/Environment not initialized")

        # Configure checkpoint saving
        callbacks = [self._update_ir_state]
        if checkpoint_dir:
            checkpoint_dir.mkdir(exist_ok=True)
            callbacks.append(
                self.agent.create_checkpoint_callback(
                    str(checkpoint_dir),
                    save_interval
                )
            )

        # Start training
        results = self.agent.train(
            timesteps=timesteps,
            callback=callbacks,
            progress_bar=True
        )

        # Save final state
        if checkpoint_dir:
            self.agent.save(checkpoint_dir / "final_model.zip")
            
        return results

    def _update_ir_state(self, locals_: Dict[str, Any], globals_: Dict[str, Any]) -> None:
        """Callback for updating IR-compatible game state"""
        if self.game_state:
            # Capture frame and rewards
            self.game_state.update_from_casino(
                frame=locals_.get('obs', b''),
                rewards=locals_.get('rewards', {})
            )
            
            # Update metadata with training progress
            self.game_state.metadata.update({
                'timestep': locals_.get('timestep', 0),
                'episode': locals_.get('episode', 0),
                'mean_reward': locals_.get('mean_reward', 0.0)
            })

    def close(self) -> None:
        """Close the environment and clean up resources"""
        if self.env:
            self.env.close()
            self.env = None
        if self.agent:
            self.agent = None
