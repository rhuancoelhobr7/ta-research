# -*- coding: utf-8 -*-
"""Relatorio profundo da bateria a33-a37 (+ a35-bis)."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, KeepTogether)

OUT = "a33_a37_relatorio.pdf"
NAVY = colors.HexColor("#1a2b4a"); BLUE = colors.HexColor("#2a6f97")
GREEN = colors.HexColor("#2e7d4f"); RED = colors.HexColor("#b3352e")
AMBER = colors.HexColor("#9c6b0a"); GRAYBG = colors.HexColor("#eef1f5")
LIGHT = colors.HexColor("#f7f9fb")

st = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=st["Heading1"], textColor=NAVY, fontSize=13.5,
                    spaceBefore=10, spaceAfter=3, fontName="Helvetica-Bold")
H2 = ParagraphStyle("H2", parent=st["Heading2"], textColor=BLUE, fontSize=10.8,
                    spaceBefore=7, spaceAfter=2, fontName="Helvetica-Bold")
BODY = ParagraphStyle("BODY", parent=st["Normal"], fontSize=9.1, leading=12.6,
                      alignment=TA_JUSTIFY, spaceAfter=4)
SMALL = ParagraphStyle("SMALL", parent=BODY, fontSize=7.8, textColor=colors.HexColor("#555"))
CELL = ParagraphStyle("CELL", parent=BODY, fontSize=8, leading=10.4, spaceAfter=0, alignment=TA_LEFT)
CELLB = ParagraphStyle("CELLB", parent=CELL, fontName="Helvetica-Bold")
CELLW = ParagraphStyle("CELLW", parent=CELL, textColor=colors.white, fontName="Helvetica-Bold")
TITLE = ParagraphStyle("TITLE", parent=st["Title"], textColor=NAVY, fontSize=21, leading=25, spaceAfter=2)
SUB = ParagraphStyle("SUB", parent=BODY, fontSize=10.5, textColor=BLUE, spaceAfter=1, alignment=TA_LEFT)

story = []
def rule(c=BLUE, w=1.1, sb=1, sa=6): story.append(HRFlowable(width="100%", thickness=w, color=c, spaceBefore=sb, spaceAfter=sa))
def chip(t, c): return Paragraph(f"<b>{t}</b>", ParagraphStyle("c", parent=CELL, textColor=c, fontName="Helvetica-Bold", fontSize=7.8))

def kvtable(rows, widths, header=True, shade_row=None):
    data = []
    for i, r in enumerate(rows):
        if header and i == 0:
            data.append([Paragraph(f"<b>{c}</b>", CELLW) for c in r])
        else:
            data.append([c if hasattr(c, "style") else Paragraph(str(c), CELL) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    s = [("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#c9d2dd")),
         ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("TOPPADDING",(0,0),(-1,-1),2.5),
         ("BOTTOMPADDING",(0,0),(-1,-1),2.5), ("LEFTPADDING",(0,0),(-1,-1),5)]
    if header: s.append(("BACKGROUND",(0,0),(-1,0),NAVY))
    for i in range(1, len(rows)):
        if i % 2 == 0: s.append(("BACKGROUND",(0,i),(-1,i),LIGHT))
    if shade_row: s.append(("BACKGROUND",(0,shade_row),(-1,shade_row),colors.HexColor("#eef6f0")))
    t.setStyle(TableStyle(s)); return t

def box(flowable, border, bg):
    tb = Table([[flowable]], colWidths=[170*mm])
    tb.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),bg),("BOX",(0,0),(-1,-1),0.8,border),
        ("LEFTPADDING",(0,0),(-1,-1),9),("RIGHTPADDING",(0,0),(-1,-1),9),
        ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7)]))
    return tb

# ---------- capa + sumario ----------
story.append(Spacer(1,2))
story.append(Paragraph("Bateria a33-a37 — Relatório", TITLE))
story.append(Paragraph("Da cadeia composta à direção: existe sistema?", SUB))
story.append(Spacer(1,2)); rule(NAVY,2,0,5)
story.append(Paragraph("Repositório <b>ta-research</b> &nbsp;·&nbsp; 2026-07-11 &nbsp;·&nbsp; PR #19 &nbsp;·&nbsp; "
    "base M5 3 anos (~790 dias) + M15 ~10 anos &nbsp;·&nbsp; <b>pytest 180 verde</b>", SMALL))
story.append(Spacer(1,5))
story.append(box(Paragraph(
    "<b>Pergunta da bateria: as peças positivas isoladas (top-3 de moedas aos 90 min, par = "
    "líder×anti-líder, ATR de sessão, calendário) formam um SISTEMA quando compostas?</b> "
    "Resposta: <b>não há sistema de amplitude</b> — a cadeia composta colapsa (a33) e o ATR de "
    "sessão sozinho domina. Emergem <b>dois sinais direcionais modestos, confirmados out-of-sample</b>: "
    "(1) o top-3 de moedas por z-score@180min (a34/a35, 1º preditor OOS do projeto); (2) a persistência "
    "de direção de preço 4h->15h (a35-bis). Ambos chegam tarde (3-4h no dia) e são fracos. O "
    "<b>CSS/CSSM é confirmado como puramente DESCRITIVO</b> — sem valor preditivo (a34) nem concorrente "
    "(a37). Tema transversal: <b>o sinal está no preço</b>, e chega quando o grosso do movimento já passou.",
    CELL), BLUE, GRAYBG))

# ---------- 1. método ----------
story.append(Paragraph("1. Objetivo e método", H1)); rule()
story.append(Paragraph(
    "<b>Mudança de objetivo</b> (registrada no CHANGELOG): abandona-se a engenharia reversa do "
    "especialista; o alvo passa a ser <b>acertar as moedas/pares de grande movimento direcional</b>, "
    "usando os achados positivos e evitando o que é nulo. A motivação é honesta: os positivos foram "
    "validados <i>isoladamente</i>; a cadeia operável nunca foi medida ponta a ponta, e o par "
    "líder×anti-líder (a31, 55%) pressupõe conhecer a líder — coisa que o a29 diz NÃO se conhecer "
    "cedo. Sem o número composto, há peças, não sistema.", BODY))
story.append(Paragraph(
    "<b>Disciplina metodológica</b> (regras duras do repositório): pré-registro de cada estudo com o "
    "código congelado ANTES do resultado; barras fechadas e sem lookahead; split temporal 70/30; "
    "bootstrap em blocos (semanais) para intervalos de confiança; correção de Benjamini-Hochberg sobre "
    "a família inteira de testes; reality check por permutação (máximo entre células); controle negativo. "
    "Resultado nulo é resultado publicável e a maioria dos achados é nula, reportada sem suavização.", BODY))
story.append(Paragraph(
    "<b>Holdout</b>: o corte final de dias foi tratado como recurso escasso e IRREVERSÍVEL. O a34 "
    "(varredura exploratória) usou apenas os primeiros 50% dos dias; o a35 confirmou o vencedor UMA "
    "única vez numa fatia pristina reservada [q50, q70), nunca vista pela varredura. Essa fatia foi "
    "consumida e não se repete.", BODY))

# ---------- 2. os estudos ----------
story.append(Paragraph("2. Os estudos, em profundidade", H1)); rule()

# a33
story.append(Paragraph("a33 — A cadeia composta, ponta a ponta, líquida de custo", H2))
story.append(Paragraph("Uma execução do pipeline como seria operado: aos 90 min, estimar o top-3 de "
    "moedas por momentum de preço; dentro do top-3, líder = maior score, anti-líder = menor entre as 8; "
    "par candidato = líder×anti-líder; comparar amplitude com ATR de sessão. 631 dias de research; spread "
    "real por par; holdout intocado.", BODY))
story.append(kvtable([
    ["P(par candidato = par de maior range do dia)", "Valor"],
    [Paragraph("<b>Cadeia (momentum -> líder×anti)</b>", CELLB), Paragraph("<b>4.1%</b>", CELLB)],
    ["Baseline: maior ATR de sessão (a25)", "29.8%"],
    ["Baseline: persistência (maior range de ontem)", "23.8%"],
    ["Aleatório (1/28)", "3.6%"],
    ["Referência a31 (conhecendo a líder)", "14%"]],
    [120*mm, 50*mm]))
story.append(Spacer(1,3))
story.append(Paragraph("<b>Decomposição do colapso.</b> A líder estimada = a verdadeira em só 15.7% dos "
    "dias. E MESMO com a líder correta, o par líder×anti-líder é o maior-range global em apenas 10.1% — "
    "porque o 55% do a31 era o campeão DENTRO dos 7 pares da líder, não o maior-range entre os 28. O "
    "candidato tem excesso de ATR <b>-0.08</b> (abaixo da média dos 28) e captura 72.7 pips vs 143 do "
    "baseline ATR. <b>Veredito pré-registrado: a cadeia NÃO se sustenta</b> — as peças não compõem; o ATR "
    "de sessão domina.", BODY))

# a34
story.append(Paragraph("a34 — Varredura de métricas (exploratório)", H2))
story.append(Paragraph("Grade pré-registrada de 70 células: 8 famílias de métrica (momentum, retorno/ATR, "
    "Efficiency Ratio, z-score, rank cross-sectional, dispersão, range/vol, e CSS/CSSM como controle) x 7 "
    "janelas (5 a 180 min) x régua top-3. Research = primeiros 50% dos dias; holdout intocado. Todas as "
    "travas ligadas (BH, reality check por permutação, controle).", BODY))
story.append(kvtable([
    ["Célula (janela 180 min)", "top-3", "vs controle"],
    [Paragraph("<b>z-score@180 (top-1)</b>", CELLB), Paragraph("<b>0.508</b>", CELLB), "reality p95 = 0.461"],
    ["css@180", "0.487", "colado no preço"],
    ["cssm@180", "0.485", "colado no preço"],
    ["momentum / rank / dispersão / ER @180", "0.482", "colados"],
    ["Acaso (top-3)", "0.375", "-"]],
    [95*mm, 35*mm, 40*mm], shade_row=1))
story.append(Spacer(1,3))
story.append(Paragraph("13 células sobrevivem a BH + reality check, <b>TODAS em janelas longas (90-180 "
    "min)</b> — nada precoce passa (confirma a29/a33: não há detecção precoce). As métricas de preço e o "
    "CSS/CSSM ficam indistinguíveis (~0.48) — o <b>controle confirma o a30 de forma independente</b>: o "
    "CSS é transformação do preço. O candidato para o holdout é o z-score@180.", BODY))

# a35
story.append(Paragraph("a35 — Confirmação no holdout (uma vez só)", H2))
story.append(Paragraph("As células pré-declaradas do a34, sem re-otimizar, confirmadas UMA vez na fatia "
    "pristina [q50, q70) (154 dias). O z-score usa média/desvio do research (congelados).", BODY))
story.append(kvtable([
    ["Célula", "holdout", "IC95", "edge mantido", "confirma?"],
    [Paragraph("<b>z-score@180</b>", CELLB), Paragraph("<b>0.506</b>", CELLB),
     "[0.422, 0.591]", "99%", chip("SIM", GREEN)],
    ["css@180", "0.433", "[0.350, 0.516]", "52%", chip("NÃO", RED)],
    ["cssm@180", "0.439", "[0.357, 0.522]", "59%", chip("NÃO", RED)]],
    [34*mm, 24*mm, 42*mm, 34*mm, 26*mm], shade_row=1))
story.append(Spacer(1,3))
story.append(Paragraph("<b>Primeiro preditor confirmado out-of-sample do projeto.</b> O z-score mantém "
    "0.506 (research 0.508), IC exclui o acaso, edge 99% preservado. O css/cssm FALHAM (IC inclui 0.375) "
    "— normalizar cada moeda pela PRÓPRIA volatilidade histórica é o que agrega e sobrevive OOS, e é mais "
    "robusto que o momentum bruto ou o CSS. <b>Escopo honesto</b>: é régua B (top-3 de moedas, não a líder "
    "exata, que segue fraca ~0.24), latência de 180 min (3h no dia), edge modesto (~1.35x o acaso). NÃO "
    "conserta a cadeia-par do a33.", BODY))

# a35-bis
story.append(Paragraph("a35-bis — Persistência de direção de preço (confirmação OOS)", H2))
story.append(Paragraph("Confirma o 2o sinal do a36: o sinal do movimento de uma moeda em T0+4h sustenta "
    "até 15h. Regra com ZERO parâmetros livres (k e fim fixos do a17); confirma-se robustez, estabilidade "
    "temporal e a cauda recente held-out.", BODY))
story.append(kvtable([
    ["Métrica", "Valor"],
    ["Research (&lt;q70)", "0.640"],
    [Paragraph("<b>Cauda OOS (&gt;=q70)</b>", CELLB), Paragraph("<b>0.646</b> — IC [0.622, 0.668] exclui 0.5", CELLB)],
    ["Edge mantido", "104%"],
    ["Estabilidade (4 blocos consecutivos)", "0.63-0.65, todos com IC &gt; 0.5"],
    ["Magnitude residual após 4h", "+0.02 (minúscula)"]],
    [70*mm, 100*mm], shade_row=2))
story.append(Spacer(1,3))
story.append(Paragraph("<b>Confirma o SINAL, com caveat de magnitude.</b> A direção sustenta 65% até o "
    "fim, out-of-sample, estável em todos os períodos. MAS a magnitude residual após 4h é ~2% do move "
    "típico — por 4h quase todo o movimento LÍQUIDO já foi. Leitura honesta: é sinal de "
    "CONFIRMAÇÃO/MANUTENÇÃO (a moeda raramente inverte), útil para segurar uma posição já aberta, NÃO um "
    "edge de entrada tardia às 4h.", BODY))

# a36
story.append(Paragraph("a36 — Direção: calendário × confirmação de preço", H2))
story.append(Paragraph("Combina as duas peças ex-ante nunca juntadas: notícia HIGH de uma moeda (a18) e "
    "confirmação de preço em T0+k (a17). Calendário 2024-07 a 2026-07, com surpresa (realizado-esperado).", BODY))
story.append(kvtable([
    ["Regra (k=4h, fim=15h)", "P(sustenta)"],
    [Paragraph("Combinado (evento HIGH + preço)", CELL), "0.618"],
    [Paragraph("<b>Só preço (confirmação)</b>", CELLB), Paragraph("<b>0.642</b>", CELLB)],
    ["Só calendário (evento + persistência)", "0.511"],
    ["Persistência / acaso", "0.505 / 0.500"]],
    [120*mm, 50*mm], shade_row=2))
story.append(Spacer(1,3))
story.append(Paragraph("<b>A combinação calendário×preço é NULA</b>: o combinado (0.618) não supera a "
    "confirmação de preço isolada (0.642) — no 4h é até pior. O calendário e a persistência ficam no acaso; "
    "a surpresa não ajuda. <b>Mas a confirmação de PREÇO sozinha é o sinal real</b> (0.642, o mesmo do "
    "a35-bis) — a rota viva de direção é o preço, não o calendário.", BODY))

# a37
story.append(Paragraph("a37 — Fechar o caveat do a26b: controle pareado por volatilidade", H2))
story.append(Paragraph("O a26b sugeriu que o CSS servia como confirmação concorrente (MFE 1.46x o "
    "controle), mas o controle não era pareado por volatilidade. Aqui, cada evento de alinhamento é pareado "
    "a um controle não-alinhado com volatilidade prévia semelhante (decil de range anterior).", BODY))
story.append(kvtable([
    ["Comparação", "MFE (pips)", "razão"],
    ["Alinhado (CSS)", "16.8", "-"],
    ["Controle NÃO pareado (o a26b)", "11.5", "1.46x"],
    [Paragraph("<b>Controle PAREADO por volatilidade</b>", CELLB), Paragraph("<b>15.6</b>", CELLB), Paragraph("<b>1.08x</b>", CELLB)]],
    [95*mm, 35*mm, 40*mm], shade_row=3))
story.append(Spacer(1,3))
story.append(Paragraph("O alinhamento ocorre em regime muito mais volátil (vol prévia 47 vs 27). Ao parear, "
    "o incremento SOME (1.46x -> 1.08x): o extra do a26b era <b>clustering de volatilidade, não valor do "
    "CSS</b>. <b>O badge de confirmação concorrente cai</b>; o CSS/CSSM fica APENAS descritivo — sem valor "
    "preditivo (a24/a34) nem concorrente (a37). INDICATOR_CHANGELOG e a proposta de badge atualizados.", BODY))

# ---------- 3. os dois sinais ----------
story.append(Paragraph("3. Os dois sinais confirmados out-of-sample", H1)); rule()
story.append(box(Paragraph(
    "<b>1. Top-3 de moedas por z-score@180min (a35).</b> Aos ~3h do dia, ranquear as 8 moedas pelo "
    "z-score do retorno (normalizado pela volatilidade histórica da moeda) acerta o top-3 em 0.506 no "
    "holdout (acaso 0.375). É direcional (quais 3 moedas estão fortes), não seleciona par por amplitude. "
    "<br/><br/>"
    "<b>2. Persistência de direção 4h->15h (a35-bis).</b> A direção do movimento às 4h sustenta até o fim "
    "em 0.646 OOS (acaso 0.50), estável em todos os períodos — mas com magnitude residual minúscula "
    "(sinal de manutenção, não de entrada). <br/><br/>"
    "<b>Em comum</b>: ambos são DIRECIONAIS, chegam 3-4h no dia (tarde), têm edge modesto e vivem no "
    "PREÇO. Nenhum crava a moeda exata cedo; nenhum resgata a seleção de par por amplitude (que segue "
    "sendo o ATR de sessão, a25).", CELL), GREEN, colors.HexColor("#eef6f0")))

# ---------- 4. o que nao funciona ----------
story.append(Paragraph("4. O que NÃO funciona (negativos pré-registrados)", H1)); rule()
for x in [
    "<b>A cadeia composta de amplitude</b> (a33): P(par de maior range) 4.1% ~ acaso, vs 29.8% do ATR de sessão. As peças isoladas não formam sistema.",
    "<b>O CSS/CSSM como preditor</b> (a34): colado nas métricas de preço; não agrega informação. É transformação do preço.",
    "<b>O CSS como confirmação concorrente</b> (a37): o aparente 1.46x do a26b era clustering de volatilidade; some ao parear. CSS é apenas descritivo.",
    "<b>O calendário como sinal direcional</b> (a36): não agrega sobre a confirmação de preço; evento+persistência fica no acaso.",
    "<b>Detecção precoce</b> (a34): nenhuma métrica em janelas de 5-60 min sobrevive; só 90-180 min.",
]:
    story.append(Paragraph("• " + x, BODY))

# ---------- 5. implicacoes ----------
story.append(Paragraph("5. Implicações e próximos passos", H1)); rule()
story.append(Paragraph(
    "<b>Produto de seleção de par por amplitude</b>: permanece o ranqueador por ATR de sessão (a25). "
    "Nada da bateria o supera. <b>Indicador CSS/CSSM</b>: confirmado como descritivo — nenhum badge de "
    "sinal entra; a leitura de força/geometria serve ao olho, não à decisão. <b>Sinal direcional "
    "probabilístico</b>: no máximo, exibir o top-3 de moedas por z-score@180min (confirmado OOS, edge "
    "modesto), marcado com latência (3h) e confiança, jamais como sinal de T0.", BODY))
story.append(Paragraph(
    "<b>Próximos passos candidatos</b> (exigiriam novo pré-registro / novo holdout, pois a fatia pristina "
    "foi consumida): (i) medir o valor ECONÔMICO do z-score@180 e da persistência de direção com custos e "
    "gestão, não só acurácia; (ii) o refinamento forming-bar do a29 (leitura intra-barra pode adiantar a "
    "latência); (iii) reservar uma nova fatia temporal antes de qualquer nova varredura.", BODY))

story.append(Spacer(1,4)); rule(NAVY,1,2,3)
story.append(Paragraph(
    "Fonte: CHANGELOG.md e results/*/REPORT.md do repositório (PR #19). Pré-registro por estudo, holdout "
    "consumido só no a35, pytest 180 verde. Não tocados: specialist_calls/ledger, definição v1, splits_days. "
    "Todos os números são out-of-sample onde indicado; resultados nulos reportados sem suavização.", SMALL))

def footer(c, d):
    c.saveState(); c.setFont("Helvetica", 7.5); c.setFillColor(colors.HexColor("#888"))
    c.drawString(20*mm, 12*mm, "Bateria a33-a37 — Relatório · ta-research · 2026-07-11")
    c.drawRightString(190*mm, 12*mm, "Página %d" % d.page)
    c.setStrokeColor(colors.HexColor("#ccc")); c.line(20*mm, 15*mm, 190*mm, 15*mm); c.restoreState()

doc = SimpleDocTemplate(OUT, pagesize=A4, topMargin=11*mm, bottomMargin=18*mm,
                        leftMargin=20*mm, rightMargin=20*mm,
                        title="Bateria a33-a37 — Relatório", author="Claude Code")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("PDF gerado:", OUT)
