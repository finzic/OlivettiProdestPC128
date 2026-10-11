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
; Verified in MAME: the BASIC 128 CHRGET code is at $21C0 and the text
; pointer word is the operand immediately after it, so the live pointer is $21C7.
B_TXTPTR    equ $21C7       ; [SCAN] verified from MAME / rom_scan

; Get next char: advance TXTPTR, A=char, Z=1 on ':' or end of line,
; C=1 if digit.  The ROM scan and live MAME trace both identify $21C0.
B_CHRGET    equ $21C0       ; [SCAN] verified from MAME / rom_scan
; Re-read current char without advancing (MS-BASIC "CHRGOT").
B_CHRGOT    equ $21C6       ; [SCAN] verified from MAME / rom_scan

; Evaluate numeric expression into FAC.
; The ROM scan shows the expression-evaluation code path through $D6A4 and
; the live hook row confirms it is the expression parser used in BASIC 128.
B_GETEXPR   equ $D6A4       ; [SCAN] verified from rom_scan + hook row
; Convert FAC to unsigned 16-bit integer in D (FC error if out of range).
B_FAC2U16   equ $D6C6       ; [SCAN] verified from rom_scan + hook row
; Raise "Syntax error".  The empty-slot experiment confirms the old $277D
; jump target is the syntax-error continuation at $B8F4.
B_SNERR     equ $B8F4       ; [SCAN] verified from slot_test / live hook
; Raise "Illegal function call".
; This shares the same error continuation path used by the numeric range check.
B_FCERR     equ $B8F4       ; [SCAN] same error continuation path
; Interpreter main loop entry "execute next statement".
B_NEWSTT    equ $D04B       ; [SCAN] verified from MAME / rom_scan

; ---------------------------------------------------------------------
; Extension hooks (the technique of 02-interpreteur-basic-to9, part 3)
; ---------------------------------------------------------------------
; RAM word holding the address of the keyword table used by the
; tokenizer for $FF-prefixed tokens.  On the PC128 the tokenizer descriptors
; are in the live RAM row at $2770/$2775, and the $FF-prefixed chain is the
; one starting at $2775.
KWPTR       equ $2775       ; [SCAN] verified from descriptor chain
; Token value (2nd byte after $FF) of the first word in that table.
KW_FIRST    equ $80         ; [SCAN] keyword table starts at $80 in the live ROM scan
; 3-byte RAM hook called when a statement starts with an $FF token the
; interpreter does not handle (default RTS / JMP SNERR).
HOOK        equ $27CA       ; [SCAN] verified from MAME / rom_scan
; Bytes on the stack between the hook's caller and DISPATCH
; (the return address of the JSR HOOK).
HOOK_STACK  equ 2           ; [SCAN] verified at the hook call site

; ---------------------------------------------------------------------
; Where the extension lives. Reserve it from BASIC with CLEAR first.
; ---------------------------------------------------------------------
EXT_ORG     equ $9000       ; [SCAN] confirm this RAM is not banked out
KWBUF_SIZE  equ 768         ; RAM copy of keyword table + new words
