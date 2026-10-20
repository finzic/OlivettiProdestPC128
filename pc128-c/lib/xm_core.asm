* xm_core.asm - EXTRAMONITOR access from a program started with EXEC under BASIC 128.
*
* Under BASIC the "BASIC side" monitor page is mapped (PIA $A7C0 bit 5 = 1): its SWI2
* vector is a bare RTI. JSR $EFFB toggles to the extramonitor page, whose SWI2 handler
* dispatches LDB #fn / SWI2 calls. Toggling back runs BASIC-page code that maps BASIC's
* work bank at $6000-$9FFF, so the way back runs from a trampoline on the stack (fixed RAM)
* that re-selects our RAM page ($A7E5) before returning here.
        INCLUDE "olivetti.inc"

        SECTION code
        EXPORT  _xm_begin
        EXPORT  _xm_end
        EXPORT  _xm_active
        EXPORT  _xm_call

* void xm_begin(void)            (the ROM page switch clobbers U: save U and Y)
_xm_begin
        TST     xm_on,PCR
        BNE     @ret
        PSHS    U,Y
        LDA     RAMPAG
        STA     xm_page,PCR
        CLR     xm_toggled,PCR
        LDA     PIA.A
        BITA    #$20
        BEQ     @mapped                 extramonitor page already there
        JSR     EXTRAMON
        INC     xm_toggled,PCR
@mapped LDX     ZPERR
        STX     xm_oldtrap,PCR
        LEAX    xm_trap,PCR
        STX     ZPERR
        INC     xm_on,PCR
        PULS    U,Y
@ret    RTS

* void xm_end(void)
_xm_end
        TST     xm_on,PCR
        BEQ     @ret
        LDX     xm_oldtrap,PCR
        STX     ZPERR
        CLR     xm_on,PCR
        TST     xm_toggled,PCR
        BEQ     @ret
        PSHS    U,Y
        LEAS    -9,S                    JSR $EFFB / LDA #page / STA $A7E5 / RTS
        LDD     #$BDEF
        STD     ,S
        LDD     #$FB86
        STD     2,S
        LDA     xm_page,PCR
        STA     4,S
        LDD     #$B7A7
        STD     5,S
        LDD     #$E539
        STD     7,S
        JSR     ,S
        LEAS    9,S
        PULS    U,Y
@ret    RTS

* ol_byte xm_active(void)
_xm_active
        LDB     xm_on,PCR
        CLRA
        RTS

* ol_byte xm_call(ol_byte fn, ol_regs *r)      returns B (0 = ok, else error code)
_xm_call
        TST     xm_on,PCR
        BNE     @on
        LBSR    _xm_begin
@on     PSHS    U,Y                     fn 7,S  r 8,S
        LDU     8,S
        BEQ     @noin
        LDA     ,U
        LDX     2,U
        LDY     4,U
        LDU     6,U
@noin   LDB     7,S
        SWI2
        PSHS    U,CC                    r 11,S
        LDU     11,S
        BEQ     @noout
        STA     ,U
        STB     1,U
        STX     2,U
        STY     4,U
        LDX     1,S
        STX     6,U
        LDA     ,S
        STA     8,U
@noout  CLRA
        LEAS    3,S
        PULS    Y,U,PC

* Error trap (ZPERR): back to the caller of SWI2 with B = error code
* (routine from "L'Extramoniteur du MO6").
xm_trap
        LDS     SAVSTK
        LEAS    3,S
        STB     2,S
        RTI
        ENDSECTION

* exit() / return from main(): never go back to BASIC with the extramonitor mapped
        SECTION destructors
        LBSR    _xm_end
        ENDSECTION

        SECTION bss
xm_on       RMB 1
xm_toggled  RMB 1
xm_page     RMB 1
xm_oldtrap  RMB 2
        ENDSECTION
