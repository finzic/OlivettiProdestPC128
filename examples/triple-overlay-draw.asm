; Triple Overlay direct-memory graphics routines.
;
; Set PLANE to 1..4, VALUE to 0 (clear) or nonzero (set), then call PSET.
; PLOT_X/PLOT_Y are 0..159 and 0..199.
; LINE uses X0/Y0 to X1/Y1 and draws both endpoints.
; BOX uses the same endpoints; FILL=0 draws an outline, nonzero fills it.
; BOX accepts corners in either order. Coordinates must be on-screen.
;
; BASIC USR API uses one integer array, P%(0..7):
;   0 plane, 1 value, 2 fill, 3 x0, 4 y0, 5 x1, 6 y1
;   for CIRCLE, x0/y0 are center and 7 is radius (0..55)
; Keep the code in fixed RAM because VARPTR can switch the bank at $9000:
;   CLEAR ,&H4FFF:LOADM "TRIDRAW",R
;   DEFUSR0=&H5000:DEFUSR1=&H5003:DEFUSR2=&H5006:DEFUSR3=&H5009
;   R=USR0(VARPTR(P%(0)))  ; PSET at x0,y0
;   R=USR1(VARPTR(P%(0)))  ; LINE from x0,y0 to x1,y1
;   R=USR2(VARPTR(P%(0)))  ; BOX, outline or fill
;   R=USR3(VARPTR(P%(0)))  ; outline CIRCLE centered at x0,y0
; Each USR returns integer zero. Coordinates are 0..159 and 0..199.

PIA         equ $A7C0
VIDEO_MODE  equ $A7DC
SCRMOD      equ $2077
SCRPLANE    equ $2079
SCREEN_SIZE equ $1F40

            org $5000

PSET_ENTRY  lbra PSET_USR
LINE_ENTRY  lbra LINE_USR
BOX_ENTRY   lbra BOX_USR
CIRCLE_ENTRY lbra CIRCLE_USR

START       lda  #$3F
            sta  VIDEO_MODE
            lda  #$20
            sta  SCRMOD
            clr  SCRPLANE

            ; Clear both screen memories on physical page 0.
            lda  PIA
            sta  PIA_SAVE
            ora  #1
            sta  PIA
            ldx  #0
CLEAR_FORM  clr  ,x+
            cmpx #SCREEN_SIZE
            blo  CLEAR_FORM
            lda  PIA_SAVE
            anda #$FE
            sta  PIA
            ldx  #0
CLEAR_COLOR clr  ,x+
            cmpx #SCREEN_SIZE
            blo  CLEAR_COLOR
            lda  PIA_SAVE
            sta  PIA

            ; Plane 1: filled box at (20,20)-(80,80).
            lda  #1
            sta  PLANE
            sta  VALUE
            sta  FILL
            lda  #20
            sta  X0
            sta  Y0
            lda  #80
            sta  X1
            sta  Y1
            jsr  BOX

            ; Plane 2: filled box at (40,40)-(100,100).
            lda  #2
            sta  PLANE
            lda  #40
            sta  X0
            sta  Y0
            lda  #100
            sta  X1
            sta  Y1
            jsr  BOX

            ; Plane 3: filled box at (60,60)-(120,120).
            lda  #3
            sta  PLANE
            lda  #60
            sta  X0
            sta  Y0
            lda  #120
            sta  X1
            sta  Y1
            jsr  BOX

            ; Plane 1: turtle over the lower-priority filled boxes.
            lda  #1
            sta  PLANE
            sta  VALUE
            clr  FILL
            jsr  TURTLE

            ; Plane 4: diagonal line and isolated pixel.
            lda  #4
            sta  PLANE
            lda  #0
            sta  X0
            lda  #180
            sta  Y0
            lda  #159
            sta  X1
            lda  #130
            sta  Y1
            jsr  LINE
            lda  #150
            sta  PLOT_X
            sta  PLOT_Y
            jsr  PSET

            ; Plane 4: outline box at (5,5)-(30,35).
            lda  #5
            sta  X0
            sta  Y0
            lda  #30
            sta  X1
            lda  #35
            sta  Y1
            clr  FILL
            jsr  BOX

            ; Plane 4: outline circle centered at (105,45), radius 18.
            lda  #4
            sta  PLANE
            lda  #105
            sta  X0
            lda  #45
            sta  Y0
            lda  #18
            sta  CIRCLE_RADIUS
            jsr  CIRCLE

            ; Probe all three BASIC USR wrappers with a VARPTR-style frame.
            ldd  #USR_BOX_ARGS
            std  USR_FRAME+2
            ldx  #USR_FRAME
            jsr  BOX_USR
            ldd  #USR_LINE_ARGS
            std  USR_FRAME+2
            ldx  #USR_FRAME
            jsr  LINE_USR
            ldd  #USR_PSET_ARGS
            std  USR_FRAME+2
            ldx  #USR_FRAME
            jsr  PSET_USR
            ldd  #USR_CIRCLE_ARGS
            std  USR_FRAME+2
            ldx  #USR_FRAME
            jsr  CIRCLE_USR

            ; Probe one known packed byte from each of the four overlay planes.
            lda  PIA
            ora  #1
            sta  PIA
            lda  $0325
            sta  $9F10
            lda  $064A
            sta  $9F11
            lda  PIA
            anda #$FE
            sta  PIA
            lda  $096F
            sta  $9F12
            lda  $1795
            sta  $9F13

            lda  #1
            sta  $9F01
