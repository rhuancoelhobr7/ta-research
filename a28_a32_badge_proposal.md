# Proposta de badge do painel — o que (e o que NÃO) entra do a28–a32

Registro de proposta, sujeito à regra dura do repo: **nada entra em CSS/CSSM sem
sobreviver a BH + out-of-sample**, sempre marcado como PROBABILÍSTICO e com a
latência conhecida, **nunca** como sinal de T0. Este documento traduz os achados
da bateria numa proposta de leitura para o painel — a decisão de implementar é
do dono.

## O que os dados autorizam

1. **Não** existe sinal para "cravar a líder na abertura" (a29 régua A nula;
   a24 já era nulo). → Nenhum badge de seleção em T0.
2. **Existe** um sinal precoce MODESTO para "estreitar a líder para top-3" a
   partir de ~90 min de Tóquio, no TF rápido (a29: M5 top-3 0.48 vs 0.375 do
   acaso, BH/OOS; 74% do movimento ainda por vir). O detector mais simples é o
   **momentum de preço** (quem subiu mais até agora) — o CSS não agrega sobre ele
   (a30).
3. **Dado** um palpite de líder E de anti-líder, o par provável de maior movimento
   é **líder × anti-líder** (a31: 55% vs 14% do acaso; +0.67 ATR a mais).
4. **Amplitude** por par continua melhor explicada por **ATR de sessão** (a25) e
   a memória de volatilidade entre sessões (a32).

## Badge proposto: "Candidata do dia (probabilístico)"

Ative **somente após ~90 min da abertura de Tóquio** (latência fixa, exibida). NÃO
mostrar antes — antes disso está no acaso.

- **Top-3 de força** (por momentum de preço do dia / linha do CSS): destacar as
  3 moedas mais fortes e as 3 mais fracas acumuladas desde a abertura. Marcar a
  confiança medida: *"top-3 ~48% (acaso 37.5%), ~74% do range ainda na mesa"*.
- **Par sugerido** = a mais forte do top-3 × a mais fraca do bottom-3
  (líder×anti-líder). Rótulo: *"par candidato ~55% (probabilístico)"*.
- **Amplitude esperada**: ranquear os candidatos por ATR de sessão (a25) — o
  badge diz MOVIMENTO esperado, não direção garantida nem lucro.

### Marcações obrigatórias no badge
- selo **"probabilístico"** e a **latência** ("válido após 90 min de Tóquio");
- a **confiança OOS** medida (top-3 ~48%, par ~55%), nunca arredondada para cima;
- aviso de **custo do atraso** (quanto do range já passou naquele instante);
- **régua A (líder exata) é nula** — o badge nunca aponta UMA moeda como certa.

## O que explicitamente NÃO entra
- Sinal em T0 / na abertura (nulo em todos os estudos).
- Volume como seletor de moeda (a30: cego à direção).
- Qualquer leitura que trate o CSS como preditor em vez de confirmação.
- Persistência de liderança dia-a-dia (a28 Q4: ~acaso).

## Gate de implementação
Antes de qualquer mudança no MQ5: reproduzir a curva do a29 na barra em formação
(forming-bar, refinamento v2 — pode adiantar/atrasar a latência de 90 min) e
revalidar OOS. Só então discutir o badge no indicador.
