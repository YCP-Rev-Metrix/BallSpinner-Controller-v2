import numpy as np
import pytest

from utils import bandpass_wavelet


def test_bandpass_constant():
    # constant input should be filtered to near-zero (no mid-band content)
    arr = np.ones(128)
    out = bandpass_wavelet(arr)
    assert out.shape == arr.shape
    assert np.allclose(out, 0, atol=1e-6)


def test_bandpass_nonzero():
    # a simple signal containing two sinusoids should not equal the input
    t = np.linspace(0, 1, 256)
    sig = np.sin(2 * np.pi * 5 * t) + 0.2 * np.sin(2 * np.pi * 50 * t)
    out = bandpass_wavelet(sig)
    # output should not be identical to original and should have smaller energy
    assert not np.allclose(out, sig)
    assert np.linalg.norm(out) < np.linalg.norm(sig)
