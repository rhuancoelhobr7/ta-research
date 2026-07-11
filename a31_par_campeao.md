# a31 — O par campeão dentro da moeda preponderante

Deliverable da bateria a28–a32. Dada a moeda LÍDER do dia, qual dos seus 7 pares
anda mais? Descritivo, por preço, 3116 dias. `results/*_a31/REPORT.md`.
Campeão ABS = maior range (pips); REL = maior range/ATR (controla largura
estrutural do par).

## Achados

**Q15 — Existe campeão claro?** Só em **37%** dos dias o campeão anda ≥1.3× o 2º
par; ele concentra mediana **23%** do range somado dos 7. → *Na maioria dos dias
o movimento é distribuído, sem um campeão dominante.*

**Q16 — Quanto o campeão anda A MAIS** (pergunta direta do Carlos). Além da média
dos outros 6 pares da mesma moeda:

| | mediana | p75 | p90 |
|---|---|---|---|
| pips | **+61** | +93 | +142 |
| ATR | **+0.67** | +0.88 | +1.26 |
| razão | 1.75× | 2.05× | 2.47× |

**Q17 — Estabilidade (líder → par campeão).** Concentrado mas não fixo (top-share
17-31%): USD→USDJPY 31%, JPY→USDJPY 30%, EUR→EURCHF 28%, CHF→CHFJPY 26%,
AUD→AUDNZD 23%, GBP→EURGBP 21%. Vários apontam para **JPY** (a anti-líder
frequente do a28).

**Q18 — Hipótese da anti-líder (o achado forte).** O campeão REL é exatamente
**líder × anti-líder em 55%** dos dias (baseline 1/7 = 14%); ABS em 36%. →
*Saber a líder E a anti-líder resolve boa parte da seleção do par.*
- **Caveat**: há componente MECÂNICO — o par líder×anti-líder tem o maior
  diferencial de força, logo tende ao maior movimento por construção. Mas 55%
  (não 100%) e o controle por ATR (REL) tornam a associação real e não trivial.

**Q19 — Identificável cedo?** O campeão do dia já é o campeão da sessão asia em
**43%** (baseline 14%) — parcialmente visível cedo (o a29 refina com M5).

## Ressalva operacional
Líder e anti-líder são conhecidas no FECHAMENTO (retrospecto). Usar isto para
seleção exige identificá-las cedo — que é o que o a29 mede (top-3 aos ~90 min).
Encadeando: *a29 estreita a líder para top-3 → a31 aponta o par provável
(líder×anti) → a25 confirma a amplitude por ATR.*
