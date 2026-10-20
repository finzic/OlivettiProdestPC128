* ol_crt.asm - always linked by pc128cc (before main):
*   - makes printf()/putchar() print '\n' as CR LF on the PC128 screen
*   - ol_break(): empty routine to put a debugger breakpoint on
        INCLUDE "olivetti.inc"

CHROUT  IMPORT

        SECTION constructors
        LEAX    ol_chrout,PCR           runs inside INILIB, before main()
        STX     CHROUT
        ENDSECTION

        SECTION code
        EXPORT  _ol_break
        EXPORT  ol_chrout

* CHROUT hook: character in A, all registers preserved.
ol_chrout
        PSHS    B
        TFR     A,B
        CMPB    #10
        BNE     @put
        LDB     #13
        SYSCALL PUTC
        LDB     #10
@put    SYSCALL PUTC
        PULS    B,PC

* void ol_break(void)
_ol_break
        NOP
        RTS
        ENDSECTION
