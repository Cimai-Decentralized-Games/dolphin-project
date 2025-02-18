"""Format specifications for Casino Pool NFT agents and game data"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..prelude import Pubkey, Amount, UnixTimestamp

@dataclass
class AgentMetadata:
    """Metadata for a game agent NFT"""
    name: str
    description: str
    image_uri: str
    external_url: Optional[str] = None
    attributes: List[Dict[str, Any]] = field(default_factory=list)
    symbol: str = "AGENT"
    seller_fee_basis_points: int = 500  # 5%
    
    def to_json(self) -> Dict[str, Any]:
        """Convert metadata to Metaplex JSON format"""
        return {
            "name": self.name,
            "description": self.description,
            "image": self.image_uri,
            "external_url": self.external_url,
            "attributes": self.attributes,
            "symbol": self.symbol,
            "seller_fee_basis_points": self.seller_fee_basis_points,
            "properties": {
                "files": [{"uri": self.image_uri, "type": "image/png"}],
                "category": "image",
                "creators": []  # To be filled by minting process
            }
        }

@dataclass
class AgentStats:
    """Performance statistics for a game agent"""
    total_games: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    total_earnings: Amount = 0
    last_game: Optional[UnixTimestamp] = None
    win_streak: int = 0
    best_win_streak: int = 0
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage"""
        if self.total_games == 0:
            return 0.0
        return (self.wins / self.total_games) * 100.0

@dataclass
class AgentState:
    """On-chain state for a game agent"""
    version: int = 1
    is_active: bool = True
    owner: Pubkey = field(default_factory=Pubkey.default)
    mint: Pubkey = field(default_factory=Pubkey.default)
    stats: AgentStats = field(default_factory=AgentStats)
    stake_amount: Amount = 0
    last_update: UnixTimestamp = field(default_factory=lambda: int(datetime.now().timestamp()))

@dataclass
class BettingPool:
    """Betting pool for agent matches"""
    pool_id: Pubkey
    agent_a: Pubkey
    agent_b: Pubkey
    total_stake: Amount
    odds_a: float  # e.g. 1.5 means 1.5x payout
    odds_b: float
    start_time: UnixTimestamp
    end_time: Optional[UnixTimestamp] = None
    winner: Optional[Pubkey] = None
    
    def calculate_payout(self, bet_amount: Amount, bet_on: Pubkey) -> Amount:
        """Calculate potential payout for a bet"""
        if bet_on == self.agent_a:
            return int(bet_amount * self.odds_a)
        elif bet_on == self.agent_b:
            return int(bet_amount * self.odds_b)
        raise ValueError("Invalid agent pubkey")

@dataclass
class GameConfig:
    """Configuration for a game program"""
    name: str
    version: str
    max_players: int
    min_stake: Amount
    max_stake: Amount
    game_duration: int  # in seconds
    commission_rate: float  # e.g. 0.05 for 5%
    allowed_tokens: List[Pubkey] = field(default_factory=list)
    
    def validate(self) -> bool:
        """Validate configuration parameters"""
        return (
            len(self.name) > 0 and
            self.max_players > 1 and
            self.min_stake > 0 and
            self.max_stake >= self.min_stake and
            self.game_duration > 0 and
            0 <= self.commission_rate <= 1
        )

@dataclass
class MatchResult:
    """Result of a game match between agents"""
    match_id: str
    agent_a: Pubkey
    agent_b: Pubkey
    winner: Optional[Pubkey]
    score_a: int
    score_b: int
    duration: int  # in seconds
    timestamp: UnixTimestamp
    replay_uri: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_draw(self) -> bool:
        """Check if match ended in a draw"""
        return self.winner is None and self.score_a == self.score_b

def create_agent_metadata(
    agent_name: str,
    game_name: str,
    win_rate: float,
    total_games: int,
    image_uri: str
) -> AgentMetadata:
    """Create metadata for a new agent NFT"""
    return AgentMetadata(
        name=f"{agent_name} - {game_name} Agent",
        description=f"A trained AI agent for {game_name} with {win_rate:.1f}% win rate over {total_games} games.",
        image_uri=image_uri,
        attributes=[
            {"trait_type": "Game", "value": game_name},
            {"trait_type": "Win Rate", "value": f"{win_rate:.1f}%"},
            {"trait_type": "Total Games", "value": total_games},
            {"trait_type": "Generation", "value": "1.0"}
        ]
    )
