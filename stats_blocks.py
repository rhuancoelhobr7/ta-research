"""stats_blocks.py — utilitários estatísticos com estrutura de blocos.

Funções puras usadas por a3/a5/a6 (regras duras 6 do CLAUDE.md):
  block_bootstrap_ci : IC por bootstrap em blocos circulares (dias contíguos)
  block_permute      : permutação em blocos (rotação circular) p/ reality check
  reality_check_p95  : p95 da distribuição de MÁXIMOS entre regras permutadas
  purged_cv_splits   : folds temporais contíguos com gap purgado (dias)

Convenção: as séries são CRONOLÓGICAS e indexadas por dia; blocos preservam
a dependência serial (persistência de rótulos, clusters de volatilidade).
"""
from __future__ import annotations

import numpy as np


def _circular_blocks(n: int, block: int, rng: np.random.Generator) -> np.ndarray:
    """Índices de um resample circular em blocos de tamanho `block` (n itens)."""
    n_blocks = int(np.ceil(n / block))
    starts = rng.integers(0, n, size=n_blocks)
    idx = (starts[:, None] + np.arange(block)[None, :]) % n
    return idx.ravel()[:n]


def block_bootstrap_ci(values: np.ndarray, stat=np.mean, n_boot: int = 2000,
                       block: int = 5, alpha: float = 0.05,
                       seed: int = 0) -> tuple[float, float, float]:
    """(estatística, lo, hi): IC percentil por bootstrap em blocos circulares.

    values : série cronológica (1-D); NaN não são tratados — filtrar antes.
    block  : tamanho do bloco em observações (dias).
    """
    v = np.asarray(values, dtype=float)
    if len(v) == 0:
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot)
    for i in range(n_boot):
        boots[i] = stat(v[_circular_blocks(len(v), block, rng)])
    lo, hi = np.quantile(boots, [alpha / 2, 1 - alpha / 2])
    return float(stat(v)), float(lo), float(hi)


def block_permute(n: int, block: int, rng: np.random.Generator) -> np.ndarray:
    """Permutação por rotação circular + embaralhamento de blocos contíguos.

    Divide 0..n-1 em blocos contíguos de tamanho `block`, aplica uma rotação
    circular aleatória e embaralha a ordem dos blocos. Preserva a estrutura
    serial DENTRO dos blocos e destrói o alinhamento com as features.
    """
    shift = int(rng.integers(0, n))
    idx = (np.arange(n) + shift) % n
    cuts = np.arange(block, n, block)
    blocks = np.split(idx, cuts)          # blocos contíguos; último pode ser menor
    order = rng.permutation(len(blocks))
    return np.concatenate([blocks[i] for i in order])


def reality_check_p95(perm_maxima: np.ndarray) -> float:
    """p95 da distribuição de máximos (White's reality check simplificado).

    perm_maxima : para cada permutação, o MÁXIMO da métrica entre todas as
    regras candidatas. Uma regra real só é 'descoberta' se sua métrica
    observada exceder este p95.
    """
    return float(np.quantile(np.asarray(perm_maxima, dtype=float), 0.95))


def purged_cv_splits(n: int, n_folds: int = 5, gap: int = 5):
    """Folds temporais contíguos com purga de `gap` observações nas bordas.

    Gera (train_idx, test_idx): teste = fatia contígua; treino = resto MENOS
    `gap` observações de cada lado do teste (evita vazamento serial).
    """
    bounds = np.linspace(0, n, n_folds + 1).astype(int)
    for k in range(n_folds):
        a, b = bounds[k], bounds[k + 1]
        test = np.arange(a, b)
        train_mask = np.ones(n, dtype=bool)
        train_mask[max(0, a - gap):min(n, b + gap)] = False
        yield np.where(train_mask)[0], test
