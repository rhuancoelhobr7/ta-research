"""GATE DE EXECUÇÃO (CLAUDE.md regra 1): nenhuma feature usa ts > T0.

Estratégia: dados sintéticos -> pipeline completo -> (a) auditoria dos
max_ts registrados; (b) prova de truncagem — recomputar as features de um
dia com TODOS os dados posteriores a T0 removidos tem de dar o MESMO valor
(se algo olhasse o futuro, o valor mudaria).
"""
import numpy as np
import pandas as pd

from comum import config, t0_do_dia
from fase1_rotulagem import rotular
from fase3_features import (features_do_dia, f4_series, montar, preparar,
                            resample_h4)

PARES = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD"]
N_DIAS = 170


def _sintetico(seed: int = 3):
    """H1 + D1 sintéticos coerentes (24 barras H1/dia útil), índice =
    FECHAMENTO (contrato de carregar_ohlc)."""
    rng = np.random.default_rng(seed)
    dias = pd.bdate_range("2024-01-02", periods=N_DIAS)
    h1, d1 = {}, {}
    for par in PARES:
        closes = []
        idx = []
        px = 1.0
        for d in dias:
            for hh in range(1, 25):
                px *= float(np.exp(rng.normal(0, 8e-4)))
                closes.append(px)
                idx.append(d + pd.Timedelta(hours=hh))
        s = pd.Series(closes, index=pd.DatetimeIndex(idx))
        h1[par] = pd.DataFrame({"open": s.shift(1).fillna(s.iloc[0]),
                                "high": s * 1.0004, "low": s * 0.9996,
                                "close": s, "tick_volume": 1.0})
        dcl = s.resample("1D", label="right", closed="right").last().dropna()
        dop = s.resample("1D", label="right", closed="right").first().dropna()
        dhi = s.resample("1D", label="right", closed="right").max().dropna()
        dlo = s.resample("1D", label="right", closed="right").min().dropna()
        d1[par] = pd.DataFrame({"open": dop, "high": dhi * 1.0001,
                                "low": dlo * 0.9999, "close": dcl,
                                "tick_volume": 1.0})
    return h1, d1


def test_gate_vazamento_pipeline_completo():
    cfg = config()
    h1, d1 = _sintetico()
    labels = rotular(d1, cfg)
    feats = montar(h1, d1, labels, cfg)
    assert len(feats) > 30

    t0s = pd.to_datetime(feats["t0"])
    for col in ("max_ts_f13", "max_ts_f4_h1", "max_ts_f4_h4"):
        assert (pd.to_datetime(feats[col]) <= t0s).all(), f"{col} > T0"

    # prova de truncagem F1-F3 (5 dias espalhados)
    prep_full = preparar(h1, d1, labels, cfg)
    for dia in feats.index[[len(feats)//4, len(feats)//2, -3, -2, -1]]:
        t0 = t0_do_dia(dia)
        h1t = {p: df[df.index <= t0] for p, df in h1.items()}
        d1t = {p: df[df.index <= t0] for p, df in d1.items()}
        f_full = features_do_dia(prep_full, dia)
        f_trunc = features_do_dia(preparar(h1t, d1t,
                                           labels[labels.index < dia], cfg), dia)
        assert f_trunc is not None
        for k, v in f_trunc.items():
            if k in ("t0", "max_ts_f13"):
                continue
            assert np.isclose(v, f_full[k], rtol=1e-10), \
                f"VAZAMENTO em {k} @ {dia}"


def test_gate_vazamento_f4():
    """F4 (motor CSSM) também tem de ser truncagem-invariante em T0."""
    cfg = config()
    h1, _ = _sintetico(seed=5)
    closes = {p: df["close"] for p, df in h1.items()}
    dia = pd.Timestamp("2024-08-05")
    t0 = t0_do_dia(dia)
    lentes = cfg["features"]["f4_lentes"]

    for tag, w, cl in (("h1", lentes["H1"], closes),
                       ("h4", lentes["H4"], resample_h4(closes))):
        full = f4_series(cl, w, cfg, tag)
        clt = {p: s[s.index <= t0] for p, s in cl.items()}
        trunc = f4_series(clt, w, cfg, tag)
        pos = full.index.searchsorted(t0, side="right") - 1
        ts = full.index[pos]
        assert ts <= t0
        a, b = full.loc[ts], trunc.loc[ts]
        mask = a.notna() & b.notna()
        assert mask.any()
        assert np.allclose(a[mask], b[mask], rtol=1e-9), f"VAZAMENTO F4 {tag}"
