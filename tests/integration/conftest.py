"""Test configuration for Casino integration tests"""
import pytest
import os
import tempfile
from pathlib import Path
from typing import Dict, Any
from dolphin.core.types import Pubkey
from dolphin.dolphin_games.casino_config import CasinoTrainingConfig

# Test constants
TEST_CASINO_PROGRAM_ID = "Casino111111111111111111111111111111111111"
TEST_GAME = "Airstriker-Genesis"  # Built-in ROM that comes with casino-of-life
TEST_STATE = "Level1"  # Default state for Airstriker-Genesis

def pytest_configure(config):
    """Register custom marks"""
    config.addinivalue_line(
        "markers", "serial: mark test to run in serial (non-parallel)"
    )

@pytest.fixture
def test_program_id():
    """Provide a test program ID"""
    return Pubkey(TEST_CASINO_PROGRAM_ID)

@pytest.fixture
def temp_test_dir():
    """Provide a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def mock_casino_scenario(temp_test_dir) -> Dict[str, Any]:
    """Provide a mock scenario for testing"""
    return {
        "name": "Test Scenario",
        "metadata": {
            "difficulty": "normal",
            "players": 1,
            "mode": "training"
        },
        "game_files": {
            "rom": TEST_GAME,
            "state": TEST_STATE,
            "metadata": str(temp_test_dir / "metadata.json")
        }
    }

@pytest.fixture
def casino_test_config(test_program_id, temp_test_dir):
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

@pytest.fixture(autouse=True)
def setup_test_files(temp_test_dir):
    """Setup necessary test files"""
    # Create mock ROM file
    (temp_test_dir / "test_rom.bin").touch()
    # Create mock state file
    (temp_test_dir / "test_state.state").touch()
    # Create mock metadata file
    (temp_test_dir / "metadata.json").write_text('{"version": "1.0"}')
    
    yield
    
    # Cleanup is handled by temp_test_dir fixture
