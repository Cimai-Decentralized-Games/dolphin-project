"""Integration tests for Casino of Life functionality"""
import pytest
from pathlib import Path
import json
from dolphin.dolphin_games.casino_bridge import CasinoBridge
from dolphin.dolphin_games.retro_support import create_casino_env

# Use the built-in Airstriker-Genesis ROM
GAME_NAME = "Airstriker-Genesis"
GAME_STATE = "Level1"

def test_casino_config_integration(casino_test_config):
    """Test Casino of Life configuration integration"""
    # Verify Casino of Life specific configuration
    ir_data = casino_test_config.to_ir()
    assert ir_data['game'] == GAME_NAME
    assert ir_data['scenario'] == "test_scenario"
    assert ir_data['params']['policy'] == "PPO"
    assert ir_data['metadata']['version'] == "1.0"
    assert ir_data['metadata']['type'] == "test"

def test_casino_bridge_initialization(test_program_id, temp_test_dir, mock_casino_scenario):
    """Test Casino bridge initialization and environment setup"""
    # Create scenario file
    scenario_path = temp_test_dir / "scenario.json"
    with open(scenario_path, 'w') as f:
        json.dump(mock_casino_scenario, f)
    
    # Initialize bridge with Airstriker-Genesis
    bridge = CasinoBridge(test_program_id)  # Uses Airstriker-Genesis by default
    bridge.initialize_env(state_name=GAME_STATE, scenario_path=scenario_path)
    
    # Verify environment setup
    assert bridge.env is not None
    assert bridge.game_state is not None
    
    # Verify metadata loading
    metadata = bridge.metadata_manager.get_ir_metadata()
    assert metadata['program_id'] == str(test_program_id)
    assert 'metadata' in metadata
    assert metadata['metadata']['difficulty'] == "normal"
    assert metadata['metadata']['players'] == 1

def test_casino_agent_creation(test_program_id, temp_test_dir, mock_casino_scenario):
    """Test agent creation and configuration"""
    # Setup bridge with environment
    bridge = CasinoBridge(test_program_id)  # Uses Airstriker-Genesis by default
    scenario_path = temp_test_dir / "scenario.json"
    with open(scenario_path, 'w') as f:
        json.dump(mock_casino_scenario, f)
    
    bridge.initialize_env(state_name=GAME_STATE, scenario_path=scenario_path)
    
    # Create agent with specific policy
    bridge.create_agent(policy='PPO')
    
    # Verify agent setup
    assert bridge.agent is not None
    assert bridge.agent.policy == 'PPO'
    
    # Test training callback
    test_obs = b'test_frame'
    test_rewards = {'score': 100}
    bridge._update_ir_state({'obs': test_obs, 'rewards': test_rewards}, {})
    
    # Verify state updates
    assert bridge.game_state.raw_frame == test_obs
    ir_state = bridge.game_state.to_ir_dict()
    assert 'metadata' in ir_state
    assert 'timestep' in ir_state['metadata']

def test_casino_environment_creation(test_program_id, temp_test_dir, mock_casino_scenario):
    """Test casino environment creation and configuration"""
    # Create test scenario
    scenario_path = temp_test_dir / "scenario.json"
    with open(scenario_path, 'w') as f:
        json.dump(mock_casino_scenario, f)
    
    # Create environment with Airstriker-Genesis
    env = create_casino_env(
        program_id=test_program_id,
        game_name=GAME_NAME,
        state_name=GAME_STATE,
        scenario_path=scenario_path
    )
    
    # Verify environment setup
    assert env is not None
    assert env.game_state is not None
    assert env.metadata['difficulty'] == "normal"
    assert env.metadata['players'] == 1
    
    # Test environment reset
    observation = env.reset()
    assert observation is not None
    
    # Verify game state
    assert env.game_state.is_initialized
    assert env.game_state.authority == test_program_id

def test_casino_metadata_integration(test_program_id, casino_test_config, temp_test_dir):
    """Test metadata integration between Casino of Life and Dolphin"""
    # Create scenario file
    scenario_path = temp_test_dir / "scenario.json"
    with open(scenario_path, 'w') as f:
        json.dump({
            "name": "Test Scenario",
            "metadata": casino_test_config.metadata,
            "game_files": {
                "rom": GAME_NAME,
                "state": GAME_STATE
            }
        }, f)
    
    bridge = CasinoBridge(test_program_id)  # Uses Airstriker-Genesis by default
    bridge.initialize_env(
        state_name=GAME_STATE,
        scenario_path=scenario_path
    )
    
    # Verify metadata integration
    metadata = bridge.metadata_manager.get_ir_metadata()
    assert metadata['program_id'] == str(test_program_id)
    
    # Test IR state conversion
    ir_state = bridge.game_state.to_ir_dict()
    assert ir_state['metadata']['version'] == "1.0"
    assert ir_state['metadata']['type'] == "test"
