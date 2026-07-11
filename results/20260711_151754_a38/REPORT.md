# a38 — Valor econômico dos dois sinais confirmados (com custo)

Regras CONGELADAS (a35/a35-bis), zero parâmetros livres. Custo real: spread mediano por par (M5), slippage 0.1 pip/ponta, swap 0 (intradiário), comissão 0. 786 dias. Custo em pips E % do bruto. $ aproximado ($10/pip/lote).

## Resultado por estratégia (expectativa LÍQUIDA por trade, pips)

| estratégia | exp. líq. | IC95 | aleatório | acurácia dir. | win líq. | custo %bruto | PF | maxDD | viável? |
|---|---|---|---|---|---|---|---|---|---|
| A_par | -0.62 | [-4.00, +2.86] | -2.57 | 48.6% | 47.3% | 2% | 0.96 | -1579 | NÃO |
| A_cesta | -1.21 | [-3.51, +1.14] | -0.26 | 48.7% | 47.8% | 3% | 0.90 | -1334 | NÃO |
| B_par | -0.80 | [-3.96, +2.37] | -1.80 | 51.2% | 49.9% | 2% | 0.95 | -1212 | NÃO |
| B_cesta | +0.13 | [-2.29, +2.68] | -0.19 | 51.4% | 50.5% | 3% | 1.01 | -1081 | NÃO |


_A diferença entre **acurácia direcional** e **win líquido** é a resposta de 'acurácia vira lucro?': o custo move a linha d'água._

## Decomposição por fatia e por ano (expectativa líq., pips)

- **A_par** — fatias: {'>=q70': 0.58, 'q50-q70': -1.68, 'research': -0.94} · anos: {2023: -0.32, 2024: -1.7, 2025: -1.81, 2026: 3.43}
- **A_cesta** — fatias: {'>=q70': -0.11, 'q50-q70': -1.39, 'research': -1.82} · anos: {2023: -3.59, 2024: -1.47, 2025: -0.86, 2026: 0.72}
- **B_par** — fatias: {'>=q70': -0.02, 'q50-q70': 0.02, 'research': -1.6} · anos: {2023: -0.22, 2024: -2.07, 2025: 0.22, 2026: -0.82}
- **B_cesta** — fatias: {'>=q70': 1.99, 'q50-q70': -1.74, 'research': -0.25} · anos: {2023: 0.85, 2024: -0.33, 2025: -0.86, 2026: 2.27}


## Sensibilidade ao custo (varia só o spread assumido, não a regra)

|   spread_x |   A_par |   A_cesta |   B_par |   B_cesta |
|-----------:|--------:|----------:|--------:|----------:|
|        0.5 |   -0.39 |     -0.97 |   -0.58 |      0.37 |
|        1   |   -0.62 |     -1.21 |   -0.8  |      0.13 |
|        1.5 |   -0.85 |     -1.45 |   -1.02 |     -0.1  |
|        2   |   -1.08 |     -1.69 |   -1.24 |     -0.34 |


_Breakeven: spread máximo que o sinal tolera antes de zerar. Se o breakeven ficar abaixo do spread real do broker, o sinal é INOPERÁVEL._

## Veredito pré-registrado

**NENHUMA estratégia é economicamente viável.** E o motivo é mais fundo que 'o custo come o edge': a **acurácia direcional do movimento CAPTURÁVEL (da entrada até 15h) é ~49-51% — quase moeda-ao-ar**. Os sinais confirmados (0.506 do a35, 0.646 do a35-bis) descreviam o estado JÁ FORMADO até o horário de entrada; o RESIDUAL que se captura entrando ali é ruído (coerente com o +0.02 do a35-bis). O custo é só 2-3% do bruto — não é o vilão; o BRUTO já é ~0. Mesmo com spread 0.5x nada fica robustamente positivo (IC sempre inclui zero). Os dois sinais são fatos estatísticos reais sobre o PASSADO, não edges tradeáveis sobre o FUTURO. O projeto NÃO produziu sinal direcional operável; o único entregável prático permanece o ranqueador de AMPLITUDE por ATR de sessão (a25).


_Próximo passo honesto (não executado): validação PROSPECTIVA em dias novos — não há mais fatia pristina p/ novos testes retrospectivos._
