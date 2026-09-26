* Encoding: UTF-8.
*Valor Sef-direction (criatividade + tomar as suas pr�prias decis�es)*

RECODE
  ipcrtiv impfree
  (1=6)  (2=5)  (3=4)  (4=3)  (5=2)  (6=1)  (SYSMIS=SYSMIS)  INTO  crt_r
  fre_r .
VARIABLE LABELS crt_r 'criatividade recodificada - escala invertida' /fre_r
  'Tomar as suas proprias decisoes recodificada - escala invertida'.
EXECUTE .

COMPUTE SD = mean(crt_r, fre_r).
VARIABLE LABELS SD 'Auto-direcao'.
EXECUTE .


*Valor "benevolencia" (ajudar as pessoas + dedica��o aos pr�ximos)*

RECODE
  iphlppl
  (SYSMIS=SYSMIS)  (1=6)  (2=5)  (3=4)  (4=3)  (5=2)  (6=1)  INTO  help_r .
VARIABLE LABELS help_r 'ajudar as pessoas recodificada (escala'+
 ' invertida)'.
EXECUTE .

RECODE
  iplylfr
  (SYSMIS=SYSMIS)  (1=6)  (2=5)  (3=4)  (4=3)  (5=2)  (6=1)  INTO  dedic_r .
VARIABLE LABELS dedic_r 'dedicado aos proximos (escala investida)'.
EXECUTE .

COMPUTE BE = mean(help_r, dedic_r) .
VARIABLE LABELS BE 'Benevolencia' .
EXECUTE .

*Valor universalismo (tratamento igual + ouvir as pessoas + preocupa��o com a natureza)*

RECODE
  ipeqopt ipudrst impenv
  (1=6)  (2=5)  (3=4)  (4=3)  (5=2)  (6=1)  (SYSMIS=SYSMIS)  INTO  igual_r
  ouvir_r  natur_r .
VARIABLE LABELS igual_r 'tratar os outros como iguais (escala'+
 ' invertida)' /ouvir_r 'ouvir as pessoas (escala invertida)' /natur_r
  'preocupacao com a natureza (escala invertida)'.
EXECUTE .

COMPUTE UN = mean(igual_r, ouvir_r, natur_r).
VARIABLE LABELS UN 'Universalismo)' .
EXECUTE .

COMPUTE UN2 = mean(igual_r, ouvir_r).
VARIABLE LABELS UN2 'Universalismo2)' .
EXECUTE .

*Valor "stimulation" (fazer coisas diferentes + procura aventura)*

RECODE
  impdiff ipadvnt
  (1=6)  (2=5)  (3=4)  (4=3)  (5=2)  (6=1)  (SYSMIS=SYSMIS)  INTO  difer_r
  aven_r .
VARIABLE LABELS difer_r ' fazer coisas diferentes (escala invertida)'
 /aven_r 'procura aventura (escala invertida)'.
EXECUTE .


COMPUTE STM = mean(difer_r, aven_r).
VARIABLE LABELS STM 'Stimulation' .
EXECUTE .


*Valor "Hedonism" (passar bons momentos + fazer coisas que lhe d�o prazer)*

RECODE
  ipgdtim impfun
  (1=6)  (2=5)  (3=4)  (4=3)  (5=2)  (6=1)  (SYSMIS=SYSMIS)  INTO  bonsm_r
  praz_r .
VARIABLE LABELS bonsm_r 'passar bons momentos (escala invertida)'
 /praz_r 'fazer coisas que lhe dao prazer (escala invertida)'.
EXECUTE .


COMPUTE HE = mean(bonsm_r, praz_r)  .
VARIABLE LABELS HE 'Hedonism' .
EXECUTE .

*Valor "Achievement" (mostrar as suas capacidades + sucesso)*

RECODE
  ipshabt ipsuces
  (1=6)  (2=5)  (3=4)  (4=3)  (5=2)  (6=1)  (SYSMIS=SYSMIS)  INTO  habil_r
  suce_r .
VARIABLE LABELS habil_r 'mostrar as suas capacidades (escala invertida)' /suce_r 'sucesso (escala invertida)'.
EXECUTE .


COMPUTE AC = mean(habil_r, suce_r) .
VARIABLE LABELS AC 'Achievement' .
EXECUTE .


*Valor poder (ser rico + fazer o que diz)*

RECODE
  imprich iprspot
  (1=6)  (2=5)  (3=4)  (4=3)  (5=2)  (6=1)  (SYSMIS=SYSMIS)  INTO  rico_r
  autor_r .
VARIABLE LABELS rico_r 'ser rico (escala invertida)' /autor_r 'fazer o que ele diz (escala invertida)'.
EXECUTE .


COMPUTE PO = mean(autor_r, rico_r) .
VARIABLE LABELS PO 'Poder' .
EXECUTE .


