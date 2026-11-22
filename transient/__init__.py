"""Transient shaping for drum-bus audio processing."""

from .shaper import (
    TransientError,
    apply_shape,
    attack_gain,
    detect_transients,
    envelope,
    shape_batch,
    shape_transients,
    soft_knee,
    validate,
)

__all__ = [
    "TransientError",
    "apply_shape",
    "attack_gain",
    "detect_transients",
    "envelope",
    "shape_batch",
    "shape_transients",
    "soft_knee",
    "validate",
]
