# a28 — Comportamento da moeda preponderante em todas as sessões

**Deliverable da bateria a28–a32.** Descritivo, por PREÇO (`preponderante.py`),
3116 dias (2016-07 → 2026-07), 28 pares G8. Janelas: asia[00-07)/londres[07-13)/
ny[13-21) UTC + dia inteiro. Números completos em `results/*_a28/REPORT.md`.

## Definições (fixadas para toda a bateria)
- **consistência direcional(moeda, dia)** = nº de pares (0-7) em que a moeda foi
  na mesma direção (dirmove = ±net/ATR conforme base/cotada).
- **líder** = moeda de maior força líquida no conjunto; **anti-líder** = a mais
  fraca; **preponderante** = o polo de maior consistência.
- **força_preponderante** = média de |dirmove| nos 7 pares (normalizada por ATR).

## Achados

**Q1 — Frequência.** A consistência direcional sozinha é quase universal: a
líder bate **≥6/7 em 98%** dos dias e **7/7 em 85%**. Ou seja, quase todo dia
existe uma moeda que anda contra (quase) todos os seus pares. O "~88%" ÚTIL da
tese só aparece quando se exige **magnitude**: 7/7 **E** força ≥ 0.5 ATR = **62%**
dos dias. → *Direção consistente não seleciona o dia; magnitude sim.*

**Q2 — Direção e viés por moeda.** Liderar por FORÇA (moeda forte) e por FRAQUEZA
(moeda fraca) são igualmente frequentes (50/50). O viés por moeda confirma o
folclore com dados:

| Lidera por FRAQUEZA (anti-líder) | Lidera por FORÇA |
|---|---|
| **JPY 61%**, CHF 56%, CAD 52% | AUD 43%, GBP 44%, EUR 46%, NZD/USD ~47% |

**Q3 — Continuidade entre sessões.** A liderança **quase não persiste**: a líder
de asia continua em londres em só **13.5%** dos dias (acaso 12.5%); londres→ny
13.3%. Londres/NY "criam" líder novo em ~86% dos dias. → *A direção não gruda
entre sessões* (contraste com o a23/a32: o RANGE gruda).

**Q4 — Meia-vida.** A líder do dia é a líder do dia anterior em só **14%**
(acaso 12.5%) — meia-vida curta, persistência ~nula. Dentro do dia, a líder do
dia coincide com a de cada sessão em 32% (asia) / 41% (londres) / 39% (ny).

**Q5 — Limpo (7/7) vs sujo (6/7, 5/7).** A força cresce **monotonicamente** com a
consistência: 4/7 = 0.24 → 5/7 = 0.29 → 6/7 = 0.46 → **7/7 = 0.74** (~3×). O dia
7/7 limpo é materialmente maior — *"quão preponderante" importa muito*.

## Leitura
O fenômeno da preponderante é real e onipresente por direção, mas o que separa
um dia grande de um dia morto é a **magnitude/limpeza** (7/7), não a mera
existência de uma líder. E como a liderança **direcional** não persiste (Q3/Q4),
prever *quem* lidera é difícil — o que motiva o a29 (curva de detecção).
