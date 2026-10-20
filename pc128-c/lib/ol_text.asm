* ol_text.asm - PUTC based text output
        INCLUDE "olivetti.inc"

        SECTION code
        EXPORT  _ol_putc
        EXPORT  _ol_puts
        EXPORT  _ol_esc
        EXPORT  _ol_cls
        EXPORT  _ol_locate

* void ol_putc(char c)
_ol_putc
        LDB     3,S
        SYSCALL PUTC
        RTS

* void ol_puts(const char *s)      '\n' -> CR LF
_ol_puts
        LDX     2,S
@loop   LDB     ,X+
        BEQ     @done
        CMPB    #10
        BNE     @put
        LDB     #13
        SYSCALL PUTC
        LDB     #10
@put    SYSCALL PUTC
        BRA     @loop
@done   RTS

* void ol_esc(ol_byte attr)
_ol_esc
        LDB     #$1B
        SYSCALL PUTC
        LDB     3,S
        SYSCALL PUTC
        RTS

* void ol_cls(void)
_ol_cls
        LDB     #$0C
        SYSCALL PUTC
        RTS

* void ol_locate(ol_byte col, ol_byte row)     col 0-based, row 0..24
_ol_locate
        LDB     #$1F
        SYSCALL PUTC
        LDB     5,S
        ADDB    #$40
        SYSCALL PUTC
        LDB     3,S
        ADDB    #$41                    the monitor counts columns from 1
        SYSCALL PUTC
        RTS
        ENDSECTION