DEMO_HOLD  bra  DEMO_HOLD

; USR receives VARPTR(P%(0)) as a 16-bit integer at 2,X.
PSET_USR    pshs cc,d,y,u
            ldd  2,x
            std  PARAM_PTR
            ldu  PARAM_PTR
            ldb  1,u
            stb  PLANE
            ldb  3,u
            lbra USR_RETURN
            ldb  7,u
            stb  PLOT_X
            ldb  9,u
            stb  PLOT_Y
            jsr  PSET
            lbra USR_RETURN

LINE_USR    pshs cc,d,y,u
            ldd  2,x
            std  PARAM_PTR
            ldu  PARAM_PTR
            ldb  1,u
            stb  PLANE
            ldb  3,u
            stb  VALUE
            ldb  7,u
            stb  X0
            ldb  9,u
            stb  Y0
            ldb  11,u
            stb  X1
            ldb  13,u
            stb  Y1
            jsr  LINE
            lbra USR_RETURN

BOX_USR     pshs cc,d,y,u
            ldd  2,x
            std  PARAM_PTR
            ldu  PARAM_PTR
            ldb  1,u
            stb  PLANE
            ldb  3,u
            stb  VALUE
            ldb  5,u
            stb  FILL
            ldb  7,u
            stb  X0
            ldb  9,u
            stb  Y0
            ldb  11,u
            stb  X1
            ldb  13,u
            stb  Y1
            jsr  BOX
            lbra USR_RETURN

CIRCLE_USR  pshs cc,d,y,u
            ldd  2,x
            std  PARAM_PTR
            ldu  PARAM_PTR
            ldb  1,u
            stb  PLANE
            ldb  3,u
            stb  VALUE
            ldb  7,u
            stb  CIRCLE_CX
            ldb  9,u
            stb  CIRCLE_CY
            ldb  15,u
            stb  CIRCLE_RADIUS
            jsr  CIRCLE

USR_RETURN  clra
            clrb
            std  2,x
            puls cc,d,y,u
            lda  #2
            rts

