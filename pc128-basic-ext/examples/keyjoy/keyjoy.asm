; =====================================================================
; KEYJOY - read the keyboard like a joystick, for PC128 BASIC 128
;
; PC128 version of the idea in "L'interpreteur BASIC TO7-70/TO9", part 4:
; a USR function that scans the keyboard matrix directly, so a game can
; use keys without INKEY$ repeat delays or beeps, with diagonals.
;
; Position independent: assembled at $9F00 but it runs wherever it is loaded.
; Everything is addressed relative to the start address BASE:
;   BASE+0  entry point (BRA to the code)       DEFUSR0=BASE : K=USR0(0)
;   BASE+2  signature "KJ"
;   BASE+4  direction, STICK code 0-8            (arrow keys)
;   BASE+5  fire, 0 or 1                         (Space)
;   BASE+6  code
;
;   CLEAR ,&H9EFF : LOADM "KEYJOY" : B=&H9F00 : DEFUSR0=B
;   K=USR0(0)          argument ignored
;   D=K AND 15         direction like STICK: 0 none, 1 up, 2 up-right,
;                      3 right, 4 down-right, 5 down, 6 down-left,
;                      7 left, 8 up-left
;   F=(K AND 128)<>0   fire (SPACE held)
; or, without arithmetic, D=PEEK(B+4) and F=PEEK(B+5) after the call.
; To load elsewhere give LOADM an offset from $9F00, e.g. $5000 (CLEAR ,&H4FFF):
;   LOADM "KEYJOY",&HB100 : B=&H5000 : DEFUSR0=B
;
; USR convention (PC128 manual pp.346-347): return an integer at 2,X
; with A = 2; keep X, S and DP.
; Keyboard (MAME thomson.cpp, mo6_sys_portb_in): write (col<<4)|(line<<1)
; to the system PIA port B; bit 7 then reads 0 if that key is down.
; =====================================================================

PIAB        equ $A7C1           ; hardware, the only absolute address

K_SPACE     equ $40             ; line 0, column 4
K_RIGHT     equ $32             ; line 1, columns 3-6
K_DOWN      equ $42
K_LEFT      equ $52
K_UP        equ $62

            org $9F00

KEYJOY      bra  main           ; BASE+0
            fcc  "KJ"           ; BASE+2
DIR         fcb  0              ; BASE+4
FIRE        fcb  0              ; BASE+5

main        pshs cc
            orcc #$50           ; the monitor scans the keyboard on IRQ
            ldb  PIAB
            pshs b

            leay KEYS+5,pcr     ; mask bit0=U bit1=R bit2=D bit3=L
            clrb
nextkey     lda  ,-y
            beq  scandone       ; a 0 byte precedes the first key
            sta  PIAB
            lda  PIAB
            coma
            rola                ; C = key down
            rolb
            bra  nextkey
scandone    leay DIRTAB,pcr
            ldb  b,y
            stb  DIR,pcr

            lda  #K_SPACE
            sta  PIAB
            lda  PIAB
            coma
            rola                ; C = key down
            lda  #0             ; CLRA would clear C
            rola
            sta  FIRE,pcr
            beq  done
            orb  #$80

done        clra
            std  2,x
            puls a
            sta  PIAB
            lda  #2
            puls cc,pc

KEYS        fcb  0,K_UP,K_RIGHT,K_DOWN,K_LEFT
; STICK value for each U/R/D/L mask; impossible or 3+ key combinations give 0
DIRTAB      fcb  0,1,3,2,5,0,4,0,7,8,0,0,6,0,0,0

            end  KEYJOY
