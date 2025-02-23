"""Integration tests for Hello World Game example"""
import pytest
from pathlib import Path
import json
import inspect
import sys
import os
import gc
from casino_of_life import RetroEnv
from casino_of_life.agents.dynamic_agent import DynamicAgent

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import from examples
from examples.hello_world_game import HelloWorldGame, setup_game_environment, train_game_agent
from dolphin.core.types import Pubkey
from dolphin.ir_gen import IRGenerator
from dolphin.dolphin_games.casino_bridge import CasinoBridge

# Test constants
TEST_PROGRAM_ID = "HeLLo777777777777777777777777777777777777777"
GAME_NAME = "Airstriker-Genesis"
GAME_STATE = "Level1"

@pytest.fixture(scope="function")
def temp_game_dir(tmp_path):
    """Create a temporary directory for game files"""
    game_dir = tmp_path / "hello_world_game"
    game_dir.mkdir()
    # Create checkpoints directory
    (game_dir / "checkpoints").mkdir()
    return game_dir

@pytest.fixture(scope="function")
def mock_game_scenario(temp_game_dir):
    """Create a mock game scenario for testing"""
    metadata_path = temp_game_dir / "metadata.json"
    metadata_path.write_text('{"version": "1.0"}')

    scenario = {
        "name": "Test Scenario",
        "metadata": {
            "version": "1.0",
            "type": "test",
            "difficulty": "normal",
            "players": 1,
            "mode": "training"
        },
        "game_files": {
            "rom": GAME_NAME,
            "state": GAME_STATE,
            "metadata": str(metadata_path)
        }
    }
    
    scenario_path = temp_game_dir / "scenario.json"
    with open(scenario_path, "w") as f:
        json.dump(scenario, f)
        
    return scenario_path

@pytest.fixture(scope="function")
def bridge(temp_game_dir):
    """Create and cleanup CasinoBridge instance"""
    os.chdir(temp_game_dir)
    bridge = CasinoBridge(Pubkey(TEST_PROGRAM_ID))  # Create bridge directly
    yield bridge
    bridge.close()  # Use CasinoBridge's close method
    gc.collect()

def test_hello_world_ir_generation():
    """Test IR generation for Hello World Game"""
    # Get source code from the HelloWorldGame class
    source_code = inspect.getsource(HelloWorldGame)
    
    # Generate IR
    ir_generator = IRGenerator(source_code)
    program_ir = ir_generator.generate()
    
    # Verify program structure
    assert program_ir.name == "HelloWorldGame"
    assert program_ir.program_id == TEST_PROGRAM_ID
    
    # Verify accounts
    assert len(program_ir.accounts) == 1
    game_state = program_ir.accounts[0]
    assert game_state.name == "GameState"
    assert len(game_state.fields) == 6
    
    # Verify field types
    field_types = {field.name: field.type_name for field in game_state.fields}
    assert field_types["authority"] == "Pubkey"
    assert field_types["player"] == "Pubkey"
    assert field_types["score"] == "u64"
    assert field_types["high_score"] == "u64"
    assert field_types["last_play"] == "i64"
    assert field_types["is_initialized"] == "bool"
    
    # Verify instructions
    assert len(program_ir.instructions) == 2
    assert {instr.name for instr in program_ir.instructions} == {"initialize", "update_score"}

@pytest.mark.serial
def test_hello_world_game_environment(bridge, mock_game_scenario):
    """Test game environment setup with Casino integration"""
    # Initialize environment
    bridge.initialize_env(state_name=GAME_STATE, scenario_path=mock_game_scenario)
    
    try:
        # Verify environment setup
        assert bridge.env is not None
        assert isinstance(bridge.env, RetroEnv)  # Verify correct environment type
        assert bridge.game_state is not None
        assert bridge.metadata_manager is not None
        
        # Verify metadata
        metadata = bridge.metadata_manager.get_ir_metadata()
        assert metadata["metadata"]["version"] == "1.0"
        assert metadata["metadata"]["type"] == "test"
        assert metadata["metadata"]["difficulty"] == "normal"
    finally:
        bridge.close()  # Use CasinoBridge's close method

@pytest.mark.serial
def test_hello_world_agent_training(bridge, mock_game_scenario):
    """Test agent training integration"""
    # Initialize environment
    bridge.initialize_env(state_name=GAME_STATE, scenario_path=mock_game_scenario)
    
    try:
        # Create and train agent
        bridge.create_agent(policy='PPO')
        
        # Verify agent setup
        assert bridge.agent is not None
        assert isinstance(bridge.agent, DynamicAgent)  # Verify correct agent type
        assert bridge.agent.policy == 'PPO'
        
        # Test short training run
        results = train_game_agent(bridge, training_steps=1000)
        
        # Verify training results
        assert isinstance(results, dict)
        assert 'final_score' in results or 'high_score' in results
    finally:
        bridge.close()  # Use CasinoBridge's close method

@pytest.mark.serial
def test_hello_world_full_integration(bridge, mock_game_scenario):
    """Test full integration of smart contract and game components"""
    # 1. Generate and verify IR
    source_code = inspect.getsource(HelloWorldGame)
    ir_generator = IRGenerator(source_code)
    program_ir = ir_generator.generate()
    
    try:
        # 2. Setup game environment
        bridge.initialize_env(state_name=GAME_STATE, scenario_path=mock_game_scenario)
        
        # 3. Create and train agent
        bridge.create_agent(policy='PPO')
        results = train_game_agent(bridge, training_steps=1000)
        
        # 4. Verify game state updates
        test_score = 100
        # Update score through reward data
        bridge.game_state.reward_data = {'score': test_score}
        bridge.game_state.metadata.update({
            'score': test_score,
            'high_score': test_score
        })
        
        # Convert to IR and verify
        ir_state = bridge.game_state.to_ir_dict()
        assert ir_state['metadata']['version'] == "1.0"
        assert ir_state['rewards']['score'] == test_score
        assert ir_state['metadata']['score'] == test_score
        assert ir_state['metadata']['high_score'] == test_score
    finally:
        bridge.close()  # Use CasinoBridge's close method
