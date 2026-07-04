# Histórico de decisões e resultados

Registro cronológico das decisões metodológicas — o "porquê" que o código não
conta. Toda IA (ou humano) trabalhando neste repositório deve ler isto antes
de propor mudanças: várias escolhas abaixo são IRREVERSÍVEIS por regra
(CLAUDE.md, "Regras duras").

## 2026-07-04 — Fase 0: dados e fuso

- Exportados 28 pares G8 do MT5 (M5 2 anos + D1 4 anos) via `s0_export_mt5.py`.
- **Fuso do servidor verificado e confirmado pelo usuário**: UTC+2 (inverno
  NA) / UTC+3 (verão NA), DST dos EUA — meia-noite do servidor = 17:00 NY.
  Evidência: todas as 104 segundas-feiras da amostra abrem 00:00 e todas as
  sextas fecham 23:55, inverno e verão (ver `data/raw/_meta.json`).
  Consequência: T0 = 00:00 do servidor ≈ pré-Tokyo, como o PLAN assume.

## 2026-07-04 — Fase A: definição v1 CONGELADA

- Calibração pelos dois critérios do PLAN §2 (âncoras + taxa-base):
  **breadth ≥ 6/7, |z| ≥ 0.8, er ≥ 0.12** → 1.98 rótulos/dia, 88.1% dos dias
  com ≥1 rótulo, **6/7 chamadas do especialista confirmadas** (direção 7/7).
- `er_min=0.12` está ABAIXO da grade de sensibilidade do PLAN (piso 0.15):
  os dias das 7 chamadas tinham er ≈ 0.14 e o piso da grade perdia 3 âncoras
  por 0.004–0.014. Decisão tomada ANTES de qualquer contato com features do
  indicador — separação de fases intacta. Aprovada explicitamente pelo usuário.
- Âncora não reproduzida: NZD 2026-06-17 (z 0.45, er 0.089 — o movimento não
  aparece na janela T0+12h). Registrada como miss honesto.
- A partir daqui, mudar a definição = v2 e reinicia a Fase B do zero.

## 2026-07-04 — Fase A3: anatomia (results/*_anatomy)

- Tokyo carrega 56% do |movimento|; protagonistas mais frequentes: EUR/GBP.
- Hipótese "NZD ilíquido rotula mais" NÃO se sustentou (NZD 9.8%, meio da fila).
- **Persistência dia-a-dia NULA** (lift 0.99, IC [0.216, 0.277] vs base
  0.248) — refuta a suspeita do PLAN de que o edge seria "surfar sequências".
- Proxy de evento (vol 1ª hora pós-T0) e dia-da-semana: nada saliente.

## 2026-07-04 — Fase B: features T0 (a4) e engenharia reversa (a5)

- Matriz 3.952 linhas (494 dias × 8 moedas); M30/H1/H4/D1 completos, W1
  reduzido, MN omitido; teste anti-lookahead em tests/test_features_t0.py.
- **RESULTADO CENTRAL: NULO** (results/*_reverse):
  - B1: maior separação rotulado×não = d de Cohen 0.10 (nada separa);
  - alinhamento direcional dos TFs em T0 ≈ 50% (moeda ao ar);
  - B2/B3: nenhuma das 9 regras bate os 3 baselines nem o reality check
    (p95 dos máximos permutados = 17.5% top-1; melhor regra: 14.2%);
  - B4: ML honesto AUC 0.487 (logistic) / 0.480 (gboost) para "rotula?";
    direção entre rotulados 0.588 ± 0.085 (fraco e instável).
  - Leitura: se o edge do especialista é real, vem de informação FORA do
    indicador (calendário, fluxo, preço) — exatamente o desfecho que o
    PLAN §5-B4 antecipava como resposta válida.
- Cenários A/B/C do "Protocolo" foram APROXIMADOS (documento não está no
  repositório) e estão rotulados como tal no relatório.

## 2026-07-04 — Fase C: portfólio (a6)

- Baselines e melhor regra (referência, não-sobrevivente) ≈ 0 bp/dia líquido
  ou pior; **teto oracle +41 bp/dia (+141% no período)** — o fenômeno vale
  muito SE previsível; o gargalo é a previsão, não o veículo.

## 2026-07-04 — a8: rótulos × estados nas primeiras 4h (descritivo)

- 126 dias research (2025-08-19 a 2026-02-16), holdout intocado.
- Nas primeiras 4h o CSSM quase não sai de Ruído, NEM nos dias rotulados:
  H1 ativo-na-direção em 4.1% (T0+2h) / 3.3% (T0+4h) das rotuladas — menor
  que nas não-rotuladas (6.8% / 6.2%). P(rotulou | H1 Ruído em T0+4h) = 25%
  > P(rotulou | Emergindo) = 16%.
- `align_4h` = 88.9% [85.4, 92.2]: o preço já anda na direção do dia cedo —
  mas é decomposição da própria janela do rótulo, não previsão.
- Única hipótese registrada p/ v2: sinal de preço das primeiras horas como
  confirmação intraday (exigiria v2 + Fase B reiniciada).

## Pendente

- `a7_final_test.py` (holdout, últimos ~20% dos dias): NÃO executado. Roda
  UMA vez, só sob ordem explícita do dono do repositório.
