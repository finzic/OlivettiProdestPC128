* ol_swi.asm - generic monitor call
        INCLUDE "olivetti.inc"

        SECTION code
        EXPORT  _ol_swi

* ol_byte ol_swi(ol_byte service, ol_regs *r)
*   r: a(0) b(1) x(2) y(4) u(6) cc(8). Returns CC after the call.
_ol_swi
        LDB     3,S
        STB     ol_swi_code,PCR         self-modifying: the byte after SWI is the service
        PSHS    U,Y                     service 6,S  r 8,S
        LDU     8,S
        LDA     ,U
        LDB     1,U
        LDX     2,U
        LDY     4,U
        LDU     6,U
        SWI
ol_swi_code
        FCB     0
        PSHS    U,CC                    CC 0,S  U 1,S  r 11,S
        LDU     11,S
        STA     ,U
        STB     1,U
        STX     2,U
        STY     4,U
        LDD     1,S
        STD     6,U
        LDB     ,S
        STB     8,U
        CLRA
        LEAS    3,S
        PULS    Y,U,PC
        ENDSECTION
