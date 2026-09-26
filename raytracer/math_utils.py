"""
Mathematical and vector utility functions for ray tracing.
Provides vectorized operations supporting both single vectors (shape: (3,))
and ray batches (shape: (..., 3)).
"""

import numpy as np


def normalize(v: np.ndarray, axis: int = -1, eps: float = 1e-8) -> np.ndarray:
    """
    Normalizes vector(s) along a specified axis.
    
    Args:
        v: Array of vectors.
        axis: Axis along which vector coordinates lie.
        eps: Small epsilon to prevent division by zero.
        
    Returns:
        Unit-length vector(s) with identical shape.
    """
    norm = np.linalg.norm(v, axis=axis, keepdims=True)
    norm = np.maximum(norm, eps)
    return v / norm


def dot(a: np.ndarray, b: np.ndarray, axis: int = -1, keepdims: bool = False) -> np.ndarray:
    """
    Vectorized dot product along the specified axis.
    """
    return np.sum(a * b, axis=axis, keepdims=keepdims)


def cross(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Cross product of two 3D vectors.
    """
    return np.cross(a, b)


def reflect(d: np.ndarray, n: np.ndarray) -> np.ndarray:
    """
    Calculates the ideal specular reflection vector of incident ray direction 'd'
    about surface normal 'n'.
    
    Formula: R = d - 2 * (d . n) * n
    
    Args:
        d: Incident ray direction (pointing towards the surface).
        n: Surface normal unit vector (pointing outwards).
        
    Returns:
        Reflected ray direction unit vector.
    """
    return d - 2.0 * dot(d, n, keepdims=True) * n


def clamp(val: np.ndarray, min_val: float = 0.0, max_val: float = 1.0) -> np.ndarray:
    """
    Clamps array values within [min_val, max_val].
    """
    return np.clip(val, min_val, max_val)
