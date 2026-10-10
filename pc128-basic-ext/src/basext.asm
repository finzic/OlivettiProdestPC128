; =====================================================================
; basext.asm -- new BASIC 128 commands for the Olivetti Prodest PC128
;
; Port of the method in "L'interpreteur BASIC TO7-70/TO9" (part 3):
;   1. copy the ROM keyword table to RAM and append the new words, so the
;      tokenizer encodes them as $FF,<token>;
;   2. point the interpreter's keyword-table pointer at the RAM copy;
;   3. patch the RAM hook reached for unknown $FF statements with a JMP
;      to DISPATCH, which runs our handler (or falls back to the old hook).
;
; Usage from BASIC:   CLEAR ,&H8FFF : LOADM "BASEXT" : EXEC &H9000
; New commands:       HELLO
;                     BORDER n            (n = 0..15)
;                     DOKE addr,value     (16-bit POKE)
;                     FILL addr,len,byte
; =====================================================================

            include "equ_pc128.asm"

            org     EXT_ORG

; ---------------------------------------------------------------------
; INSTALL -- EXEC entry point
; ---------------------------------------------------------------------
INSTALL     pshs    d,x,y,u
            lda     INSTALLED
            bne     inst_done           ; already active: do nothing
            ldx     KWPTR
            ldu     #KWBUF
            ldb     #KW_FIRST
cpy_word    lda     ,x+
            beq     cpy_end             ; $00 terminates the table
            sta     ,u+
            bpl     cpy_word            ; bit 7 set marks a word's last char
            incb
            bra     cpy_word
cpy_end     stb     NEWTOK              ; token of our first word
            ldx     #NEWWORDS
app_word    lda     ,x+
            sta     ,u+
            bne     app_word            ; also copies the final $00
            ldx     #KWBUF
            stx     KWPTR
            ldx     #HOOK               ; save old hook, install JMP DISPATCH
            ldd     ,x
            std     OLDHOOK
            lda     2,x
            sta     OLDHOOK+2
            lda     #$7E
            sta     ,x
            ldd     #DISPATCH
            std     1,x
            inc     INSTALLED
inst_done   puls    d,x,y,u,pc

; ---------------------------------------------------------------------
; DISPATCH -- reached through HOOK.
; Assumed entry state (verify at the hook call site in the ROM):
;   TXTPTR points to the 2nd token byte, A = that byte.
; ---------------------------------------------------------------------
DISPATCH    cmpa    NEWTOK
            blo     not_ours
            suba    NEWTOK
            cmpa    #NCMDS
            bhs     not_ours
            lsla
            ldx     #CMDTAB
            ldx     a,x
            pshs    x
            jsr     B_CHRGET            ; skip token: A = first argument char
            rts                         ; jump to handler
not_ours    jmp     OLDHOOK

; Handlers jump here when done: drop the hook's return address and
; resume the interpreter on the next statement.
CMD_DONE    leas    HOOK_STACK,s
            jmp     B_NEWSTT

CMDTAB      fdb     CMD_HELLO
            fdb     CMD_BORDER
            fdb     CMD_DOKE
            fdb     CMD_FILL
NCMDS       equ     (*-CMDTAB)/2

; Same order as CMDTAB; fcs sets bit 7 on the last character.
NEWWORDS    fcs     "HELLO"
            fcs     "BORDER"
            fcs     "DOKE"
            fcs     "FILL"
            fcb     0

; ---------------------------------------------------------------------
; Argument helpers
; ---------------------------------------------------------------------
GETWORD     jsr     B_GETEXPR           ; D = 16-bit value of an expression
            jmp     B_FAC2U16

GETBYTE     bsr     GETWORD             ; B = 0..255
            tsta
            lbne    B_FCERR
            rts

COMMA       jsr     B_CHRGOT            ; require ',' and skip it
            cmpa    #',
            lbne    B_SNERR
            jmp     B_CHRGET

PRINTSTR    ldb     ,x+                 ; print $00-terminated string at X
            beq     ps_end
            pshs    x                   ; monitor may return values in X
            swi
            fcb     M_PUTC
            puls    x
            bra     PRINTSTR
ps_end      rts

; ---------------------------------------------------------------------
; Commands
; ---------------------------------------------------------------------
CMD_HELLO   ldx     #MSG_HELLO
            bsr     PRINTSTR
            jmp     CMD_DONE

; BORDER n -- ESC $6n via PUTC sets the border colour (01-assembleurMo6 p.209)
CMD_BORDER  bsr     GETBYTE
            cmpb    #15
            lbhi    B_FCERR
            pshs    b
            ldb     #$1B
            swi
            fcb     M_PUTC
            puls    b
            orb     #$60
            swi
            fcb     M_PUTC
            jmp     CMD_DONE

CMD_DOKE    bsr     GETWORD
            pshs    d                   ; address
            bsr     COMMA
            bsr     GETWORD
            puls    x
            std     ,x
            jmp     CMD_DONE

CMD_FILL    bsr     GETWORD
            pshs    d                   ; address
            bsr     COMMA
            bsr     GETWORD
            pshs    d                   ; length
            bsr     COMMA
            bsr     GETBYTE
            puls    y                   ; Y = length
            puls    x                   ; X = address
            leay    ,y
            beq     fill_end
fill_loop   stb     ,x+
            leay    -1,y
            bne     fill_loop
fill_end    jmp     CMD_DONE

; ---------------------------------------------------------------------
; Data
; ---------------------------------------------------------------------
MSG_HELLO   fcc     "PC128 BASIC extension active"
            fcb     13,10,0
INSTALLED   fcb     0
NEWTOK      fcb     0
OLDHOOK     rmb     3
KWBUF       rmb     KWBUF_SIZE

            end     INSTALL