; Draw a small right-facing turtle using the direct-memory primitives.
TURTLE      lda  #86
            sta  X0
            lda  #43
            sta  Y0
            lda  #110
            sta  X1
            lda  #63
            sta  Y1
            jsr  BOX

            lda  #98
            sta  X0
            lda  #45
            sta  Y0
            sta  X1
            lda  #61
            sta  Y1
            jsr  LINE
            lda  #89
            sta  X0
            lda  #53
            sta  Y0
            lda  #107
            sta  X1
            sta  Y1
            jsr  LINE

            lda  #1
            sta  FILL
            lda  #111
            sta  X0
            lda  #49
            sta  Y0
            lda  #123
            sta  X1
            lda  #57
            sta  Y1
            jsr  BOX

            clr  VALUE
            lda  #119
            sta  PLOT_X
            lda  #52
            sta  PLOT_Y
            jsr  PSET
            lda  #1
            sta  VALUE

            lda  #88
            sta  X0
            lda  #38
            sta  Y0
            lda  #94
            sta  X1
            lda  #43
            sta  Y1
            jsr  BOX
            lda  #101
            sta  X0
            lda  #38
            sta  Y0
            lda  #107
            sta  X1
            lda  #43
            sta  Y1
            jsr  BOX
            lda  #88
            sta  X0
            lda  #63
            sta  Y0
            lda  #94
            sta  X1
            lda  #68
            sta  Y1
            jsr  BOX
            lda  #101
            sta  X0
            lda  #63
            sta  Y0
            lda  #107
            sta  X1
            lda  #68
            sta  Y1
            jsr  BOX

            clr  FILL
            lda  #86
            sta  X0
            lda  #51
            sta  Y0
            lda  #80
            sta  X1
            lda  #53
            sta  Y1
            jsr  LINE
            lda  #80
            sta  X0
            lda  #53
            sta  Y0
            lda  #86
            sta  X1
            lda  #56
            sta  Y1
            jsr  LINE
            rts

; PSET uses PLOT_X/PLOT_Y and updates one bit in the selected plane.
PSET        pshs d,x,y,u
            lda  PLANE
            cmpa #1
            lblo PSET_DONE
            cmpa #4
            lbhi PSET_DONE
            lda  PLOT_X
            cmpa #160
            lbhs PSET_DONE
            lda  PLOT_Y
            cmpa #200
            lbhs PSET_DONE

            lda  PIA
            sta  PIA_SAVE
            lda  PLANE
            cmpa #3
            blo  PSET_FORM
            lda  PIA_SAVE
            anda #$FE
            sta  PIA
            bra  PSET_ADDRESS
PSET_FORM   lda  PIA_SAVE
            ora  #1
            sta  PIA

PSET_ADDRESS
            clra
            ldb  PLOT_Y
            tfr  d,y
            lslb
            rola
            lslb
            rola
            lslb
            rola
            tfr  d,u
            lslb
            rola
            lslb
            rola
            leau d,u
            clra
            ldb  PLOT_X
            lsrb
            lsrb
            leau d,u
            tfr  u,x

            lda  PLANE
            bita #1
            beq  PSET_LOW_NIBBLE
            ldb  #$80
            bra  PSET_MASK
PSET_LOW_NIBBLE
            ldb  #$08
PSET_MASK   stb  MASK
            lda  PLOT_X
            anda #3
            sta  SHIFT_COUNT
PSET_SHIFT  tst  SHIFT_COUNT
            beq  PSET_WRITE
            ldb  MASK
            lsrb
            stb  MASK
            dec  SHIFT_COUNT
            bra  PSET_SHIFT

PSET_WRITE  lda  VALUE
            beq  PSET_CLEAR
            lda  ,x
            ora  MASK
            sta  ,x
            bra  PSET_RESTORE
PSET_CLEAR  lda  MASK
            coma
            anda ,x
            sta  ,x
PSET_RESTORE
            lda  PIA_SAVE
            sta  PIA
PSET_DONE   puls d,x,y,u
            rts

; Midpoint outline circle. Radius is limited to 55 so 8-bit sums cannot wrap.
CIRCLE      pshs a,b,x,y,u
            lda  PLANE
            cmpa #1
            lblo CIRCLE_DONE
            cmpa #4
            lbhi CIRCLE_DONE
            lda  CIRCLE_CX
            cmpa #160
            lbhs CIRCLE_DONE
            lda  CIRCLE_CY
            cmpa #200
            lbhs CIRCLE_DONE
            lda  CIRCLE_RADIUS
            cmpa #56
            lbhs CIRCLE_DONE
            sta  CIRC_X
            clr  CIRC_Y
            clra
            ldb  #1
            subb CIRCLE_RADIUS
            sbca #0
            std  CIRC_ERR

