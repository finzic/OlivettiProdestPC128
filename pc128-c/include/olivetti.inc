* olivetti.inc - equates and macros for 6809 assembly modules linked with C programs
* (lwasm, relocatable object format). Include with:   INCLUDE "olivetti.inc"
*
* Calling convention (CMOC): arguments pushed right to left, each at least 16 bits;
* in a routine without a frame the first argument is at 2,S (a byte argument at 3,S).
* Return 8-bit values in B, 16-bit values in D. Preserve U, Y, S and DP; A, B, X, CC are free.
* Exported C names get a leading underscore:  EXPORT _myfunc  -> void myfunc(...);

* ---- monitor call:  SYSCALL PUTC   ==  SWI / FCB $02
SYSCALL MACRO
        SWI
        FCB     \1
        ENDM

* ---- extramonitor call (after xm_begin()):  XMCALL XM.LINE  ==  LDB #26 / SWI2
XMCALL  MACRO
        LDB     #\1
        SWI2
        ENDM

* ---- monitor services (SWI + byte)
PUTC    EQU     $02
FRM0    EQU     $04
FRM1    EQU     $06
BIIP    EQU     $08
GETC    EQU     $0A
KTST    EQU     $0C
DRAW    EQU     $0E
PLOT    EQU     $10
CHPL    EQU     $12
GETP    EQU     $14
LPIN    EQU     $16
GETL    EQU     $18
GETS    EQU     $1A
JOYS    EQU     $1C
NOTE    EQU     $1E
K7CO    EQU     $20
K7MO    EQU     $22
PRCO    EQU     $24
DKCO    EQU     $26
DKFO    EQU     $2A
SETP    EQU     $3C
MOUSEB  EQU     $3E
MOUSE   EQU     $40
RSCO    EQU     $42

* ---- monitor RAM
STATUS  EQU     $2019
FORME   EQU     $2029
COLOUR  EQU     $202B
PLOTX   EQU     $2032
PLOTY   EQU     $2034
CHDRAW  EQU     $2036
TEMPO   EQU     $2039
DUREE   EQU     $203B
TIMBRE  EQU     $203D
OCTAVE  EQU     $203E
PR.OPC  EQU     $2042
PR.STA  EQU     $2043
DK.OPC  EQU     $2048
DK.DRV  EQU     $2049
DK.TRK  EQU     $204A
DK.SEC  EQU     $204C
DK.NUM  EQU     $204D
DK.STA  EQU     $204E
DK.BUF  EQU     $204F
CONFIG  EQU     $2079
RS.OPC  EQU     $2082
RS.STA  EQU     $2083

* ---- hardware
PIA.A   EQU     $A7C0           bit 5: monitor ROM page (1 = BASIC side, 0 = extramonitor)
RAMPAG  EQU     $A7E5           RAM page mapped at $6000-$9FFF
EXTRAMON EQU    $EFFB           toggles the monitor ROM page

* ---- extramonitor function numbers
XM.CIRCLE EQU   24
XM.PSETXY EQU   25
XM.LINE EQU     26
XM.BOX  EQU     27
XM.CHOIX EQU    28
XM.PAINT EQU    29
XM.MIG  EQU     30
XM.MOVFM EQU    62
XM.MOVMF EQU    63
XM.MOVAF EQU    64

* ---- extramonitor RAM
SAVSTK  EQU     $2175
ZPERR   EQU     $2185
COULEUR EQU     $219F
TRATYP  EQU     $21A0
XXXXX   EQU     $21A1
YYYYY   EQU     $21A3
XL      EQU     $21A5
YB      EQU     $21A7
XR      EQU     $21A9
YT      EQU     $21AB
FILFLG  EQU     $21EF
MACP    EQU     $227D
WITH    EQU     $2288
