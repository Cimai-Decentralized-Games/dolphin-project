"""Test suite for Dolphin project initialization"""

import pytest
import os
from pathlib import Path
from dolphin.cli import DolphinCLI
import json

def verify_project_structure(project_dir: Path):
    """Validate core project structure"""
    required_paths = [
        project_dir / "Cargo.toml",
        project_dir / "Anchor.toml",
        project_dir / "pyproject.toml",
        project_dir / "setup.cfg",
        project_dir / "src" / "lib.rs",
        project_dir / "program" / "lib.py",
        project_dir / "tests" / "test_program.py",
        project_dir / "client" / "package.json"
    ]
    
    for path in required_paths:
        assert path.exists(), f"Missing required path: {path}"
        assert path.stat().st_size > 0, f"Empty file: {path}"

class BaseTestInit:
    """Base class for initialization tests with common assertions"""
    
    TEMPLATE = "basic"
    
    def verify_template_specifics(self, project_dir: Path):
        """Template-specific validations"""
        lib_py = project_dir / "program" / "lib.py"
        content = lib_py.read_text()
        
        if self.TEMPLATE == "basic":
            assert "class Counter:" in content
            assert "authority: Pubkey" in content
        elif self.TEMPLATE == "game":
            assert "class GameState:" in content
            assert "player: Pubkey" in content
        elif self.TEMPLATE == "token":
            assert "class TokenMint:" in content
            assert "supply: u64" in content
        elif self.TEMPLATE == "nft":
            assert "class NFTMint:" in content
            assert "metadata: Pubkey" in content

class TestBasicProjectInitialization(BaseTestInit):
    """Test basic project initialization"""

    def test_project_creation(self, init_test_context):
        """Test core project structure"""
        base_dir = init_test_context["base_dir"]
        project_name = "test_program"
        program_id = init_test_context["program_id"]

        original_cwd = Path.cwd()
        try:
            os.chdir(base_dir)
            DolphinCLI.init(project_name, program_id, template=self.TEMPLATE, base_dir=base_dir)
            project_dir = base_dir / project_name
            
            verify_project_structure(project_dir)
            self.verify_template_specifics(project_dir)
            
            # Verify config files
            cargo_toml = project_dir / "Cargo.toml"
            assert f'name = "{project_name}"' in cargo_toml.read_text()
            
            anchor_toml = project_dir / "Anchor.toml"
            assert program_id in anchor_toml.read_text()
            
            # Verify Python packaging config
            pyproject = project_dir / "pyproject.toml"
            assert "[build-system]" in pyproject.read_text()
            
            setup_cfg = project_dir / "setup.cfg"
            assert "[metadata]" in setup_cfg.read_text()

        finally:
            os.chdir(original_cwd)

    def test_build_process(self, init_test_context):
        """Test building the initialized project"""
        base_dir = init_test_context["base_dir"]
        project_name = "test_program"
        program_id = init_test_context["program_id"]
        
        original_cwd = Path.cwd()
        try:
            # First initialize the project
            DolphinCLI.init(project_name, program_id, template=self.TEMPLATE, base_dir=base_dir)
            # Then change directory and build
            os.chdir(base_dir / project_name)
            DolphinCLI.build()
            
            # Verify IR generation
            ir_path = Path("target") / "ir.json"
            assert ir_path.exists(), "IR file not generated"
            
            # Validate IR structure
            with open(ir_path) as f:
                ir_data = json.load(f)
                assert "program_id" in ir_data
                assert "accounts" in ir_data
                assert "instructions" in ir_data

        finally:
            os.chdir(original_cwd)

class TestGameProjectInitialization(BaseTestInit):
    """Test initializing a game project template"""
    TEMPLATE = "game"

    def test_project_creation(self, init_test_context):
        base_dir = init_test_context["base_dir"]
        project_name = "test_program"
        program_id = init_test_context["program_id"]

        original_cwd = Path.cwd()
        try:
            os.chdir(base_dir)
            DolphinCLI.init(project_name, program_id, template=self.TEMPLATE, base_dir=base_dir)
            project_dir = base_dir / project_name
            
            verify_project_structure(project_dir)
            self.verify_template_specifics(project_dir)

            # Verify game-specific features
            lib_py = project_dir / "program" / "lib.py"
            content = lib_py.read_text()
            assert "score: u64" in content
            assert "is_initialized: bool" in content

        finally:
            os.chdir(original_cwd)

class TestTokenProjectInitialization(BaseTestInit):
    """Test initializing a token project template"""
    TEMPLATE = "token"

    def test_project_creation(self, init_test_context):
        base_dir = init_test_context["base_dir"]
        project_name = "test_program"
        program_id = init_test_context["program_id"]

        original_cwd = Path.cwd()
        try:
            os.chdir(base_dir)
            DolphinCLI.init(project_name, program_id, template=self.TEMPLATE, base_dir=base_dir)
            project_dir = base_dir / project_name
            
            verify_project_structure(project_dir)
            self.verify_template_specifics(project_dir)

            # Verify token-specific features
            lib_py = project_dir / "program" / "lib.py"
            content = lib_py.read_text()
            assert "mint_to" in content
            assert "checked_add" in content

        finally:
            os.chdir(original_cwd)

class TestNFTProjectInitialization(BaseTestInit):
    """Test initializing an NFT project template"""
    TEMPLATE = "nft"

    def test_project_creation(self, init_test_context):
        base_dir = init_test_context["base_dir"]
        project_name = "test_program"
        program_id = init_test_context["program_id"]

        original_cwd = Path.cwd()
        try:
            os.chdir(base_dir)
            DolphinCLI.init(project_name, program_id, template=self.TEMPLATE, base_dir=base_dir)
            project_dir = base_dir / project_name
            
            verify_project_structure(project_dir)
            self.verify_template_specifics(project_dir)

            # Verify NFT-specific features
            lib_py = project_dir / "program" / "lib.py"
            content = lib_py.read_text()
            assert "transfer" in content
            assert "metadata: Pubkey" in content

        finally:
            os.chdir(original_cwd)

def test_invalid_template_handling(init_test_context):
    """Test handling of invalid template selection"""
    base_dir = init_test_context["base_dir"]
    project_name = "test_program"
    program_id = init_test_context["program_id"]
    
    with pytest.raises(ValueError, match="Invalid template"):
        DolphinCLI.init(project_name, program_id, template="invalid_template")

def test_duplicate_project_handling(init_test_context):
    """Test handling of duplicate project creation"""
    base_dir = init_test_context["base_dir"]
    project_name = "test_program"
    program_id = init_test_context["program_id"]
    
    original_cwd = Path.cwd()
    try:
        os.chdir(base_dir)
        
        # Create first project
        DolphinCLI.init(project_name, program_id, template="basic", base_dir=base_dir)
        
        # Attempt to create duplicate project
        with pytest.raises(ValueError, match="Project directory already exists"):
            DolphinCLI.init(project_name, program_id, template="basic", base_dir=base_dir)
            
    finally:
        os.chdir(original_cwd)

def test_invalid_program_id_handling(init_test_context):
    """Test handling of invalid program ID"""
    base_dir = init_test_context["base_dir"]
    project_name = "test_program"
    invalid_program_id = "invalid_program_id"
    
    with pytest.raises(ValueError, match="Invalid program ID"):
        DolphinCLI.init(project_name, invalid_program_id, template="basic")
