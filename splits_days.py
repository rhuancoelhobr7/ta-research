"""splits_days.py — ÚNICO ponto de corte temporal (regra dura nº 1).
Split por DIAS: treino 60%, validação 20%, holdout 20% (dias mais recentes,
que incluem 6 das 7 chamadas do especialista — auditoria e teste final se
encontram no mesmo trecho jamais usado para desenvolver regras)."""
import pandas as pd

TRAIN_FRAC, VALID_FRAC = 0.60, 0.20


def day_cuts(days: pd.DatetimeIndex):
    days = days.sort_values().unique()
    n = len(days)
    return days[int(n * TRAIN_FRAC)], days[int(n * (TRAIN_FRAC + VALID_FRAC))]


def research_days(days: pd.DatetimeIndex):
    t_cut, v_cut = day_cuts(days)
    d = days.sort_values().unique()
    return d[d < t_cut], d[(d >= t_cut) & (d < v_cut)]


def holdout_days(days: pd.DatetimeIndex, i_accept_this_is_final: bool = False):
    if not i_accept_this_is_final:
        raise PermissionError("Holdout é tocado UMA vez, por a7_final_test.py.")
    _, v_cut = day_cuts(days)
    d = days.sort_values().unique()
    return d[d >= v_cut]
