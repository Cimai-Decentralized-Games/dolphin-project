import pytest
from pathlib import Path
from typing import Dict, Any
from dolphin.core.types import Pubkey
from dolphin.dolphin_games.casino_config import CasinoTrainingConfig

# Casino of Life test constants
CASINO_TEST_DIR = Path(__file__).parent.parent / "casino_test"
TEST_CASINO_PROGRAM_ID = "Casino111111111111111111111111111111111111"
TEST_GAME = "Airstriker-Genesis"  # Built-in ROM that comes with casino-of-life
TEST_STATE = "Level1"  # Default state for Airstriker-Genesis

@pytest.fixture
def test_program_id():
    """Provide a test program ID for Casino of Life tests"""
    return Pubkey(TEST_CASINO_PROGRAM_ID)

@pytest.fixture
def casino_test_dir():
    """Create a temporary directory for Casino of Life testing"""
    CASINO_TEST_DIR.mkdir(exist_ok=True)
    yield CASINO_TEST_DIR
    if CASINO_TEST_DIR.exists():
        import shutil
        shutil.rmtree(CASINO_TEST_DIR)

@pytest.fixture
def casino_test_config(test_program_id):
    """Provide test configuration for Casino of Life"""
    return CasinoTrainingConfig(
        program_id=test_program_id,
        game_name=TEST_GAME,  # Use Airstriker-Genesis
        scenario="test_scenario",
        state_name=TEST_STATE,  # Use Level1 state
        training_params={
            "policy": "PPO",
            "learning_rate": 0.001
        },
        metadata={
            "version": "1.0",
            "type": "test"
        }
    )

@pytest.fixture
def mock_casino_scenario(temp_test_dir) -> Dict[str, Any]:
    """Provide a mock scenario for testing"""
    metadata_path = temp_test_dir / "metadata.json"
    metadata_path.write_text('{"version": "1.0"}')

    return {
        "name": "Test Scenario",
        "metadata": {
            "difficulty": "normal",
            "players": 1,
            "mode": "training"
        },
        "game_files": {
            "rom": TEST_GAME,  # Use Airstriker-Genesis
            "state": TEST_STATE,  # Use Level1 state
            "metadata": str(metadata_path)
        }
    }
