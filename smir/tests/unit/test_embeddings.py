"""Unit-тесты face-worker embeddings."""
from __future__ import annotations

import numpy as np
import pytest

from smir_face.embeddings import (
    PATCH_SIZE,
    cosine_similarity,
    is_consented,
    match_consented_name,
)


def test_cosine_identical():
    v = np.random.rand(PATCH_SIZE * PATCH_SIZE).astype(np.float32)
    v /= np.linalg.norm(v)
    assert cosine_similarity(v, v) == pytest.approx(1.0, abs=1e-5)


def test_is_consented_match():
    v = np.ones(PATCH_SIZE * PATCH_SIZE, dtype=np.float32)
    v /= np.linalg.norm(v)
    assert is_consented(v, [v.copy()], threshold=0.99)


def test_match_consented_name():
    v = np.ones(PATCH_SIZE * PATCH_SIZE, dtype=np.float32)
    v /= np.linalg.norm(v)
    faces = [{"embedding": v.tolist(), "display_name": "Иван И."}]
    assert match_consented_name(v, faces, threshold=0.99) == "Иван И."


def test_match_consented_name_miss():
    a = np.zeros(PATCH_SIZE * PATCH_SIZE, dtype=np.float32)
    a[0] = 1.0
    b = np.zeros(PATCH_SIZE * PATCH_SIZE, dtype=np.float32)
    b[1] = 1.0
    faces = [{"embedding": b.tolist(), "display_name": "Другой"}]
    assert match_consented_name(a, faces, threshold=0.85) is None


def test_match_consented_name_multi_template():
    a = np.zeros(PATCH_SIZE * PATCH_SIZE, dtype=np.float32)
    a[0] = 1.0
    b = np.zeros(PATCH_SIZE * PATCH_SIZE, dtype=np.float32)
    b[5] = 1.0
    faces = [
        {
            "display_name": "Иван И.",
            "embedding": a.tolist(),
            "embeddings": [a.tolist(), b.tolist()],
        }
    ]
    assert match_consented_name(b, faces, threshold=0.99) == "Иван И."
