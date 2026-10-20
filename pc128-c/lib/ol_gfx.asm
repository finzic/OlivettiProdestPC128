* ol_gfx.asm - monitor graphics primitives
        INCLUDE "olivetti.inc"

        SECTION code
        EXPORT  _ol_plot
        EXPORT  _ol_lineto
        EXPORT  _ol_moveto
        EXPORT  _ol_line
        EXPORT  _ol_point
        EXPORT  _ol_screen_char
        EXPORT  _ol_frm0
        EXPORT  _ol_frm1
        EXPORT  _ol_palette
        EXPORT  _ol_load_palette

* void ol_plot(int x, int y, signed char color)
_ol_plot
        PSHS    Y                       x 4,S  y 6,S  color 9,S
        LDB     9,S
        STB     FORME
        CLR     CHDRAW
        LDX     4,S
        BMI     @sk
        LDY     6,S
        BMI     @sk
        SYSCALL PLOT
@sk     PULS    Y,PC

* void ol_lineto(int x, int y, signed char color)
_ol_lineto
        PSHS    Y
        LDB     9,S
        STB     FORME
        CLR     CHDRAW
        LDX     4,S
        LDY     6,S
        BSR     clampxy
        SYSCALL DRAW
        PULS    Y,PC

* Negative coordinates make the ROM DRAW loop forever: clamp X and Y to >= 0.
clampxy
        CMPX    #0
        BGE     @cy
        LDX     #0
@cy     CMPY    #0
        BGE     @ok
        LDY     #0
@ok     RTS

* void ol_moveto(int x, int y)
_ol_moveto
        LDD     2,S
        BPL     @x
        CLRA
        CLRB
@x      STD     PLOTX
        LDD     4,S
        BPL     @y
        CLRA
        CLRB
@y      STD     PLOTY
        RTS

* void ol_line(int x1, int y1, int x2, int y2, signed char color)
_ol_line
        PSHS    Y                       x1 4,S  y1 6,S  x2 8,S  y2 10,S  color 13,S
        LDX     4,S
        LDY     6,S
        BSR     clampxy
        STX     PLOTX
        STY     PLOTY
        LDB     13,S
        STB     FORME
        CLR     CHDRAW
        LDX     8,S
        LDY     10,S
        BSR     clampxy
        SYSCALL DRAW
        PULS    Y,PC

* signed char ol_point(int x, int y)
_ol_point
        PSHS    Y
        LDB     #-1
        LDX     4,S
        BMI     @off
        LDY     6,S
        BMI     @off
        SYSCALL GETP
@off    SEX
        PULS    Y,PC

* ol_byte ol_screen_char(ol_byte col, ol_byte row)
_ol_screen_char
        CLRA
        LDB     3,S
        TFR     D,X
        LDA     5,S
        SYSCALL GETS
        CLRA
        RTS

* void ol_frm0(void) / void ol_frm1(void)
_ol_frm0
        SYSCALL FRM0
        RTS
_ol_frm1
        SYSCALL FRM1
        RTS

* ol_word ol_palette(ol_byte index, ol_word andmask, ol_word ormask)
_ol_palette
        PSHS    Y                       index 5,S  and 6,S  or 8,S
        LDA     5,S
        LDX     6,S
        LDY     8,S
        SYSCALL SETP
        TFR     X,D
        PULS    Y,PC

* void ol_load_palette(const ol_word *table16)
_ol_load_palette
        PSHS    Y
        LDA     #$FF
        LDX     4,S
        SYSCALL SETP
        PULS    Y,PC
        ENDSECTION
