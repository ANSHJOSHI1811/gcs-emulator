"""CLI package"""
# Re-export cli function from parent module
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from ..cli import cli
    __all__ = ['cli']
except ImportError:
    pass
