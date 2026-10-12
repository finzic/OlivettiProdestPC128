; =====================================================================
; KEYJOY2 - two players on one keyboard, for PC128 BASIC 128
;
; Position independent: assembled at $9F00 but it runs wherever it is loaded.
; Everything is addressed relative to the start address BASE:
;   BASE+0  entry point (BRA to the code)       DEFUSR0=BASE : K=USR0(0)
;   BASE+2  signature "K2"
;   BASE+4  player 1 direction, STICK code 0-8   (arrow keys)
;   BASE+5  player 1 fire, 0 or 1                (Enter)
;   BASE+6  player 2 direction, STICK code 0-8   (W up, D right, S down, A left)
;   BASE+7  player 2 fire, 0 or 1                (Space)
;   BASE+8  code
; USR0 also returns player 1 as in KEYJOY: direction + 128 if Enter is held.
; Results are separate bytes so BASIC decodes them with PEEK (about 5x faster
; than AND and division).
;
;   CLEAR ,&H9EFF : LOADM "KEYJOY2" : B=&H9F00 : DEFUSR0=B
;   K=USR0(0) : D1=PEEK(B+4) : F1=PEEK(B+5) : D2=PEEK(B+6) : F2=PEEK(B+7)
; To load elsewhere give LOADM an offset from $9F00, e.g. $5000 (CLEAR ,&H4FFF):
;   LOADM "KEYJOY2",&HB100 : B=&H5000 : DEFUSR0=B
;
; Key scan codes (col<<4)|(line<<1) for the QWERTY pro128 keyboard map in MAME;
; the system PIA port B selects one key, bit 7 then reads 0 while it is down.
; =====================================================================

PIAB        equ $A7C1           ; hardware, the only absolute address

K_UP        equ $62
K_RIGHT     equ $32
K_DOWN      equ $42
K_LEFT      equ $52
K_ENTER     equ $68             ; line 4, column 6
K_W         equ $4A             ; line 5, column 4
K_D         equ $36             ; line 3, column 3
K_S         equ $46             ; line 3, column 4
K_A         equ $56             ; line 3, column 5
K_SPACE     equ $40             ; line 0, column 4

            org $9F00

KEYJOY2     bra  main           ; BASE+0
            fcc  "K2"           ; BASE+2
P1DIR       fcb  0              ; BASE+4
P1FIRE      fcb  0
P2DIR       fcb  0
P2FIRE      fcb  0              ; BASE+7

main        pshs cc
            orcc #$50           ; the monitor scans the keyboard on IRQ
            ldb  PIAB
            pshs b

            leay KEYS1+5,pcr
            bsr  scan
            leay DIRTAB,pcr
            ldb  b,y
            stb  P1DIR,pcr
            lda  #K_ENTER
            bsr  fire
            sta  P1FIRE,pcr

            leay KEYS2+5,pcr
            bsr  scan
            leay DIRTAB,pcr
            ldb  b,y
            stb  P2DIR,pcr
            lda  #K_SPACE
            bsr  fire
            sta  P2FIRE,pcr

            ldb  P1DIR,pcr      ; USR result: player 1 as in KEYJOY
            lda  P1FIRE,pcr
            beq  nofire
            orb  #$80
nofire      clra
            std  2,x
            puls a
            sta  PIAB
            lda  #2
            puls cc,pc

; Y = end of a key table (a 0 byte precedes the first key); B = mask
; bit0=up bit1=right bit2=down bit3=left
scan        clrb
nextkey     lda  ,-y
            beq  scandone
            sta  PIAB
            lda  PIAB
            coma
            rola                ; C = key down
            rolb
            bra  nextkey
scandone    rts

; A = key code; returns A = 1 if held, else 0
fire        sta  PIAB
            lda  PIAB
            coma
            rola                ; C = key down
            lda  #0             ; CLRA would clear C
            rola
            rts

KEYS1       fcb  0,K_UP,K_RIGHT,K_DOWN,K_LEFT
KEYS2       fcb  0,K_W,K_D,K_S,K_A
; STICK value for each mask; impossible or 3+ key combinations give 0
DIRTAB      fcb  0,1,3,2,5,0,4,0,7,8,0,0,6,0,0,0

            end  KEYJOY2
