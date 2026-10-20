; XOR mouse pointer for the 320x200 two-colour (40-column) screen.
;
; Draws a 16-pixel-wide sprite by EORing its mask into the form plane.
; Only the form plane is touched, so calling it twice at the same
; coordinates restores the screen exactly. To move the pointer, erase
; at the old position, then draw at the new one.
;
; Parameters (fixed addresses, so BASIC can POKE them):
;   AR_X   ($5002, 2 bytes) x of the hotspot, 0..319
;   AR_Y   ($5004, 1 byte)  y of the hotspot, 0..199
;   AR_SHP ($5005, 2 bytes) shape address, 0 = built-in arrow
; Shape format: height byte, then 2 bytes per row (bit 7 = leftmost pixel).
; Parts falling off the right or bottom edge are clipped.
;
; From BASIC:
;   CLEAR ,&H4FFF:LOADM "ARROW"
;   POKE &H5002,X\256:POKE &H5003,X AND 255:POKE &H5004,Y:EXEC &H5000

PIA         equ $A7C0
ROWBYTES    equ 40
SCRH        equ 200

            org $5000

ARROW       bra  ARROW_XOR
AR_X        fdb  0
AR_Y        fcb  0
AR_SHP      fdb  0

ARROW_XOR   pshs cc,a,b,x,u
            orcc #$50               ; keep the IRQ from flipping the plane
            lda  PIA
            sta  PIASAV
            ora  #1                 ; select the form plane at $0000
            sta  PIA

            ldu  AR_SHP
            bne  AR_HAVESH
            ldu  #DEFARROW
AR_HAVESH   ldd  AR_X
            cmpd #320
            bhs  AR_DONE
            andb #7
            stb  AR_SHIFT
            ldd  AR_X
            lsra
            rorb
            lsra
            rorb
            lsra
            rorb
            stb  AR_COL             ; byte column 0..39
            lda  AR_Y
            cmpa #SCRH
            bhs  AR_DONE
            sta  AR_CURY
            ldb  #ROWBYTES
            mul
            addb AR_COL
            adca #0
            tfr  d,x                ; X = first screen byte
            lda  ,u+
            beq  AR_DONE
            sta  AR_ROWS

AR_ROW      lda  AR_CURY
            cmpa #SCRH
            bhs  AR_DONE
            ldd  ,u++
            sta  AR_M0
            stb  AR_M1
            clr  AR_M2
            lda  AR_SHIFT
            beq  AR_PUT
AR_SHL      lsr  AR_M0
            ror  AR_M1
            ror  AR_M2
            deca
            bne  AR_SHL
AR_PUT      lda  ,x
            eora AR_M0
            sta  ,x
            ldb  AR_COL
            cmpb #ROWBYTES-1
            bhs  AR_NEXT
            lda  1,x
            eora AR_M1
            sta  1,x
            cmpb #ROWBYTES-2
            bhs  AR_NEXT
            lda  2,x
            eora AR_M2
            sta  2,x
AR_NEXT     leax ROWBYTES,x
            inc  AR_CURY
            dec  AR_ROWS
            bne  AR_ROW

AR_DONE     lda  PIASAV
            sta  PIA
            puls cc,a,b,x,u,pc

PIASAV      rmb  1
AR_SHIFT    rmb  1
AR_COL      rmb  1
AR_CURY     rmb  1
AR_ROWS     rmb  1
AR_M0       rmb  1
AR_M1       rmb  1
AR_M2       rmb  1

; Filled arrow, hotspot at the top-left pixel.
DEFARROW    fcb  15
            fdb  %1000000000000000
            fdb  %1100000000000000
            fdb  %1110000000000000
            fdb  %1111000000000000
            fdb  %1111100000000000
            fdb  %1111110000000000
            fdb  %1111111000000000
            fdb  %1111111100000000
            fdb  %1111100000000000
            fdb  %1101100000000000
            fdb  %1001100000000000
            fdb  %0000110000000000
            fdb  %0000110000000000
            fdb  %0000011000000000
            fdb  %0000011000000000
