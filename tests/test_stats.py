"""Testes de stats_blocks — obrigatórios ANTES do uso (CLAUDE.md, convenções)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np
import pytest

from stats_blocks import (block_bootstrap_ci, block_permute,
                          purged_cv_splits, reality_check_p95)


def test_bootstrap_ci_covers_true_mean():
    """IID N(0.5, 1): IC de 95% deve conter a média verdadeira na maioria
    das repetições (checagem grosseira de calibração)."""
    rng = np.random.default_rng(0)
    hits = 0
    for i in range(40):
        x = rng.normal(0.5, 1.0, 300)
        _, lo, hi = block_bootstrap_ci(x, n_boot=500, block=5, seed=i)
        hits += lo <= 0.5 <= hi
    assert hits >= 33  # ~95% nominal; folga p/ variância do teste


def test_bootstrap_ci_width_grows_with_dependence():
    """Série AR(1) forte: IC em blocos deve ser MAIS LARGO que o de uma série
    iid com a mesma variância marginal (motivo de usar blocos)."""
    rng = np.random.default_rng(1)
    n = 500
    ar = np.zeros(n)
    for t in range(1, n):
        ar[t] = 0.9 * ar[t - 1] + rng.normal()
    ar = ar / ar.std()
    iid = rng.normal(0, 1, n)
    _, lo_a, hi_a = block_bootstrap_ci(ar, n_boot=800, block=20, seed=2)
    _, lo_i, hi_i = block_bootstrap_ci(iid, n_boot=800, block=20, seed=2)
    assert (hi_a - lo_a) > (hi_i - lo_i)


def test_block_permute_is_permutation():
    rng = np.random.default_rng(3)
    for n in (10, 47, 100):
        p = block_permute(n, 5, rng)
        assert sorted(p) == list(range(n))


def test_block_permute_preserves_local_runs():
    """Dentro de um bloco, vizinhos originais continuam vizinhos."""
    rng = np.random.default_rng(4)
    p = block_permute(100, 10, rng)
    consec = np.mean(np.diff(p) == 1)
    assert consec > 0.8  # 9 de cada 10 transições são consecutivas no original


def test_purged_cv_no_leakage_and_coverage():
    n, gap = 100, 5
    seen = np.zeros(n, dtype=int)
    for train, test in purged_cv_splits(n, n_folds=5, gap=gap):
        seen[test] += 1
        # nenhuma observação de treino a menos de `gap` do teste
        assert min(abs(int(t) - int(s)) for t in (test[0], test[-1])
                   for s in train) >= 1
        assert all(s < test[0] - gap or s > test[-1] + gap - 1 or
                   s < test[0] or s > test[-1] for s in train)
        assert not set(train) & set(test)
        assert all((s <= test[0] - gap - 1) or (s >= test[-1] + gap + 1) or
                   (test[0] <= s <= test[-1]) is False for s in train)
    assert (seen == 1).all()  # cada dia testado exatamente uma vez


def test_purged_cv_gap_strict():
    for train, test in purged_cv_splits(60, n_folds=3, gap=4):
        lo, hi = test[0], test[-1]
        bad = [s for s in train if lo - 4 <= s <= hi + 4]
        assert bad == []


def test_reality_check_p95():
    x = np.arange(100, dtype=float)
    assert reality_check_p95(x) == pytest.approx(np.quantile(x, 0.95))


def test_bootstrap_empty():
    s, lo, hi = block_bootstrap_ci(np.array([]))
    assert np.isnan(s) and np.isnan(lo) and np.isnan(hi)
