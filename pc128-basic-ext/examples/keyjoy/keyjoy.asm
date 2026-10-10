; =====================================================================
; KEYJOY - read the keyboard like a joystick, for PC128 BASIC 128
;
; PC128 version of the idea in "L'interpreteur BASIC TO7-70/TO9", part 4:
; a USR function that scans the keyboard matrix directly, so a game can
; use keys without INKEY$ repeat delays or beeps, with diagonals.
;
;   CLEAR ,&H9EFF : LOADM "KEYJOY" : DEFUSR0=&H9F00
;   K=USR0(0)          argument ignored
;   D=K AND 15         direction like STICK: 0 none, 1 up, 2 up-right,
;                      3 right, 4 down-right, 5 down, 6 down-left,
;                      7 left, 8 up-left
;   F=(K AND 128)<>0   fire (SPACE held)
;
; USR convention (PC128 manual pp.346-347): return an integer at 2,X
; with A = 2; keep X, S and DP.
; Keyboard (MAME thomson.cpp, mo6_sys_portb_in): write (col<<4)|(line<<1)
; to the system PIA port B; bit 7 then reads 0 if that key is down.
; =====================================================================

PIAB        equ $A7C1

K_SPACE     equ $40             ; line 0, column 4
K_RIGHT     equ $32             ; line 1, columns 3-6
K_DOWN      equ $42
K_LEFT      equ $52
K_UP        equ $62

            org $9F00

KEYJOY      pshs cc
            orcc #$50           ; the monitor scans the keyboard on IRQ
            ldb  PIAB
            pshs b

            ldy  #KEYS+4        ; mask bit0=U bit1=R bit2=D bit3=L
            clrb
scan        lda  ,-y
            sta  PIAB
            lda  PIAB
            coma
            rola                ; C = key down
            rolb
            cmpy #KEYS
            bne  scan
            ldy  #DIRTAB
            ldb  b,y

            lda  #K_SPACE
            sta  PIAB
            lda  PIAB
            bmi  done
            orb  #$80

done        clra
            std  2,x
            puls a
            sta  PIAB
            lda  #2
            puls cc,pc

KEYS        fcb  K_UP,K_RIGHT,K_DOWN,K_LEFT
; STICK value for each U/R/D/L mask; impossible or 3+ key combinations give 0
DIRTAB      fcb  0,1,3,2,5,0,4,0,7,8,0,0,6,0,0,0

            end  KEYJOY
