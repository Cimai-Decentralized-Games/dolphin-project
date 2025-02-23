from dataclasses import dataclass, field
from typing import Any, Dict
from hashlib import sha256
from .types import Pubkey

@dataclass
class CasinoGameState:
    """Extended state for Casino of Life integration"""
    version: int
    authority: Pubkey
    is_initialized: bool
    raw_frame: bytes = b''
    reward_data: Dict[str, Any] = None
    agent_state: Dict[str, Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_from_casino(self, frame: bytes, rewards: Dict[str, Any]) -> None:
        """Update state from Casino environment"""
        self.raw_frame = frame
        self.reward_data = rewards or {}
        
    def to_ir_dict(self) -> Dict[str, Any]:
        """Convert to IR-serializable format"""
        return {
            'version': self.version,
            'authority': str(self.authority),
            'is_initialized': self.is_initialized,
            'frame_hash': self._hash_frame(),
            'rewards': self.reward_data,
            'metadata': self.metadata
        }
        
    def _hash_frame(self) -> str:
        """Generate frame hash for IR compatibility"""
        return sha256(self.raw_frame).hexdigest() if self.raw_frame else ''
