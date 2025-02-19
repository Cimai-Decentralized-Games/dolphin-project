"""
Dolphin Program Templates

This module provides templates for different types of Solana programs.
Templates are used by the Dolphin CLI when initializing new projects.
"""

from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent

def get_template_path(template_name: str) -> Path:
    """Get the path to a template file
    
    Args:
        template_name: Name of the template ('basic', 'game', 'token', or 'nft')
        
    Returns:
        Path to the template file
        
    Raises:
        ValueError: If template_name is invalid
    """
    template_map = {
        'basic': TEMPLATES_DIR / 'basic_program.py',
        'game': TEMPLATES_DIR / 'game_program.py',
        'token': TEMPLATES_DIR / 'token_program.py',
        'nft': TEMPLATES_DIR / 'nft_program.py'
    }
    
    if template_name not in template_map:
        raise ValueError(
            f"Invalid template name: {template_name}. "
            f"Must be one of: {', '.join(template_map.keys())}"
        )
    
    return template_map[template_name]

def read_template(template_name: str) -> str:
    """Read the contents of a template file
    
    Args:
        template_name: Name of the template ('basic', 'game', 'token', or 'nft')
        
    Returns:
        The template file contents
        
    Raises:
        ValueError: If template_name is invalid
        FileNotFoundError: If template file is missing
    """
    template_path = get_template_path(template_name)
    
    if not template_path.exists():
        raise FileNotFoundError(
            f"Template file not found: {template_path}"
        )
    
    return template_path.read_text()

# List of available templates
TEMPLATES = ['basic', 'game', 'token', 'nft']

__all__ = ['get_template_path', 'read_template', 'TEMPLATES']
