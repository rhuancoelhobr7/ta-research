//+------------------------------------------------------------------+
//|                                       Test_CSSM_Parity_V141.mq5  |
//|  Critério de aceite nº 1 do v1.41: WM_BARS reproduz o v1.40      |
//|  EXATAMENTE. Cria dois handles iCustom — Cssm_v140_ref (cópia    |
//|  congelada do v1.40, git show main:Cssm.mq5) e Cssm (v1.41 em    |
//|  modo WM_BARS) — com parâmetros idênticos, e compara os buffers  |
//|  0-39 em InpNBars barras FECHADAS. PASS = diff máximo 0.0.       |
//|                                                                  |
//|  O handle v1.41 recebe DE PROPÓSITO horizonte/AutoGates ativos   |
//|  (18h/120h/true): em WM_BARS eles devem ser ignorados — se       |
//|  vazarem para o cálculo, o diff acusa.                           |
//|                                                                  |
//|  USO:                                                            |
//|   1. Compilar Cssm.mq5 e Cssm_v140_ref.mq5 em MQL5\Indicators    |
//|      e este script em MQL5\Scripts.                              |
//|   2. Arrastar o script num gráfico de par G8 com histórico       |
//|      (H1 recomendado). De preferência um gráfico SEM o CSSM      |
//|      anexado: os handles são ocultos, mas compartilham o         |
//|      prefixo de objetos do painel.                               |
//|   3. Ler a aba Experts do Journal: diff máximo por bloco de      |
//|      buffers + veredito PASS/FAIL.                               |
//|                                                                  |
//|  NOTA: as chamadas iCustom são POSICIONAIS. Se a ordem dos       |
//|  inputs de qualquer um dos indicadores mudar, este script tem    |
//|  de ser realinhado.                                              |
//+------------------------------------------------------------------+
#property script_show_inputs
#property version "1.00"

input ENUM_TIMEFRAMES InpTF     = PERIOD_H1;         // TF do teste
input int             InpNBars  = 100;               // barras fechadas comparadas
input string          InpOldInd = "Cssm_v140_ref";   // v1.40 congelado
input string          InpNewInd = "Cssm";            // v1.41

//--- espera o indicador terminar o primeiro cálculo
bool WaitReady(int h)
{
   for(int i=0;i<150;i++)
   {
      if(BarsCalculated(h)>0) return true;
      Sleep(200);
   }
   return false;
}

void OnStart()
{
   // v1.40: ordem legada — motor(6), estados(6), visual(7),
   // relacional(4), MTF desligado (grade não afeta buffers)
   int hOld=iCustom(_Symbol,InpTF,InpOldInd,
                    InpTF,16,64,500,300,8,
                    2.0,1.0,0.55,0.75,-1.0,-0.75,
                    true,true,false,12,16,9,false,
                    true,2.13,1.28,false,
                    false);
   // v1.41: modo(4) NA FRENTE — WM_BARS(0) com horizonte/AutoGates
   // propositalmente ativos (devem ser ignorados) — depois a mesma
   // lista legada, posição a posição
   int hNew=iCustom(_Symbol,InpTF,InpNewInd,
                    0,18.0,120.0,true,
                    InpTF,16,64,500,300,8,
                    2.0,1.0,0.55,0.75,-1.0,-0.75,
                    true,true,false,12,16,9,false,
                    true,2.13,1.28,false,
                    false);
   if(hOld==INVALID_HANDLE || hNew==INVALID_HANDLE)
   {
      Print("PARITY: iCustom falhou (old=",hOld,", new=",hNew,
            ") — confira os nomes/compilação dos indicadores.");
      return;
   }
   if(!WaitReady(hOld) || !WaitReady(hNew))
   {
      Print("PARITY: indicador nao calculou a tempo — aguarde o historico dos 28 pares e rode de novo.");
      IndicatorRelease(hOld); IndicatorRelease(hNew);
      return;
   }

   string blkName[5]={"M (0-7)","estado (8-15)","direcao (16-23)",
                      "br_hard (24-31)","br_soft (32-39)"};
   double blkMax[5]={0,0,0,0,0};
   int nBad=0;
   bool ok=true;
   for(int b=0;b<40 && ok;b++)
   {
      double va[],vb[];
      if(CopyBuffer(hOld,b,1,InpNBars,va)<InpNBars ||
         CopyBuffer(hNew,b,1,InpNBars,vb)<InpNBars)
      {
         Print("PARITY: CopyBuffer falhou no buffer ",b," — rode de novo.");
         ok=false;
         break;
      }
      for(int k=0;k<InpNBars;k++)
      {
         double d=MathAbs(va[k]-vb[k]);
         if(d>blkMax[b/8]) blkMax[b/8]=d;
         if(d>0.0) nBad++;
      }
   }
   if(ok)
   {
      double mx=0.0;
      for(int i=0;i<5;i++)
      {
         mx=MathMax(mx,blkMax[i]);
         Print(StringFormat("PARITY: %-16s max|diff| = %.3e",blkName[i],blkMax[i]));
      }
      Print(StringFormat("PARITY v1.40 x v1.41(WM_BARS)  %s  %d barras: %s  (max|diff|=%.3e, %d valores diferentes)",
            EnumToString(InpTF),InpNBars,(mx==0.0)?"PASS":"FAIL",mx,nBad));
   }
   IndicatorRelease(hOld);
   IndicatorRelease(hNew);
}
//+------------------------------------------------------------------+
