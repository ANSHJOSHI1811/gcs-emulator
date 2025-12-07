"""CLI package for GCS Emulator"""
from .compute_cli import ComputeCLI, handle_compute_command, parse_compute_args

__all__ = ['ComputeCLI', 'handle_compute_command', 'parse_compute_args']
