; Experiment: use BASIC 128's empty keyword descriptor at $277A to add statements.
; Descriptor = count, keyword table, handler; tokens continue after the 121
; built-in statements, so HELLO=$F9, BYE=$FA. The dispatcher does JMP [$277D]
; with A = token and the text pointer still on the token.
; Result: HELLO writes $42 to $5F00, BYE writes $99 to $5F01.

CHRGET      equ $21C0
SNERR       equ $B8F4           ; previous contents of $277D

            org $5000
INSTALL     ldx #KEYWORDS
            stx $277B
            ldx #HANDLER
            stx $277D
            lda #NWORDS
            sta $277A
            rts

HANDLER     cmpa #$F9
            beq do_hello
            cmpa #$FA
            beq do_bye
            jmp SNERR
do_hello    ldb #$42
            stb $5F00
            jmp CHRGET          ; skip the token; CHRGET's RTS returns to the dispatcher's caller
do_bye      ldb #$99
            stb $5F01
            jmp CHRGET

KEYWORDS    fcs "HELLO"
            fcs "BYE"
NWORDS      equ 2

            end INSTALL
