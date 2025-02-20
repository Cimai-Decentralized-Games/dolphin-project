"""
Dolphin CLI for Solana development
Provides commands for initializing, building, and deploying Dolphin projects
"""

import os
import sys
import click
import shutil
from pathlib import Path
from typing import Optional

from .ir_gen import DolphinCLI
from .core.types import ValidationError
from .utils.validation import validate_program_id

DEFAULT_PROGRAM_LIB = "lib.rs"
DEFAULT_CONFIG = "Dolphin.toml"

def validate_project_structure():
    """Validates the current directory is a Dolphin project"""
    if not os.path.exists("Cargo.toml"):
        raise click.ClickException("Not a Dolphin project directory (Cargo.toml not found)")
    
    if not os.path.exists("src"):
        raise click.ClickException("src directory not found")

@click.group()
def cli():
    """Dolphin CLI - A framework for Solana program development"""
    pass

@cli.command()
@click.argument('name')
@click.argument('program_id')
@click.option('--template', default='basic',
              type=click.Choice(['basic', 'game', 'token', 'nft']),
              help='Project template to use')
def init(name: str, program_id: str, template: str):
    """Initialize a new Dolphin project
    
    NAME: Name of the project
    PROGRAM_ID: Solana program ID for deployment
    """
    # Validate program ID
    if not validate_program_id(program_id):
        raise ValidationError(f"Invalid program ID: {program_id}")
    
    # Validate template
    valid_templates = ['basic', 'game', 'token', 'nft']
    if template not in valid_templates:
        raise ValueError(f"Invalid template. Must be one of: {', '.join(valid_templates)}")

    # Create project
    project_dir = Path(name)
    if project_dir.exists():
        raise ValueError(f"Project directory {name} already exists")
    
    click.echo(f"Creating new {template} project in {project_dir}...")
    
    try:
            # Create project structure
            project_dir.mkdir(parents=True)
            (project_dir / "src").mkdir()
            (project_dir / "program").mkdir()
            (project_dir / "tests").mkdir()
            (project_dir / "client").mkdir()
            (project_dir / "client" / "src").mkdir(parents=True)
            
            # Create Cargo.toml
            cargo_content = f"""[package]
name = "{name}"
version = "0.1.0"
edition = "2021"

[dependencies]
anchor-lang = "0.30.1"
"""
            (project_dir / "Cargo.toml").write_text(cargo_content)
            
            # Create Anchor.toml
            anchor_content = f"""[features]
seeds = false

[programs.localnet]
{name} = "{program_id}"

[registry]
url = "https://anchor.projectserum.com"

[provider]
cluster = "localnet"
wallet = "~/.config/solana/id.json"
"""
            (project_dir / "Anchor.toml").write_text(anchor_content)
            
            # Create Python packaging config
            pyproject_content = """[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"
"""
            (project_dir / "pyproject.toml").write_text(pyproject_content)
            
            # Create setup.cfg
            setup_content = f"""[metadata]
name = {name}
version = 0.1.0
description = Dolphin program package
long_description = file: README.md
long_description_content_type = text/markdown

[options]
packages = find:
install_requires =
    dolphin
    anchorpy

[options.packages.find]
where = ./program
"""
            (project_dir / "setup.cfg").write_text(setup_content)

            # Create lib.rs
            lib_rs_content = f"""use anchor_lang::prelude::*;

declare_id!("{program_id}");

#[program]
pub mod {name} {{
    use super::*;
    
    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {{
        Ok(())
    }}
}}

#[derive(Accounts)]
pub struct Initialize {{}}
"""
            (project_dir / "src" / "lib.rs").write_text(lib_rs_content)
            
            # Create template-specific program file
            program_content = ""
            if template == "basic":
                program_content = f'''from dolphin.prelude import *

@program("{program_id}")
class {name.title()}Program:
    @account
    class Counter:
        authority: Pubkey
        count: u64
        
    @instruction
    def initialize(self, counter: Counter, authority: Signer):
        counter.authority = authority.key()
        counter.count = 0
        
    @instruction
    def increment(self, counter: Counter, authority: Signer):
        assert counter.authority == authority.key(), "Invalid authority"
        counter.count += 1
'''
            elif template == "game":
                program_content = f'''from dolphin.prelude import *

@program("{program_id}")
class {name.title()}Program:
    @account
    class GameState:
        authority: Pubkey
        player: Pubkey
        score: u64
        is_initialized: bool
        
    @instruction
    def initialize(self, state: GameState, authority: Signer):
        state.authority = authority.key()
        state.player = authority.key()
        state.score = 0
        state.is_initialized = True
        
    @instruction
    def update_score(self, state: GameState, authority: Signer, new_score: u64):
        assert state.authority == authority.key(), "Invalid authority"
        assert state.is_initialized, "Game not initialized"
        state.score = new_score
'''
            elif template == "token":
                program_content = f'''from dolphin.prelude import *

@program("{program_id}")
class {name.title()}Program:
    @account
    class TokenMint:
        authority: Pubkey
        supply: u64
        decimals: u8
        is_initialized: bool
        
    @instruction
    def initialize(self, mint: TokenMint, authority: Signer, decimals: u8):
        mint.authority = authority.key()
        mint.supply = 0
        mint.decimals = decimals
        mint.is_initialized = True
        
    @instruction
    def mint_to(self, mint: TokenMint, authority: Signer, amount: u64):
        assert mint.authority == authority.key(), "Invalid authority"
        assert mint.is_initialized, "Token not initialized"
        mint.supply += amount
'''
            elif template == "nft":
                program_content = f'''from dolphin.prelude import *

@program("{program_id}")
class {name.title()}Program:
    @account
    class NFTMint:
        authority: Pubkey
        metadata: Pubkey
        owner: Pubkey
        is_initialized: bool
        
    @instruction
    def initialize(self, nft: NFTMint, authority: Signer, metadata: Pubkey):
        nft.authority = authority.key()
        nft.metadata = metadata
        nft.owner = authority.key()
        nft.is_initialized = True
        
    @instruction
    def transfer(self, nft: NFTMint, authority: Signer, new_owner: Pubkey):
        assert nft.owner == authority.key(), "Invalid owner"
        assert nft.is_initialized, "NFT not initialized"
        nft.owner = new_owner
'''
            
            (project_dir / "program" / "lib.py").write_text(program_content)
            
            # Create test file
            test_content = f'''import pytest
from pathlib import Path
from dolphin.testing import ProgramTest

async def test_{name}():
    program = await ProgramTest.load("program/lib.py")
    # Add your tests here
'''
            (project_dir / "tests" / "test_program.py").write_text(test_content)
            
            # Create package.json
            package_content = '''{
  "name": "client",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@project-serum/anchor": "^0.26.0",
    "@solana/web3.js": "^1.87.6"
  }
}'''
            (project_dir / "client" / "package.json").write_text(package_content)
            
            click.echo(f"✨ Successfully created project {name}")
            
    except (ValidationError, ValueError) as e:
        if project_dir.exists():
            shutil.rmtree(project_dir)
        raise click.ClickException(str(e))
    except Exception as e:
        if project_dir.exists():
            shutil.rmtree(project_dir)
        raise click.ClickException(f"Failed to create project: {str(e)}")

