# a42 — O a25 tem informação diária, ou é uma tabela estática?

**EXPLORATÓRIO (holdout esgotado): vencedores são CANDIDATOS, confirmáveis só via prospectivo (a39).** 2335 dias (após aquecimento). Competidores do base_atr do a25 (importado).

## Q1/Q2 — Diferença de captura vs ESTÁTICO (E), pips/dia

| comp   |   dif_vs_E_pips |      lo |      hi |   p | bh    |
|:-------|----------------:|--------:|--------:|----:|:------|
| A      |           3.685 |   2.08  |   5.462 |   0 | True  |
| Z60    |         -27.823 | -30.166 | -25.367 |   1 | False |
| Z120   |         -28.804 | -30.944 | -26.66  |   1 | False |
| Z250   |         -27.382 | -30.019 | -24.79  |   1 | False |


**Q1 (A vs E): o a25 TEM informação diária demonstrável** — dif A−E = +3.68 pips, IC [+2.08, +5.46]. A vantagem existe.

## Q3 (primária) — Eficiência range/spread e captura

| sel       |   cap1_pips |   net1_pips |   efic_range/spread |   P(top1=max) |   pct_teto |
|:----------|------------:|------------:|--------------------:|--------------:|-----------:|
| E         |      76.933 |      75.343 |              97.226 |         0.223 |      0.773 |
| A         |      80.617 |      79.269 |             135.547 |         0.254 |      0.796 |
| Z60       |      49.458 |      48.497 |             150.035 |         0.046 |      0.501 |
| Z120      |      48.792 |      47.844 |             147.823 |         0.043 |      0.494 |
| Z250      |      50.109 |      49.16  |             159.702 |         0.061 |      0.513 |
| aleatório |      45.944 |      45.002 |             132.365 |         0.036 |    nan     |


- **Melhor razão de eficiência (range/spread): Z250.** O z-ATR supera o ATR bruto aqui (cenário que o a40 antecipa).

## Q4 — Composição dos rankings

- pares mais escolhidos pelo a25 (top-1): {'GBPNZD': 0.505, 'GBPJPY': 0.231, 'GBPAUD': 0.122, 'EURNZD': 0.067, 'EURAUD': 0.028, 'GBPCAD': 0.014}

- sobreposição dia a dia (top-1 = ontem): E 100%, A 84%, Z60 62%, Z120 68%, Z250 73%

- sobreposição Z120 vs A (mesmo top-1): 6% (Z carrega info do DIA (troca mais)).


## Síntese

**O a25 SOBREVIVE**: tem informação diária real (+3.7 pips vs estático, IC exclui 0, BH), mas é SOBRETUDO uma tabela (escolhe GBP-crosses ~86%, 84% de sobreposição). **O z-ATR FALHA para AMPLITUDE absoluta** (~-28 pips vs estático): para amplitude, o NÍVEL É o sinal, e auto-normalizar (remover o nível) o destrói — o OPOSTO da direção (a35, onde a auto-normalização venceu). Dicotomia limpa: **amplitude mora no NÍVEL, direção morava no DESVIO.** PORÉM o **z-ATR VENCE em eficiência range/spread** (160 vs 136 do a25), selecionando pares calmos num dia atípico com spread proporcionalmente menor — o cenário do a40. CANDIDATO para o prospectivo (a39): z-ATR como seletor spread-eficiente; jamais achado confirmado (holdout esgotado).
