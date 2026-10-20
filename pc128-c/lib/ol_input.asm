* ol_input.asm - joysticks, light pen, mouse, beep, note
        INCLUDE "olivetti.inc"

        SECTION code
        EXPORT  _ol_joystick
        EXPORT  _ol_lightpen_button
        EXPORT  _ol_lightpen
        EXPORT  _ol_mouse_buttons
        EXPORT  _ol_mouse

* ol_byte ol_joystick(ol_byte n, ol_byte *fire)
_ol_joystick
        LDA     3,S
        SYSCALL JOYS
        PSHS    B                       n 4,S  fire 5,S
        TFR     CC,A
        ANDA    #1
        LDX     5,S
        BEQ     @ret
        STA     ,X
@ret    PULS    B
        CLRA
        RTS

* ol_byte ol_lightpen_button(void)
_ol_lightpen_button
        SYSCALL LPIN
        TFR     CC,B
        ANDB    #1
        CLRA
        RTS

* ol_byte ol_lightpen(int *x, int *y)      0 = ok, 1 = bad reading
_ol_lightpen
        PSHS    U,Y                     px 6,S  py 8,S
        SYSCALL GETL
xy_out  TFR     CC,A
        ANDA    #1
        PSHS    A                       px 7,S  py 9,S
        LDU     7,S
        BEQ     @s1
        STX     ,U
@s1      LDU     9,S
        BEQ     @s2
        STY     ,U
@s2      PULS    B
        CLRA
        PULS    Y,U,PC

* ol_byte ol_mouse_buttons(void)           bit 0 left, bit 1 right
_ol_mouse_buttons
        SYSCALL MOUSEB
        TFR     CC,A
        CLRB
        BITA    #1
        BEQ     @s1
        ORB     #1
@s1      BITA    #4
        BEQ     @s2
        ORB     #2
@s2      CLRA
        RTS

* ol_byte ol_mouse(int *x, int *y)         0 = ok, 1 = bad reading
_ol_mouse
        PSHS    U,Y
        SYSCALL MOUSE
        BRA     xy_out
        ENDSECTION