CIRCLE_LOOP lda  CIRC_X
            cmpa CIRC_Y
            lblo CIRCLE_DONE
            jsr  CIRCLE_POINTS
            inc  CIRC_Y
            ldd  CIRC_ERR
            bmi  CIRCLE_Y_ONLY
            dec  CIRC_X
            clra
            ldb  CIRC_Y
            subb CIRC_X
            sbca #0
            aslb
            rola
            addd #1
            addd CIRC_ERR
            std  CIRC_ERR
            bra  CIRCLE_LOOP

CIRCLE_Y_ONLY
            clra
            ldb  CIRC_Y
            aslb
            rola
            addd #1
            addd CIRC_ERR
            std  CIRC_ERR
            bra  CIRCLE_LOOP

CIRCLE_POINTS
            lda  CIRCLE_CX
            adda CIRC_X
            sta  PLOT_X
            lda  CIRCLE_CY
            adda CIRC_Y
            sta  PLOT_Y
            jsr  PSET

            lda  CIRCLE_CX
            adda CIRC_Y
            sta  PLOT_X
            lda  CIRCLE_CY
            adda CIRC_X
            sta  PLOT_Y
            jsr  PSET

            lda  CIRCLE_CX
            suba CIRC_Y
            sta  PLOT_X
            lda  CIRCLE_CY
            adda CIRC_X
            sta  PLOT_Y
            jsr  PSET

            lda  CIRCLE_CX
            suba CIRC_X
            sta  PLOT_X
            lda  CIRCLE_CY
            adda CIRC_Y
            sta  PLOT_Y
            jsr  PSET

            lda  CIRCLE_CX
            suba CIRC_X
            sta  PLOT_X
            lda  CIRCLE_CY
            suba CIRC_Y
            sta  PLOT_Y
            jsr  PSET

            lda  CIRCLE_CX
            suba CIRC_Y
            sta  PLOT_X
            lda  CIRCLE_CY
            suba CIRC_X
            sta  PLOT_Y
            jsr  PSET

            lda  CIRCLE_CX
            adda CIRC_Y
            sta  PLOT_X
            lda  CIRCLE_CY
            suba CIRC_X
            sta  PLOT_Y
            jsr  PSET

            lda  CIRCLE_CX
            adda CIRC_X
            sta  PLOT_X
            lda  CIRCLE_CY
            suba CIRC_Y
            sta  PLOT_Y
            jsr  PSET
            rts

CIRCLE_DONE puls a,b,x,y,u
            rts

; Inclusive Bresenham line from X0/Y0 to X1/Y1.
LINE        pshs a,b,x,y,u
            lda  X1
            suba X0
            bcc  LINE_DX_READY
            nega
LINE_DX_READY
            tfr  a,b
            clra
            std  DX
            lda  Y1
            suba Y0
            bcc  LINE_DY_READY
            nega
LINE_DY_READY
            tfr  a,b
            clra
            std  DY

            lda  X0
            cmpa X1
            bls  LINE_STEP_X_POS
            lda  #$FF
            bra  LINE_STEP_X_SET
LINE_STEP_X_POS
            lda  #1
LINE_STEP_X_SET
            sta  STEP_X
            lda  Y0
            cmpa Y1
            bls  LINE_STEP_Y_POS
            lda  #$FF
            bra  LINE_STEP_Y_SET
LINE_STEP_Y_POS
            lda  #1
LINE_STEP_Y_SET
            sta  STEP_Y
            lda  X0
            sta  CUR_X
            lda  Y0
            sta  CUR_Y
            ldd  DX
            subd DY
            std  ERR
            ldd  DY
            coma
            comb
            addd #1
            std  NEG_DY

LINE_LOOP   lda  CUR_X
            sta  PLOT_X
            lda  CUR_Y
            sta  PLOT_Y
            jsr  PSET
            lda  CUR_X
            cmpa X1
            bne  LINE_STEP
            lda  CUR_Y
            cmpa Y1
            beq  LINE_DONE
