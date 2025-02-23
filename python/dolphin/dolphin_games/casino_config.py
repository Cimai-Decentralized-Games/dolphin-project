from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path
from ..core.types import Pubkey

class CasinoTrainingConfig(BaseModel):
    """IR-compatible training configuration"""
    program_id: Pubkey
    game_name: str
    scenario: str
    state_name: str
    training_params: Dict[str, Any]
    metadata: Dict[str, str]
    
    def to_ir(self) -> Dict[str, Any]:
        return {
            "program_id": str(self.program_id),
            "game": self.game_name,
            "scenario": self.scenario,
            "state": self.state_name,
            "params": self.training_params,
            "metadata": self.metadata
        }

    # New attributes for Casino of Life integration
    casino_scenario_path: Optional[Path] = None
    casino_metadata_path: Optional[Path] = None

    def get_casino_config(self) -> Dict[str, Any]:
        """Return the Casino of Life specific configuration."""
        return {
            "casino_scenario_path": str(self.casino_scenario_path) if self.casino_scenario_path else None,
            "casino_metadata_path": str(self.casino_metadata_path) if self.casino_metadata_path else None,
        }
