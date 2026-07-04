# Tendência Absoluta — Pesquisa

Estudo empírico em duas fases sobre a "tendência absoluta" diária de moedas
G8 (a tese de um especialista: quase todo dia uma moeda entra em tendência
que se reflete em TODOS os seus 7 pares, decidível na abertura de Tokyo):

- **Fase A** — rotular a realidade: quando/quanto o fenômeno acontece (2 anos, intraday);
- **Fase B** — engenharia reversa: o estado do indicador CSSM em T0 (abertura
  de Tokyo) previa os dias rotulados?

**Estado (2026-07-04): fases A, B e C executadas. Resultado central: NULO —
o fenômeno existe (~88% dos dias), mas o CSSM em T0 não o prevê.** Detalhes
e números em `CHANGELOG.md` e nos `results/*/REPORT.md`. O teste final de
holdout (a7) permanece intocado.

## Para começar (humanos e IAs)

1. Leia `CLAUDE.md` (contratos e **regras duras não-negociáveis** — holdout,
   congelamento, anti-lookahead) e `PLAN.md` (metodologia completa).
2. Leia `CHANGELOG.md` — o histórico de decisões; várias são irreversíveis.
3. Setup: Python ≥ 3.11; `pip install -r requirements.txt`; `pytest -q`
   (25 testes) deve passar ANTES e DEPOIS de qualquer mudança.

## Dados

Os parquets brutos do MT5 **não são versionados** (36 MB, específicos da
corretora). Para reproduzir do zero: `python s0_export_mt5.py` (Windows +
terminal MT5 logado) e **verifique o fuso** em `data/raw/_meta.json`
(instruções no CLAUDE.md — erro de fuso invalida tudo). Os artefatos
derivados pequenos SÃO versionados (rótulos congelados, features em T0,
relatórios), então as análises da Fase B podem ser refeitas sem MT5.

## Mapa do repositório

| Arquivo | Papel |
|---|---|
| `cssm_engine.py` | Porte fiel do indicador CSSM (MQ5 → Python), validado |
| `s0_export_mt5.py` | Fase 0: exporta M5 (2a) + D1 (4a) dos 28 pares |
| `a1_label_days.py` | Fase A1: rotulador — **definição v1 congelada** |
| `a2_audit_specialist.py` | Fase A2: auditoria das 7 chamadas do especialista |
| `a3_anatomy.py` | Fase A3: anatomia (taxa-base, persistência, sessões) |
| `a4_features_t0.py` | Fase B: matriz de features do CSSM em T0 |
| `a5_reverse.py` | Fase B: contraste, regras, baselines, ML, reality check |
| `a6_portfolio.py` | Fase C: portfólio diário de 7 pares com custos |
| `a7_final_test.py` | Holdout — stub de propósito; UMA execução, sob ordem |
| `a8_first4h.py` | Descritivo: rótulos × estados CSSM nas primeiras 4h |
| `splits_days.py` | Guardião do split temporal (treino/validação/holdout) |
| `stats_blocks.py` | Bootstrap em blocos, permutação, purged CV (testados) |
| `specialist_calls.csv` | As 7 chamadas reais — IMUTÁVEL, âncora de auditoria |

Sequência canônica: `s0 → a1 → a2 → freeze → a3 → a4 → a5 → a6` (feita);
`a7` só sob ordem explícita do dono do repositório.

## Regras para quem for mexer (inclusive IAs)

- **Toda alteração vai para o git** — branch + commit + push, de preferência
  via Pull Request. O fluxo completo (obrigatório) está no CLAUDE.md, seção
  "Fluxo de alterações (git)". Mudança sem commit não existe.
- `pytest -q` sempre verde; novos cálculos estatísticos ganham teste antes.
- NUNCA chamar `splits_days.holdout_days` fora de `a7_final_test.py`.
- NUNCA mudar a definição de rótulo dentro da v1 — mudança = v2, Fase B do
  zero, reportada como segunda tentativa.
- Features em T0 só com barras fechadas (teste anti-lookahead obrigatório).
- Resultados nulos são resultados: reportar com as métricas do PLAN.md.
