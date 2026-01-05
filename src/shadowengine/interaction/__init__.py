"""
Interaction Engine

Input parsing, command handling, and hotspot management.
"""

from .parser import CommandParser, Command, CommandType
from .hotspot import Hotspot, HotspotType

__all__ = [
    'CommandParser', 'Command', 'CommandType',
    'Hotspot', 'HotspotType'
]
