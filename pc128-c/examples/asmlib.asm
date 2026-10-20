* asmlib.asm - assembly routines linked with mixed.c
        INCLUDE "olivetti.inc"

        SECTION code
        EXPORT  _sum_bytes
        EXPORT  _put_stars
        EXPORT  _for_each_char
        IMPORT  _counter                C global variable (unsigned int counter)

* ol_word sum_bytes(const ol_byte *p, ol_word n)
_sum_bytes
        PSHS    Y                       p 4,S  n 6,S
        LDX     4,S
        LDY     6,S
        CLRA
        CLRB
        CMPY    #0
        BEQ     @done
@loop   ADDB    ,X+
        ADCA    #0
        LEAY    -1,Y
        BNE     @loop
@done   PULS    Y,PC

* void put_stars(ol_byte n) - prints n '*' through the monitor PUTC
_put_stars
        LDA     3,S
        BEQ     @end
@next   PSHS    A
        LDB     #'*'
        SYSCALL PUTC
        LDD     _counter                touch a C global from assembly
        ADDD    #1
        STD     _counter
        PULS    A
        DECA
        BNE     @next
@end    RTS

* void for_each_char(const char *s, void (*fn)(char)) - calls back into C
_for_each_char
        PSHS    U
        LDU     4,S                     s
@loop   LDB     ,U+
        BEQ     @end
        CLRA
        PSHS    D                       char argument (promoted to 16 bits)
        JSR     [8,S]                   fn: 6,S + 2 bytes pushed
        LEAS    2,S
        BRA     @loop
@end    PULS    U,PC
        ENDSECTION