@cli.command()
@click.option('--release/--debug', default=False,
              help='Build in release mode')
@click.option('--optimize/--no-optimize', default=True,
              help='Enable optimization passes')
def build(release: bool, optimize: bool):
    """Build the current Dolphin project"""
    try:
        validate_project_structure()
        
        click.echo("Building Dolphin project...")
        mode = "release" if release else "debug"
        DolphinCLI.build(mode=mode, optimize=optimize)
        click.echo("✨ Build completed successfully")
        
    except Exception as e:
        raise click.ClickException(f"Build failed: {str(e)}")

@cli.command()
@click.option('--cluster', default='localnet',
              type=click.Choice(['localnet', 'devnet', 'testnet', 'mainnet-beta']),
              help='Solana cluster to deploy to (default: localnet)')
@click.option('--keypair', type=click.Path(exists=True),
              help='Path to deployer keypair')
def deploy(cluster: str, keypair: Optional[str]):
    """Deploy the built program to Solana.
    
    By default deploys to localnet (test validator). Use --cluster to specify another network.
    """
    try:
        validate_project_structure()
        
        if not os.path.exists("target/deploy"):
            raise click.ClickException("No built program found. Run 'dolphin build' first")
        
        click.echo(f"Deploying to {cluster}...")
        DolphinCLI.deploy(cluster=cluster, keypair_path=keypair)
        click.echo("✨ Deployment completed successfully")
        
    except Exception as e:
        raise click.ClickException(f"Deployment failed: {str(e)}")

@cli.command()
def test():
    """Run project tests"""
    try:
        validate_project_structure()
        
        click.echo("Running tests...")
        DolphinCLI.test()
        click.echo("✨ Tests completed successfully")
        
    except Exception as e:
        raise click.ClickException(f"Tests failed: {str(e)}")

@cli.command()
def clean():
    """Clean build artifacts"""
    try:
        validate_project_structure()
        
        click.echo("Cleaning build artifacts...")
        DolphinCLI.clean()
        click.echo("✨ Clean completed successfully")
        
    except Exception as e:
        raise click.ClickException(f"Clean failed: {str(e)}")

def main():
    """Main entry point for the CLI"""
    try:
        cli()
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
