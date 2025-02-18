"""
Dolphin CLI for Solana development
Provides commands for initializing, building, and deploying Dolphin projects
"""

import os
import sys
import click
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
    try:
        # Validate program ID
        if not validate_program_id(program_id):
            raise ValidationError(f"Invalid program ID: {program_id}")
        
        # Create project
        project_dir = Path(name)
        if project_dir.exists():
            raise click.ClickException(f"Directory {name} already exists")
        
        click.echo(f"Creating new {template} project in {project_dir}...")
        DolphinCLI.init(name, program_id, template)
        click.echo(f"✨ Successfully created project {name}")
        
    except ValidationError as e:
        raise click.ClickException(str(e))
    except Exception as e:
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
@click.option('--cluster', default='devnet',
              type=click.Choice(['localnet', 'devnet', 'testnet', 'mainnet-beta']),
              help='Solana cluster to deploy to')
@click.option('--keypair', type=click.Path(exists=True),
              help='Path to deployer keypair')
def deploy(cluster: str, keypair: Optional[str]):
    """Deploy the built program to Solana"""
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
