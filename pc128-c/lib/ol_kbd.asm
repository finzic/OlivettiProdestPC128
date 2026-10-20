* ol_kbd.asm - keyboard
        INCLUDE "olivetti.inc"

        SECTION code
        EXPORT  _ol_getc
        EXPORT  _ol_ktst
        EXPORT  _ol_waitkey

* ol_byte ol_getc(void)            key code or 0
_ol_getc
        SYSCALL GETC
        CLRA
        RTS

* ol_byte ol_ktst(ol_byte *mods)   key code or 0 (fast keyboard test)
_ol_ktst
        SYSCALL KTST
        BEQ     @none
        LDX     2,S
        BEQ     @ret
        STA     ,X
@ret    CLRA
        RTS
@none   CLRA
        CLRB
        RTS

* ol_byte ol_waitkey(void)
_ol_waitkey
@loop   SYSCALL GETC
        TSTB
        BEQ     @loop
        CLRA
        RTS
        ENDSECTION
