; Minimal 6809 test for lwasm. Stores $42 at $9F00, then sets the done flag.
        ORG     $9000
start   LDA     #$42
        STA     $9F00
        LDA     #1
        STA     $9F01          ; done flag (run with --done-addr 9F01)
loop    BRA     loop
        END     start
