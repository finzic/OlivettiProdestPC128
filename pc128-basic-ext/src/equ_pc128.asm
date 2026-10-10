; =====================================================================
; equ_pc128.asm -- addresses for Olivetti Prodest PC128 / Thomson MO6
;
; Status tags:
;   [DOC]   verified in the scanned manuals (reference given)
;   [SCAN]  MUST be filled from tools/rom_scan.py + disassembly of YOUR
;           PC128 BASIC 128 ROM. The value shown is only a placeholder;
;           the TO7-70/TO9 value from "02-interpreteur-basic-to9" is given
;           for comparison. Do not run the extension until all [SCAN]
;           values are confirmed.
; =====================================================================

; ---------------------------------------------------------------------
; Monitor: called with   SWI / FCB code   (01-assembleurMo6 p.194)
; ---------------------------------------------------------------------
M_PUTC      equ $02         ; [DOC] B = char to output (p.208-209)
M_GETC      equ $0A         ; [DOC] returns char in B
M_KTST      equ $0C         ; [DOC] keyboard test, C=1 if key pressed

; ---------------------------------------------------------------------
; System page / BASIC 128 page
; ---------------------------------------------------------------------
SAVTOUR     equ $2086       ; [DOC] saved border colour (p.209)
ZPERR       equ $2185       ; [DOC] BASIC 128 error trap vector (p.288)
SAVSTK      equ $2175       ; [DOC] BASIC 128 saved stack (p.288)
EXTRAMON    equ $EFFB       ; [DOC] ROM bank toggle BASIC<->EXTRAMON (p.288)

; ---------------------------------------------------------------------
; BASIC 128 interpreter internals                               [SCAN]
; ---------------------------------------------------------------------
; Text pointer (address of current char in the tokenised line).
;   TO7-70: $61B9 (DP=$61, "$B9").  On MO6 BASIC 128 the BASIC page is
;   $2100-$21FF (ZPERR/SAVSTK above live there), so expect $21xx.
B_TXTPTR    equ $21B9       ; [SCAN] placeholder

; Get next char: advance TXTPTR, A=char, Z=1 on ':' or end of line,
; C=1 if digit.  TO7-70: JSR <$B2 (RAM copy at $61B2).
B_CHRGET    equ $21B2       ; [SCAN] placeholder
; Re-read current char without advancing (MS-BASIC "CHRGOT").
B_CHRGOT    equ $21B8       ; [SCAN] placeholder

; Evaluate numeric expression into FAC.          TO7-70: $081A
B_GETEXPR   equ $0000       ; [SCAN]
; Convert FAC to unsigned 16-bit integer in D (FC error if out of range).
B_FAC2U16   equ $0000       ; [SCAN]
; Raise "Syntax error".                           TO7-70: $07F3
B_SNERR     equ $0000       ; [SCAN]
; Raise "Illegal function call".
B_FCERR     equ $0000       ; [SCAN]
; Interpreter main loop entry "execute next statement". TO7-70: $2AED
B_NEWSTT    equ $0000       ; [SCAN]

; ---------------------------------------------------------------------
; Extension hooks (the technique of 02-interpreteur-basic-to9, part 3)
; ---------------------------------------------------------------------
; RAM word holding the address of the keyword table used by the
; tokenizer for $FF-prefixed tokens.             TO7-70: $6287
KWPTR       equ $0000       ; [SCAN]
; Token value (2nd byte after $FF) of the first word in that table.
KW_FIRST    equ $80         ; [SCAN] TO7-70 functions start at $FF,$80
; 3-byte RAM hook called when a statement starts with an $FF token the
; interpreter does not handle (default RTS / JMP SNERR). TO7-70: $6273
HOOK        equ $0000       ; [SCAN]
; Bytes on the stack between the hook's caller and DISPATCH
; (the return address of the JSR HOOK).
HOOK_STACK  equ 2           ; [SCAN] verify at the hook call site

; ---------------------------------------------------------------------
; Where the extension lives. Reserve it from BASIC with CLEAR first.
; ---------------------------------------------------------------------
EXT_ORG     equ $9000       ; [SCAN] confirm this RAM is not banked out
KWBUF_SIZE  equ 768         ; RAM copy of keyword table + new words