LINE_STEP   ldd  ERR
            aslb
            rola
            std  ERR2
            ldd  ERR2
            cmpd NEG_DY
            ble  LINE_SKIP_X
            ldd  ERR
            subd DY
            std  ERR
            lda  CUR_X
            adda STEP_X
            sta  CUR_X
LINE_SKIP_X ldd  ERR2
            cmpd DX
            bge  LINE_SKIP_Y
            ldd  ERR
            addd DX
            std  ERR
            lda  CUR_Y
            adda STEP_Y
            sta  CUR_Y
LINE_SKIP_Y bra  LINE_LOOP
LINE_DONE   puls a,b,x,y,u
            rts

; BOX normalizes corners, then draws an outline or filled horizontal spans.
BOX         pshs a,b,x,y,u
            lda  X0
            cmpa X1
            bls  BOX_X_ORDERED
            lda  X0
            ldb  X1
            sta  X1
            stb  X0
BOX_X_ORDERED
            lda  Y0
            cmpa Y1
            bls  BOX_Y_ORDERED
            lda  Y0
            ldb  Y1
            sta  Y1
            stb  Y0
BOX_Y_ORDERED
            lda  X0
            sta  BOX_X0
            lda  Y0
            sta  BOX_Y0
            lda  X1
            sta  BOX_X1
            lda  Y1
            sta  BOX_Y1
            tst  FILL
            bne  BOX_FILLED

            lda  BOX_X0
            sta  X0
            lda  BOX_Y0
            sta  Y0
            lda  BOX_X1
            sta  X1
            lda  BOX_Y0
            sta  Y1
            jsr  LINE
            lda  BOX_X1
            sta  X0
            lda  BOX_Y0
            sta  Y0
            lda  BOX_Y1
            sta  Y1
            jsr  LINE
            lda  BOX_X1
            sta  X0
            lda  BOX_Y1
            sta  Y0
            lda  BOX_X0
            sta  X1
            lda  BOX_Y1
            sta  Y1
            jsr  LINE
            lda  BOX_X0
            sta  X0
            lda  BOX_Y1
            sta  Y0
            lda  BOX_Y0
            sta  Y1
            jsr  LINE
            bra  BOX_DONE

BOX_FILLED  lda  BOX_Y0
            sta  ROW
BOX_FILL_ROW
            lda  BOX_X0
            sta  X0
            lda  ROW
            sta  Y0
            lda  BOX_X1
            sta  X1
            lda  ROW
            sta  Y1
            jsr  LINE
            lda  ROW
            cmpa BOX_Y1
            beq  BOX_DONE
            inc  ROW
            bra  BOX_FILL_ROW
BOX_DONE    puls a,b,x,y,u
            rts

; Shared parameters and private scratch.
PLANE       fcb  1
VALUE       fcb  1
PLOT_X      fcb  0
PLOT_Y      fcb  0
X0          fcb  0
Y0          fcb  0
X1          fcb  0
Y1          fcb  0
FILL        fcb  0
PIA_SAVE    fcb  0
PARAM_PTR   rmb  2
MASK        fcb  0
SHIFT_COUNT fcb  0
DX          rmb  2
DY          rmb  2
NEG_DY      rmb  2
ERR         rmb  2
ERR2        rmb  2
STEP_X      fcb  0
STEP_Y      fcb  0
CUR_X       fcb  0
CUR_Y       fcb  0
BOX_X0      fcb  0
BOX_Y0      fcb  0
BOX_X1      fcb  0
CIRCLE_CX   fcb  0
CIRCLE_CY   fcb  0
CIRCLE_RADIUS fcb  0
CIRC_X      fcb  0
CIRC_Y      fcb  0
CIRC_ERR    rmb  2
BOX_Y1      fcb  0
ROW         fcb  0
USR_FRAME   rmb  4
USR_BOX_ARGS  fdb  4,1,0,5,5,30,35
USR_CIRCLE_ARGS fdb  4,1,0,105,45,0,0,18
USR_LINE_ARGS fdb  4,1,0,0,180,159,130
USR_PSET_ARGS fdb  4,1,0,150,150,0,0

            end  START