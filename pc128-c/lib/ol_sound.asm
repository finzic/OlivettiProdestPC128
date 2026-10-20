* ol_sound.asm - BIIP and NOTE
        INCLUDE "olivetti.inc"

        SECTION code
        EXPORT  _ol_beep
        EXPORT  _ol_note

* void ol_beep(void)
_ol_beep
        SYSCALL BIIP
        RTS

* void ol_note(ol_byte note)
_ol_note
        LDB     3,S
        SYSCALL NOTE
        RTS
        ENDSECTION
