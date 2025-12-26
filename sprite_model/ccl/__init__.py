"""
CCL (Connected Component Labeling) Module
==========================================

CCL-based sprite extraction and processing for irregular sprite collections.
Extracted from monolithic SpriteModel for better separation of concerns and testability.
"""

from .ccl_operations import CCLOperations

__all__ = ['CCLOperations']
