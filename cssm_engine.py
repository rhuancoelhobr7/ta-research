"""
cssm_engine.py — Porte fiel do motor CSSM_Contexto v1.30 (MQ5) para Python.

Replica, função por função, os cálculos do indicador:
  - Índices sintéticos G8 a partir de retornos log dos pares
  - TStat (t da média dos retornos, erro-padrão Newey-West/Bartlett L=3, piso 0.1*g0)
  - EffRatio (Kaufman), VolMom (fast/mid), Persist, Convex, Acc (EMA de momF-momM)
  - z-scores adaptativos (valor / desvio-padrão rolante — SEM subtrair a média,
    exatamente como SerStd é usado no MQ5)
  - Máquina de estados: 0=Ruído, 1=Emergindo, 2=Madura, 3=Exausta
    (prioridade: Exausta > Madura > Emergindo)
  - Valor M = sign(t) * min(|t|/2, 1) * ER

Convenção temporal: séries CRONOLÓGICAS (índice 0 = mais antigo), o oposto do
MQ5 (k=0 = barra fechada mais recente). Todas as janelas olham para trás.
O valor na linha t usa apenas dados até t, inclusive — sem lookahead.

Uso mínimo:
    from cssm_engine import CssmParams, build_indices, compute_currency

    idx = build_indices(closes)            # closes: dict {"EURUSD": pd.Series}
    out = compute_currency(idx["GBP"], CssmParams())
    out.columns -> ['t','er','mom_f','mom_m','pers','conv','acc',
                    'acc_z','conv_z','M','state','dir']
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

G8 = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]

ST_NOISE, ST_EMERGING, ST_MATURE, ST_EXHAUSTED = 0, 1, 2, 3
STATE_NAMES = {0: "Ruido", 1: "Emergindo", 2: "Madura", 3: "Exausta"}


@dataclass(frozen=True)
class CssmParams:
    """Espelha os inputs do indicador (mesmos defaults)."""
    w_fast: int = 16      # InpWFast
    w_mid: int = 64       # InpWMid  — janela-base das features
    z_win: int = 500      # InpZWin  — janela do z-score adaptativo
    acc_span: int = 8     # InpAccSpan — EMA da aceleração
    t_gate: float = 2.0   # InpTGate — |t| mínimo p/ Madura/Exausta
    t_low: float = 1.0    # InpTLow  — |t| mínimo p/ Emergindo
    persist: float = 0.55  # InpPersist
    acc_emg: float = 0.75  # InpAccEmg — |z acc| p/ Emergindo
    cx_exh: float = -1.0   # InpCxExh — z convexidade contra tendência
    ac_exh: float = -0.75  # InpAcExh — z aceleração contra tendência


# ----------------------------------------------------------------------------
# 1. Índices sintéticos
# ----------------------------------------------------------------------------

def build_indices(closes: dict[str, pd.Series],
                  align: str = "inner") -> pd.DataFrame:
    """Constrói os 8 índices sintéticos a partir dos closes dos pares.

    closes : dict {symbol: Series de fechamentos indexada por datetime}.
             O símbolo deve conter os códigos das moedas (ex. 'EURUSD',
             'GBPJPY.m' também funciona — extraímos os 2 códigos G8).
    align  : 'inner' (interseção de timestamps — recomendado p/ pesquisa)
             ou 'ffill' (união + forward-fill; retorno 0 nas barras preenchidas).

    Retorna DataFrame (datetime x 8 moedas) com o índice acumulado de cada
    moeda: soma cumulativa da MÉDIA dos retornos log de todos os pares em que
    ela participa (base soma +r, cotada soma -r), começando em 0 — o mesmo
    procedimento de Compute() no MQ5.
    """
    parsed: list[tuple[str, int, int]] = []
    for sym in closes:
        found = [c for c in G8 if c in sym.upper()]
        # ordena pela posição no nome p/ distinguir base de cotada
        found = sorted(set(found), key=lambda c: sym.upper().find(c))
        if len(found) != 2:
            raise ValueError(f"Não identifiquei 2 moedas G8 em '{sym}'")
        b, q = G8.index(found[0]), G8.index(found[1])
        parsed.append((sym, b, q))

    frame = pd.DataFrame({s: closes[s] for s, _, _ in parsed})
    if align == "inner":
        frame = frame.dropna()
    else:
        frame = frame.ffill().dropna()

    logp = np.log(frame.to_numpy(dtype=float))
    rets = np.diff(logp, axis=0)                      # (T-1, n_pairs)

    T = rets.shape[0]
    cur_ret = np.zeros((T, 8))
    cnt = np.zeros(8)
    for j, (_, b, q) in enumerate(parsed):
        cur_ret[:, b] += rets[:, j]
        cur_ret[:, q] -= rets[:, j]
        cnt[b] += 1
        cnt[q] += 1
    if (cnt == 0).any():
        missing = [G8[i] for i in range(8) if cnt[i] == 0]
        raise ValueError(f"Moedas sem nenhum par na cesta: {missing}")
    cur_ret /= cnt                                    # média dos votos

    idx = np.vstack([np.zeros((1, 8)), np.cumsum(cur_ret, axis=0)])
    return pd.DataFrame(idx, index=frame.index, columns=G8)


# ----------------------------------------------------------------------------
# 2. Features (todas vetorizadas; janela = últimos w valores até t, inclusive)
# ----------------------------------------------------------------------------

def _pad(arr: np.ndarray, total: int) -> np.ndarray:
    """Prefixa NaN para realinhar saída de janelas ao comprimento original."""
    out = np.full(total, np.nan)
    out[total - len(arr):] = arr
    return out


def tstat_nw(x: np.ndarray, w: int) -> np.ndarray:
    """t da média dos retornos com erro-padrão Newey-West (Bartlett L=3).

    Idêntico a TStat() do MQ5: g_l normalizado por (w-l), pesos 0.75/0.50/0.25,
    piso v >= 0.1*g0, se = sqrt(v/w).
    """
    d = np.diff(x)
    n = len(x)
    if len(d) < w:
        return np.full(n, np.nan)
    W = sliding_window_view(d, w)                 # (m, w) cronológico
    mu = W.mean(axis=1)
    E = W - mu[:, None]
    g0 = (E * E).sum(axis=1) / w
    g1 = (E[:, :-1] * E[:, 1:]).sum(axis=1) / (w - 1)
    g2 = (E[:, :-2] * E[:, 2:]).sum(axis=1) / (w - 2)
    g3 = (E[:, :-3] * E[:, 3:]).sum(axis=1) / (w - 3)
    v = g0 + 2.0 * (0.75 * g1 + 0.50 * g2 + 0.25 * g3)
    v = np.maximum(v, 0.1 * g0)
    se = np.sqrt(v / w)
    t = np.where(se > 0, mu / se, 0.0)
    return _pad(t, n)


def eff_ratio(x: np.ndarray, w: int) -> np.ndarray:
    d = np.abs(np.diff(x))
    n = len(x)
    if len(d) < w:
        return np.full(n, np.nan)
    net = np.abs(x[w:] - x[:-w])
    path = sliding_window_view(d, w).sum(axis=1)
    er = np.where(path > 0, net / path, 0.0)
    return _pad(er, n)


def _win_std(d: np.ndarray, w: int) -> np.ndarray:
    """Desvio-padrão amostral (ddof=1) dos retornos em janela w — como no MQ5."""
    W = sliding_window_view(d, w)
    mean = W.mean(axis=1)
    var = (W * W).mean(axis=1) - mean * mean
    var = np.clip(var, 0.0, None)
    return np.sqrt(var * w / (w - 1))


def vol_mom(x: np.ndarray, w: int) -> np.ndarray:
    d = np.diff(x)
    n = len(x)
    if len(d) < w:
        return np.full(n, np.nan)
    net = x[w:] - x[:-w]
    sd = _win_std(d, w)
    vm = net / (sd * math.sqrt(w) + 1e-12)
    return _pad(vm, n)


def persist(x: np.ndarray, w: int) -> np.ndarray:
    d = np.diff(x)
    n = len(x)
    if len(d) < w:
        return np.full(n, np.nan)
    up = sliding_window_view((d > 0).astype(float), w).sum(axis=1)
    dn = sliding_window_view((d < 0).astype(float), w).sum(axis=1)
    net = x[w:] - x[:-w]
    p = np.where(net >= 0, up / w, dn / w)
    return _pad(p, n)


def convex(x: np.ndarray, w: int) -> np.ndarray:
    """Coeficiente quadrático (polinômio ortogonal) * w² / sd dos retornos."""
    n = len(x)
    if n < w + 1:
        return np.full(n, np.nan)
    jm = (w - 1) / 2.0
    u = np.arange(w) - jm
    mu2 = (u * u).mean()
    p2 = u * u - mu2                       # simétrico: ordem da janela é irrelevante
    den = (p2 * p2).sum()
    L = sliding_window_view(x, w)          # janelas de NÍVEIS, cronológicas
    cq = (L @ p2) / den
    d = np.diff(x)
    sd = _win_std(d, w)                    # mesmos w retornos da janela
    # alinhar: janela de níveis terminando em t usa retornos t-w+1..t
    m = min(len(cq) - 1, len(sd))          # cq tem uma janela a mais (sem retorno)
    cv = cq[-m:] * (w * w) / (sd[-m:] + 1e-12)
    return _pad(cv, n)


def acc_ema(mom_f: np.ndarray, mom_m: np.ndarray, span: int) -> np.ndarray:
    """EMA recursiva de (momF - momM), alpha = 2/(span+1), como no MQ5."""
    x = mom_f - mom_m
    return pd.Series(x).ewm(span=span, adjust=False).mean().to_numpy()


def rolling_sd_z(v: np.ndarray, z_win: int, min_n: int = 8) -> np.ndarray:
    """z adaptativo do MQ5: valor / desvio-padrão dos últimos z_win valores
    (incluindo o atual). NÃO subtrai a média — replica SerStd + divisão direta.
    """
    s = pd.Series(v)
    sd = s.rolling(z_win, min_periods=min_n).std(ddof=1).to_numpy()
    ok = np.isfinite(sd) & (sd > 0)
    z = np.zeros(len(v))
    z[ok] = v[ok] / sd[ok]
    return z


# ----------------------------------------------------------------------------
# 3. Motor completo por moeda
# ----------------------------------------------------------------------------

def compute_currency(index: pd.Series, p: CssmParams = CssmParams()) -> pd.DataFrame:
    """Aplica todo o pipeline de features + estados a UM índice sintético.

    Retorna DataFrame alinhado ao índice temporal de entrada. Linhas iniciais
    (aquecimento das janelas) vêm como NaN/estado -1.
    """
    x = index.to_numpy(dtype=float)
    n = len(x)

    t = tstat_nw(x, p.w_mid)
    er = eff_ratio(x, p.w_mid)
    mf = vol_mom(x, p.w_fast)
    mm = vol_mom(x, p.w_mid)
    pe = persist(x, p.w_mid)
    cv = convex(x, p.w_mid)

    valid = ~np.isnan(mf) & ~np.isnan(mm)
    ac = np.full(n, np.nan)
    if valid.any():
        i0 = np.argmax(valid)
        ac[i0:] = acc_ema(mf[i0:], mm[i0:], p.acc_span)

    acz = np.where(np.isnan(ac), np.nan, rolling_sd_z(np.nan_to_num(ac), p.z_win))
    cvz = np.where(np.isnan(cv), np.nan, rolling_sd_z(np.nan_to_num(cv), p.z_win))

    sign_t = np.sign(t)
    M = sign_t * np.minimum(np.abs(t) / 2.0, 1.0) * er

    # máquina de estados (prioridade: Exausta > Madura > Emergindo)
    at = np.abs(t)
    cx_dir = cvz * sign_t
    ac_dir = acz * sign_t
    emerging = ((at < p.t_gate) & (at >= p.t_low) &
                (np.abs(acz) >= p.acc_emg) &
                (((ac > 0) & (mf > 0)) | ((ac < 0) & (mf < 0))))
    mature = (at >= p.t_gate) & (pe >= p.persist)
    exhaust = (at >= p.t_gate) & (cx_dir <= p.cx_exh) & (ac_dir <= p.ac_exh)

    state = np.zeros(n, dtype=float)
    state[emerging] = ST_EMERGING
    state[mature] = ST_MATURE
    state[exhaust] = ST_EXHAUSTED
    state[np.isnan(t) | np.isnan(acz) | np.isnan(cvz)] = -1  # aquecimento

    out = pd.DataFrame({
        "t": t, "er": er, "mom_f": mf, "mom_m": mm, "pers": pe,
        "conv": cv, "acc": ac, "acc_z": acz, "conv_z": cvz,
        "M": M, "state": state, "dir": sign_t,
    }, index=index.index)
    return out


def compute_all(indices: pd.DataFrame,
                p: CssmParams = CssmParams()) -> dict[str, pd.DataFrame]:
    """Motor para as 8 moedas. Retorna {moeda: DataFrame de features/estados}."""
    return {c: compute_currency(indices[c], p) for c in indices.columns}


# ----------------------------------------------------------------------------
# 4. Utilitários de pesquisa
# ----------------------------------------------------------------------------

def resample_closes(closes: dict[str, pd.Series], rule: str) -> dict[str, pd.Series]:
    """Reamostra closes de um TF base (ex. M5) para TFs maiores.
    rule: regra pandas — '30min', '1h', '4h', '1D', 'W-FRI', 'MS'...
    Usa o ÚLTIMO close do período (fechamento da barra agregada)."""
    return {s: v.resample(rule).last().dropna() for s, v in closes.items()}


def forward_returns(index: pd.Series, horizons: list[int]) -> pd.DataFrame:
    """Retornos futuros do índice sintético em cada horizonte (em barras).
    forward_returns(...)[h].loc[t] = index[t+h] - index[t]  (sem lookahead na
    variável explicativa; o alvo é explicitamente futuro)."""
    out = {h: index.shift(-h) - index for h in horizons}
    return pd.DataFrame(out, index=index.index)


def state_transitions(state: pd.Series) -> pd.DataFrame:
    """Eventos de transição de estado: DataFrame com colunas from/to no
    timestamp em que o novo estado apareceu (barra fechada)."""
    s = state[state >= 0]
    prev = s.shift(1)
    mask = (s != prev) & prev.notna()
    return pd.DataFrame({"from": prev[mask].astype(int),
                         "to": s[mask].astype(int)})
