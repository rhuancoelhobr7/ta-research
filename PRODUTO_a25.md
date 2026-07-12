# Produto a25 — Ranqueador de AMPLITUDE (o único sobrevivente do projeto)

## O que é
Todo dia, ordena os 28 pares G8 por MOVIMENTO esperado, usando o ATR de sessão.
Dois modos:
- **AMPLITUDE** — os pares de maior movimento absoluto (~79 pips
  líq/dia, 80% do teto do dia; acerta o maior-range em
  25% vs 3.6% do acaso). Tende a apontar crosses de GBP.
- **EFICIÊNCIA** — mais movimento POR SPREAD (razão 160 vs
  136), para quem é sensível a custo.

## O que NÃO é (honestidade dura)
- **NÃO é sinal de direção.** O projeto testou ~12 formulações direcionais; todas
  mortas (a5→a41). Você escolhe a direção; o a25 só diz ONDE há movimento.
- **NÃO é P&L.** A "amplitude líquida" é o teto capturável se a direção acertar.
- **NÃO é preditor de T0 nem usa CSS** (o CSS é preço reembalado — a30/a34/a37).

## Base de evidência
a33 (29.8% vs 23.8% persistência vs 4.1% da cadeia); a40 (breakeven direcional
0.505 — economia favorável; spread é 0.5% do ATR nos pares grandes vs 1.0% nos
pequenos); a42 (tem informação diária real, +3.7 pips/dia vs estático, BH).

## Como operar
1. Ingerir M5 novo; `python a43_produto.py` gera a escolha do dia (pick_hoje_*.csv).
2. Escolher o modo (amplitude ou eficiência) conforme sensibilidade a custo.
3. Aplicar a SUA direção e gestão sobre o par escolhido.
4. Registrar prospectivamente (a39) para acumular evidência OOS honesta.

## Badge no indicador (proposta)
Exibir no painel o **top-3 de amplitude** e o **top-3 de eficiência** do dia,
marcados como "movimento esperado, não direção". Nunca sugerir lado. Latência:
o ATR de sessão é conhecido na abertura (sem espera).