*Valor seguran�a (viver num s�tio seguro + Estado defender os cidad�os)*


RECODE
  impsafe ipstrgv
  (1=6)  (2=5)  (3=4)  (4=3)  (5=2)  (6=1)  (SYSMIS=SYSMIS)  INTO  seg_r
  Estdef_r .
VARIABLE LABELS seg_r ' viver sitio seguro (escala invertida)' /Estdef_r
  'Estado defender os cidadaos (escala invertida)'.
EXECUTE .


COMPUTE SEC = mean(seg_r, Estdef_r) .
VARIABLE LABELS SEC 'Segurança' .
EXECUTE .


*Valor conformismo (fazer o que lhes mandam + portar-se como deve ser)*


RECODE
  ipfrule ipbhprp
  (1=6)  (2=5)  (3=4)  (4=3)  (5=2)  (6=1)  (SYSMIS=SYSMIS)  INTO  obey_r
  behav_r .
VARIABLE LABELS obey_r 'fazer o que mandam (escala invertida)' /behav_r
  'portar-se sempre como deve ser (escala invertida)'.
EXECUTE .

COMPUTE CON = mean(obey_r, behav_r) .
VARIABLE LABELS CON 'Conformismo' .
EXECUTE .


*Valor tradi��o (humilde + import�ncia � tradi��o)*


RECODE
  ipmodst imptrad
  (1=6)  (2=5)  (3=4)  (4=3)  (5=2)  (6=1)  (SYSMIS=SYSMIS)  INTO  humil_r
  trad_r .
VARIABLE LABELS humil_r 'humildade (escala invertida)' /trad_r 'tradição (escala invertida)'.
EXECUTE .

COMPUTE TR = mean(humil_r, trad_r) .
VARIABLE LABELS TR 'Tradição' .
EXECUTE .

*M�dia dos scores individuais*

COMPUTE mscor_21 = mean(help_r, dedic_r, igual_r, ouvir_r, natur_r, difer_r, aven_r, bonsm_r, praz_r, habil_r, suce_r, rico_r, autor_r, seg_r,  estdef_r, obey_r,  behav_r, humil_r, trad_r, crt_r, fre_r )  .
EXECUTE .

VARIABLE LABELS mscor_21 'Mean score - conjunto 21 indicadores'.


compute crt_ms = crt_r - mscor_21. 
compute fre_ms = fre_r - mscor_21 .
compute help_ms = help_r - mscor_21 .
compute dedic_ms = dedic_r - mscor_21. 
compute igual_ms = igual_r - mscor_21 .
compute ouvir_ms = ouvir_r - mscor_21 .
compute natur_ms = natur_r - mscor_21 .
compute difer_ms = difer_r - mscor_21 .
compute aven_ms = aven_r - mscor_21 .
compute bonsm_ms = bonsm_r - mscor_21 .
compute praz_ms = praz_r - mscor_21 .
compute habil_ms = habil_r - mscor_21 .
compute suce_ms = suce_r - mscor_21 .
compute rico_ms = rico_r - mscor_21 .
compute autor_ms = autor_r - mscor_21. 
compute seg_ms = seg_r - mscor_21. 
compute estde_ms = estdef_r - mscor_21 .
compute obey_ms = obey_r - mscor_21 .
compute behav_ms = behav_r - mscor_21 .
compute humil_ms = humil_r - mscor_21. 
compute trad_ms = trad_r - mscor_21 .


compute sdms =mean(crt_ms, fre_ms) . 
compute bems = mean(help_ms,dedic_ms) .
compute unms = mean(igual_ms, ouvir_ms, natur_ms)  .
compute un2ms =  mean(igual_ms, ouvir_ms)  .
compute stmms = mean(difer_ms,aven_ms).
compute hems = mean( bonsm_ms,praz_ms) .
compute acms = mean(suce_ms,habil_ms). 
compute poms = mean (rico_ms, autor_ms).
compute po2ms=autor_ms.
compute secms = mean(seg_ms,estde_ms).
compute conms = mean(obey_ms, behav_ms).
compute trms = mean(humil_ms,trad_ms). 


compute STms = mean(bems, unms).
compute ST2ms=mean(bems, un2ms).
compute SEms = mean(poms, acms).
compute SE2ms=mean(po2ms, acms).
compute COms = mean(conms, secms, trms).
compute OCms = mean(sdms,stmms, hems).

compute ST = mean(be, un).
compute ST2=mean(be, un2).
compute SE = mean(po, ac).
compute CO = mean(con, sec, tr).
compute OC = mean(sd,stm, he).
Execute.


*Year born->Generation*

if yrbrn <1946 generation=1. 
if yrbrn >1945 & yrbrn < 1966 generation=2. 
if yrbrn >1965 & yrbrn < 1986 generation=3. 
if yrbrn >1985 generation=4. 
execute.



