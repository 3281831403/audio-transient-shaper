"""Red tests for the transient-shaper exercise.

Every test calls at least one public function from ``transient.shaper``.  All
eight public functions are stubs, so the initial suite has exactly 15 failures
and no collection, import, or syntax errors.
"""

import pytest

from transient.shaper import (
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


def test_defect_01_envelope_tracks_peak_not_mean():
    """An isolated peak must survive the envelope instead of being averaged."""
    samples = [0.0, 0.0, 0.8, 0.0, 0.0]
    env = envelope(
        samples,
        attack_ms=0.0,
        release_ms=100.0,
        sample_rate=1000.0,
    )

    assert len(env) == len(samples)
    assert env[2] == pytest.approx(0.8, abs=1e-6)
    assert env[3] > 0.7
    assert env[4] > 0.6


def test_defect_02_attack_and_release_use_distinct_time_constants():
    """A fast attack and a slow release must not share one time constant."""
    samples = [0.0] * 4 + [1.0] * 40

    fast_attack = envelope(samples, 1.0, 100.0, 1000.0)
    slow_attack = envelope(samples, 20.0, 100.0, 1000.0)

    assert fast_attack[8] > slow_attack[8]
    assert fast_attack[50] > 0.8
    assert fast_attack[50] < 1.0 + 1e-6


def test_defect_03_detection_uses_relative_rise_not_absolute_threshold():
    """Quiet and loud copies of one performance must detect the same onsets."""
    loud = [0.0, 0.0, 0.8, 0.7, 0.1, 0.0, 0.6, 0.5, 0.0]
    quiet = [sample * 0.1 for sample in loud]

    assert detect_transients(loud, 0.5) == [2, 6]
    assert detect_transients(quiet, 0.5) == [2, 6]


def test_defect_04_gain_segment_expands_to_width():
    """An attack anchor must cover a width-wide segment, not one sample."""
    samples = [0.5] * 9
    gains = attack_gain(samples, transients=[4], amount=0.5)

    assert gains[3] == pytest.approx(1.0, abs=1e-6)
    assert gains[4] == pytest.approx(1.5, abs=1e-6)

    shaped = apply_shape(samples, gains, width=3)
    assert shaped[3:6] == pytest.approx([0.75, 0.75, 0.75], abs=1e-6)
    assert shaped[2] == pytest.approx(0.5, abs=1e-6)
    assert shaped[6] == pytest.approx(0.5, abs=1e-6)


def test_defect_05_soft_knee_removes_gain_jump():
    """Gain above the knee must bend continuously instead of jumping to 1."""
    assert soft_knee(0.4, 0.5) == pytest.approx(0.4, abs=1e-6)
    at_knee = soft_knee(0.5, 0.5)
    above = soft_knee(1.0, 0.5)

    assert at_knee == pytest.approx(0.5, abs=1e-6)
    assert 0.5 < above < 1.0
    assert above - at_knee < 0.5
    assert soft_knee(0.5 + 1e-9, 0.5) == pytest.approx(0.5, abs=1e-6)


def test_defect_06_apply_shape_clamps_output_peak():
    """A large gain must be clamped at full scale rather than clip the output."""
    output = apply_shape([0.8, -0.9], [2.0, 3.0], width=1)

    assert output == pytest.approx([1.0, -1.0], abs=1e-6)


def test_defect_07_sensitivity_range_is_validated():
    """An out-of-range sensitivity must be reported and rejected."""
    issues = validate([0.1, 0.2], sensitivity=1.5, amount=0.0)

    assert any("sensitivity" in issue.lower() for issue in issues)
    with pytest.raises(TransientError):
        detect_transients([0.1, 0.2], sensitivity=1.5)


def test_defect_08_amount_range_is_validated():
    """An amount above 1 must not produce an invalid or inverted gain."""
    issues = validate([0.1, 0.2], sensitivity=0.5, amount=1.5)

    assert any("amount" in issue.lower() for issue in issues)
    with pytest.raises(TransientError):
        attack_gain([0.1, 0.2], transients=[0], amount=1.5)


def test_defect_09_batch_isolates_tracks_and_rolls_back():
    """Each track needs its own envelope, and an invalid track aborts all."""
    tracks = [
        [0.0, 0.0, 0.8, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0],
    ]
    config = {
        "amount": 0.5,
        "width_ms": 1.0,
        "sample_rate": 1000.0,
        "sensitivity": 0.5,
    }

    result = shape_batch(tracks, config)
    quiet = result["tracks"][1]

    quiet_transients = detect_transients(tracks[1], 0.5)
    quiet_gains = attack_gain(tracks[1], quiet_transients, 0.5)
    expected_quiet = apply_shape(tracks[1], quiet_gains, width=1)
    assert quiet == pytest.approx(expected_quiet, abs=1e-6)

    before = [list(track) for track in tracks]
    with pytest.raises(TransientError):
        shape_batch([tracks[0], []], config)
    assert tracks == before


def test_defect_10_zero_width_is_rejected():
    """A zero width must raise before a division by zero can happen."""
    with pytest.raises(TransientError):
        shape_transients([0.2] * 8, amount=0.5, width_ms=0.0, sample_rate=1000.0)


def test_amount_zero_returns_input_unchanged():
    """Zero amount is an exact identity within the stricter 1e-9 tolerance."""
    samples = [0.0, 0.25, -0.5, 0.75, 0.0]

    shaped = shape_transients(samples, amount=0.0, width_ms=5.0, sample_rate=1000.0)

    assert len(shaped) == len(samples)
    assert shaped == pytest.approx(samples, abs=1e-9)


def test_detector_returns_empty_for_steady_signal():
    """A constant signal has no rising transient onset."""
    assert detect_transients([0.2] * 12, sensitivity=0.5) == []


def test_empty_input_returns_empty():
    """Empty audio returns empty results instead of raising."""
    assert envelope([], attack_ms=5.0, release_ms=50.0, sample_rate=1000.0) == []
    assert detect_transients([], sensitivity=0.5) == []
    assert shape_transients([], amount=0.4, width_ms=5.0, sample_rate=1000.0) == []


def test_amount_above_one_raises():
    """The overall shaper must reject an amount above the documented range."""
    with pytest.raises(TransientError):
        shape_transients([0.2, 0.3], amount=1.5, width_ms=5.0, sample_rate=1000.0)


def test_batch_success_preserves_order_and_values():
    """A successful batch keeps track order, lengths, values, and its inputs."""
    tracks = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5],
        [0.0, 0.2, 0.4, 0.6],
    ]
    before = [list(track) for track in tracks]
    config = {
        "amount": 0.0,
        "width_ms": 5.0,
        "sample_rate": 1000.0,
        "sensitivity": 0.5,
    }

    result = shape_batch(tracks, config)
    output = result["tracks"]

    assert [len(track) for track in output] == [3, 2, 4]
    for actual, expected in zip(output, before):
        assert actual == pytest.approx(expected, abs=1e-6)
    assert tracks == before
