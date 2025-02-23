from typing import Dict, Any, Optional, Union
import numpy as np
import json
from pathlib import Path
from casino_of_life.game_environments.retro_env_loader import RetroEnv
from casino_of_life.client_bridge import RewardEvaluatorManager
from ..core.types import Pubkey
from ..core.casino_types import CasinoGameState

class RetroGameWrapper(RetroEnv):
    """IR-compatible Retro environment for Dolphin integration (Updated)
    
    Handles state management, scenario loading, and IR-compatible data conversion.
    """
    
    def __init__(
        self,
        program_id: Pubkey,
        game_name: str,
        state_name: Optional[str] = None,
        scenario_path: Optional[Path] = None,
        **kwargs
    ):
        super().__init__(game=game_name, state=state_name)
        self.program_id = program_id
        self.scenario_data = self._load_scenario(scenario_path) if scenario_path else {}
        self._init_game_state()
        self.reward_manager = RewardEvaluatorManager()
        self.current_frame_hash: str = ""

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get scenario metadata"""
        return self.scenario_data.get('metadata', {})

    def _load_scenario(self, scenario_path: Optional[Path]) -> Dict[str, Any]:
        """Load and validate scenario configuration"""
        if not scenario_path:
            return {}
            
        with open(scenario_path) as f:
            scenario = json.load(f)
            
        # Basic validation
        required = ['name', 'metadata', 'game_files']
        if not all(key in scenario for key in required):
            raise ValueError("Invalid scenario format - missing required fields")
            
        return scenario

    def _init_game_state(self) -> None:
        """Initialize IR-compatible game state"""
        self.game_state = CasinoGameState(
            version=1,
            authority=self.program_id,
            is_initialized=True,
            metadata=self.metadata
        )

    def step(self, action: np.ndarray) -> tuple:
        """Wrap step with IR state updates and scenario tracking"""
        obs, rew, done, info = super().step(action)
        self._update_ir_state(obs, info)
        
        # Add scenario-specific info to step results
        scenario_info = {
            'frame_hash': self.current_frame_hash,
            'scenario': self.scenario_data.get('name', ''),
            'objectives': self.scenario_data.get('objectives', [])
        }
        info.update(scenario_info)
        
        return obs, rew, done, info

    def _update_ir_state(self, frame: np.ndarray, info: Dict[str, Any]) -> None:
        """Convert frame and scenario data to IR-compatible format"""
        # Process scenario-specific rewards if available
        scenario_rewards = info.get('scenario_rewards', {})
        reward_components = {
            'total': info.get('reward', 0),
            'components': info.get('rewards', {}),
            'scenario': scenario_rewards
        }
        
        # Update game state with frame and processed rewards
        frame_bytes = frame.tobytes()
        self.game_state.update_from_casino(
            frame=frame_bytes,
            rewards=reward_components
        )
        self.current_frame_hash = self.game_state._hash_frame()

def create_retro_game(
    game_name: str,
    program_id: Pubkey,
    state_name: Optional[str] = None,
    scenario_path: Optional[Path] = None
) -> RetroGameWrapper:
    """Create IR-ready Retro game environment with scenario support"""
    return RetroGameWrapper(
        program_id=program_id,
        game_name=game_name,
        state_name=state_name,
        scenario_path=scenario_path
    )

# Alias for backward compatibility
create_casino_env = create_retro_game
