/*
 * olivetti.h - "standard Olivetti library" for the Olivetti Prodest PC128 (Thomson MO6, 6809).
 *
 * C wrappers (CMOC) for the ROM MONITOR services (SWI + service byte) and the
 * EXTRAMONITOR services (SWI2 with the function number in B).
 * Sources: docs/pc128-system-calls.md and the French "Le moniteur du MO6" /
 * "L'Extramoniteur du MO6" manuals (ocr_full.txt).
 *
 *   ol_*   ROM monitor: text, keyboard, graphics, joystick, light pen, mouse, sound,
 *          palette, printer, RS-232, disk sectors.
 *   xm_*   extramonitor: graphics with clipping window (line, box, ellipse, paint, MIG),
 *          real-number maths (4-byte reals), PLAY, error messages, raw calls (DOS, turtles).
 *
 * Programs are built with tools/pc128cc.py and started from BASIC 128 with EXEC.
 * main() returning (or exit()) goes back to BASIC.
 */
#ifndef OLIVETTI_H
#define OLIVETTI_H

typedef unsigned char  ol_byte;
typedef unsigned int   ol_word;

#ifndef NULL
#define NULL ((void *) 0)
#endif

/* ------------------------------------------------------------------ memory access */
#define OL_PEEK(a)      (*(ol_byte *) (a))
#define OL_PEEKW(a)     (*(ol_word *) (a))
#define OL_POKE(a, v)   (*(ol_byte *) (a) = (ol_byte) (v))
#define OL_POKEW(a, v)  (*(ol_word *) (a) = (ol_word) (v))

/* ------------------------------------------------------------------ debugging aids
 * The harness (pc128.py --done-addr 9F01, MCP run_c) stops when $9F01 becomes non-zero.
 * $9F00-$9FFF is outside the default link area (org $6000, limit $9F00): use it for results
 * you want to dump (pc128.py --dump 9F00:16). */
#define OL_DEBUG_AREA   0x9F00
#define OL_DONE_ADDR    0x9F01
#define ol_done()               OL_POKE(OL_DONE_ADDR, 1)
#define ol_debug_byte(i, v)     OL_POKE(OL_DEBUG_AREA + 0x10 + (i), (v))
#define ol_debug_word(i, v)     OL_POKEW(OL_DEBUG_AREA + 0x10 + (i), (v))

/* Empty function: set a breakpoint on it (`bp ol_break`) and call it where you want to stop. */
void ol_break(void);

/* ------------------------------------------------------------------ raw monitor call */
/* Register block for ol_swi()/xm_call(): inputs are loaded from it, outputs stored back. */
typedef struct ol_regs {
    ol_byte a, b;       /* offset 0, 1 (D = a:b) */
    ol_word x, y, u;    /* offset 2, 4, 6 */
    ol_byte cc;         /* offset 8: condition codes after the call */
} ol_regs;

#define OL_CC_C  0x01   /* carry: error / button pressed */
#define OL_CC_V  0x02
#define OL_CC_Z  0x04
#define OL_CC_N  0x08

/* SWI <service>: loads A,B,X,Y,U from *r, stores them back; returns CC. */
ol_byte ol_swi(ol_byte service, ol_regs *r);

/* Monitor service bytes (SWI followed by FCB service; add $80 for the JMP form). */
#define OL_SWI_PUTC     0x02
#define OL_SWI_FRM0     0x04
#define OL_SWI_FRM1     0x06
#define OL_SWI_BIIP     0x08
#define OL_SWI_GETC     0x0A
#define OL_SWI_KTST     0x0C
#define OL_SWI_DRAW     0x0E
#define OL_SWI_PLOT     0x10
#define OL_SWI_CHPL     0x12
#define OL_SWI_GETP     0x14
#define OL_SWI_LPIN     0x16
#define OL_SWI_GETL     0x18
#define OL_SWI_GETS     0x1A
#define OL_SWI_JOYS     0x1C
#define OL_SWI_NOTE     0x1E
#define OL_SWI_K7CO     0x20
#define OL_SWI_K7MO     0x22
#define OL_SWI_PRCO     0x24
#define OL_SWI_DKCO     0x26
#define OL_SWI_DKFO     0x2A
#define OL_SWI_SETP     0x3C
#define OL_SWI_MOUSEB   0x3E
#define OL_SWI_MOUSE    0x40
#define OL_SWI_RSCO     0x42

/* Monitor RAM registers */
#define OL_STATUS   0x2019
#define OL_FORME    0x2029      /* PLOT/DRAW colour, -16..15 (negative = background) */
#define OL_COLOUR   0x202B      /* current text colours */
#define OL_COPCHR   0x202F
#define OL_PLOTX    0x2032      /* last plotted point (word) */
#define OL_PLOTY    0x2034
#define OL_CHDRAW   0x2036      /* 0 = graphic PLOT/DRAW, else character code */
#define OL_TEMPO    0x2039      /* word, 1..255 */
#define OL_DUREE    0x203B      /* word, 96 = whole note */
#define OL_TIMBRE   0x203D      /* byte, 0..5 */
#define OL_OCTAVE   0x203E      /* word, 16/8/4/2/1 = octave 1..5 */
#define OL_PR_OPC   0x2042
#define OL_PR_STA   0x2043
#define OL_DK_OPC   0x2048
#define OL_DK_DRV   0x2049
#define OL_DK_TRK   0x204A      /* word */
#define OL_DK_SEC   0x204C
#define OL_DK_NUM   0x204D
#define OL_DK_STA   0x204E
#define OL_DK_BUF   0x204F      /* word */
#define OL_USERAF   0x2070
#define OL_CONFIG   0x2079      /* bit 6 mouse present, bit 7 mouse replaces light pen */
#define OL_RS_OPC   0x2082
#define OL_RS_STA   0x2083
#define OL_RS_MODE  0x2084
#define OL_RS_SPEED 0x2085
#define OL_SAVTOUR  0x2086

/* ------------------------------------------------------------------ colours */
enum {
    OL_BLACK, OL_RED, OL_GREEN, OL_YELLOW, OL_BLUE, OL_MAGENTA, OL_CYAN, OL_WHITE,
    OL_GREY, OL_PINK, OL_LIGHT_GREEN, OL_SAND, OL_LIGHT_BLUE, OL_PARMA, OL_SKY_BLUE, OL_ORANGE
};
/* PLOT/DRAW/xm_* colour that draws the background ("fond") of colour c */
#define OL_BACK(c)  (-1 - (c))

/* ------------------------------------------------------------------ text output (PUTC) */
void ol_putc(char c);               /* raw PUTC: control codes are interpreted */
void ol_puts(const char *s);        /* '\n' -> CR LF */
void ol_esc(ol_byte attr);          /* ESC attr */
void ol_cls(void);                  /* clear the current window */
void ol_locate(ol_byte col, ol_byte row);  /* col 0..39 (0..79), row 0..24 */
void ol_print_uint(ol_word n);
void ol_print_int(int n);
void ol_print_hex(ol_word n, ol_byte digits);

#define OL_BEL   0x07
#define OL_BS    0x08
#define OL_HT    0x09
#define OL_LF    0x0A
#define OL_VT    0x0B
#define OL_FF    0x0C
#define OL_CR    0x0D
#define OL_CURSOR_ON   0x11
#define OL_CURSOR_OFF  0x14
#define OL_ACC   0x16
#define OL_CAN   0x18           /* clear to end of line */
#define OL_ESC   0x1B
#define OL_RS    0x1E           /* cursor home */
#define OL_US    0x1F

#define ol_color(c)         ol_esc(0x40 | (c))   /* foreground (forme) */
#define ol_bgcolor(c)       ol_esc(0x50 | (c))   /* background (fond) */
#define ol_border(c)        ol_esc(0x60 | (c))   /* border (tour) */
#define ol_cursor(on)       ol_putc((on) ? OL_CURSOR_ON : OL_CURSOR_OFF)
#define ol_home()           ol_putc(OL_RS)

/* ESC attributes */
#define OL_ATTR_NORMAL      0x70
#define OL_ATTR_DBL_HEIGHT  0x71
#define OL_ATTR_DBL_WIDTH   0x72
#define OL_ATTR_DBL_SIZE    0x73
#define OL_ATTR_SCROLL      0x78
#define OL_ATTR_SOFT_SCROLL 0x79
#define OL_ATTR_PAGE        0x7A
#define OL_ATTR_INVERSE     0x7B
/* screen modes (ESC code) */
#define OL_MODE_40COL       0x7C    /* 320x200, 16 colours, 2 per 8 pixels ("MO5") */
#define OL_MODE_80COL       0x7D    /* 640x200, 2 colours */
#define OL_MODE_BITMAP4     0x7E    /* 320x200, 4 colours */
#define OL_MODE_BITMAP16    0x7F    /* 160x200, 16 colours (no text) */
#define OL_MODE_PAGE1       0x80
#define OL_MODE_PAGE2       0x81
#define ol_screen_mode(m)   ol_esc(m)

/* ------------------------------------------------------------------ keyboard */
ol_byte ol_getc(void);              /* GETC: key code or 0 */
ol_byte ol_ktst(ol_byte *mods);     /* KTST: key code or 0; *mods (if non-NULL) = modifier bits */
ol_byte ol_waitkey(void);           /* wait for a key */
#define OL_KEY_BASIC  0x01
#define OL_KEY_CNT    0x02
#define OL_KEY_SHIFT  0x04

/* ------------------------------------------------------------------ monitor graphics */
/* Coordinates: x 0..319 (0..639 in 80 columns), y 0..199. The ROM's DRAW never returns with a
 * negative coordinate, so the line functions clamp negatives to 0; ol_plot skips them and
 * ol_point returns -1. Larger values are clipped by the ROM itself. */
void    ol_plot(int x, int y, signed char color);       /* PLOT; colour -16..15 */
void    ol_moveto(int x, int y);                        /* sets PLOTX/PLOTY */
void    ol_lineto(int x, int y, signed char color);     /* DRAW from PLOTX/PLOTY */
void    ol_line(int x1, int y1, int x2, int y2, signed char color);
signed char ol_point(int x, int y);                     /* GETP */
ol_byte ol_screen_char(ol_byte col, ol_byte row);       /* GETS: col 1..40/80, row 0..24 */
void    ol_frm0(void);                                  /* select colour plane at $0000 */
void    ol_frm1(void);                                  /* select form (pixel) plane */
/* SETP: palette[index] = (palette[index] & andmask) | ormask; returns the new value.
 * Value format: %xxxMBBBB VVVVRRRR (M = opaque in overlay). */
ol_word ol_palette(ol_byte index, ol_word andmask, ol_word ormask);
void    ol_load_palette(const ol_word *table16);
#define ol_set_palette(i, v)  ol_palette((i), 0, (v))
#define ol_get_palette(i)     ol_palette((i), 0xFFFF, 0)
#define OL_RGB(r, g, b)       ((ol_word) (((b) & 15) << 8 | ((g) & 15) << 4 | ((r) & 15)))

/* ------------------------------------------------------------------ joystick, light pen, mouse */
#define OL_JOY_CENTER 0
#define OL_JOY_N  1
#define OL_JOY_NE 2
#define OL_JOY_E  3
#define OL_JOY_SE 4
#define OL_JOY_S  5
#define OL_JOY_SW 6
#define OL_JOY_W  7
#define OL_JOY_NW 8
ol_byte ol_joystick(ol_byte n, ol_byte *fire);  /* direction 0..8; *fire = 1 if pressed */
ol_byte ol_lightpen_button(void);               /* 1 if pressed */
ol_byte ol_lightpen(int *x, int *y);            /* 0 = ok, 1 = bad reading */
ol_byte ol_mouse_buttons(void);                 /* bit 0 left, bit 1 right */
ol_byte ol_mouse(int *x, int *y);               /* 0 = ok, 1 = bad reading */
#define OL_MOUSE_LEFT  1
#define OL_MOUSE_RIGHT 2

/* ------------------------------------------------------------------ sound */
void ol_beep(void);
/* notes for ol_note()/ol_play_note() */
enum { OL_REST = 0x30, OL_DO, OL_DO_S, OL_RE, OL_RE_S, OL_MI, OL_FA, OL_FA_S, OL_SOL, OL_SOL_S,
       OL_LA, OL_LA_S, OL_SI, OL_UT };
#define OL_C  OL_DO
#define OL_D  OL_RE
#define OL_E  OL_MI
#define OL_F  OL_FA
#define OL_G  OL_SOL
#define OL_A  OL_LA
#define OL_B  OL_SI
/* durations (DUREE) */
#define OL_WHOLE      96
#define OL_HALF       48
#define OL_QUARTER    24
#define OL_EIGHTH     12
#define OL_SIXTEENTH   6
void ol_note(ol_byte note);                     /* NOTE with the current OCTAVE/DUREE/TEMPO/TIMBRE */
void ol_sound_setup(ol_byte tempo, ol_byte timbre);
void ol_play_note(ol_byte note, ol_byte octave, ol_byte duration);   /* octave 1..5 (4 = A440) */

/* ------------------------------------------------------------------ printer, RS-232, disk */
ol_byte ol_printer_open(void);      /* 0 = ok */
ol_byte ol_printer_putc(char c);
ol_byte ol_printer_close(void);
ol_byte ol_printer_hardcopy(void);  /* graphic screen copy (40/80 columns) */
ol_byte ol_rs232(ol_byte opcode, ol_byte data);     /* RSCO: RS.OPC = opcode, B = data; returns CC carry */
/* DKCO sector I/O. drive 0..3, track 0..79, sector 1..16, 256-byte buffer.
 * Returns 0 or the DK.STA error code. */
#define OL_DK_INIT   0x01
#define OL_DK_READ   0x02
#define OL_DK_WRITE  0x08
#define OL_DK_SEEK0  0x20
#define OL_DK_SEEK   0x40
#define OL_DK_VERIFY 0x80
ol_byte ol_disk(ol_byte opcode, ol_byte drive, ol_word track, ol_byte sector, void *buf);
#define ol_disk_read(d, t, s, b)   ol_disk(OL_DK_READ, (d), (t), (s), (b))
#define ol_disk_write(d, t, s, b)  ol_disk(OL_DK_WRITE, (d), (t), (s), (b))

/* ================================================================== EXTRAMONITOR
 * The extramonitor lives in the other monitor ROM page. xm_begin() switches to it
 * (JSR $EFFB) and installs an error trap; xm_end() switches back and restores the
 * BASIC RAM bank. xm_call() calls xm_begin() automatically, and exit()/returning from
 * main() calls xm_end(), so you normally only call xm_end() before going back to BASIC
 * yourself (e.g. a longjmp) or to run BASIC-page ROM code.
 * Monitor ol_* services keep working while the extramonitor is mapped.
 * Every xm_* call returns the extramonitor error code (0 = ok, BASIC error numbers). */
void    xm_begin(void);
void    xm_end(void);
ol_byte xm_active(void);
/* LDB #fn / SWI2. A, X, Y, U from *r (NULL = none); outputs stored back; returns B (error). */
ol_byte xm_call(ol_byte fn, ol_regs *r);
#define xm_fn(fn)  xm_call((fn), NULL)

/* function numbers */
#define XM_RESETC     0
#define XM_RESETW     1
#define XM_FCBINI     2
#define XM_OPEN       3
#define XM_PRINT      4
#define XM_INPUT      5
#define XM_CLOSE      6
#define XM_PUTGET     7
#define XM_DIR0       8
#define XM_DIR1       9
#define XM_KILL       14
#define XM_NAME       15
#define XM_DSKF       16
#define XM_DSKINI     17
#define XM_LOF        18
#define XM_LOC        19
#define XM_ERRMSG     20
#define XM_RDVOL      21
#define XM_EDIT       22
#define XM_PLAY       23
#define XM_CIRCLE     24
#define XM_PSETXY     25
#define XM_LINE       26
#define XM_BOX        27
#define XM_CHOIX      28
#define XM_PAINT      29
#define XM_MIG        30
#define XM_TRACE      31
#define XM_ANIME      32
#define XM_SHOW       33
#define XM_HEAD       34
#define XM_ROT        35
#define XM_ZOOM       36
#define XM_FWD        37
#define XM_MOVE       38
#define XM_INITORTUE  39
#define XM_CMPTORTUE  40
#define XM_SGN        41
#define XM_INT        42
#define XM_ABS        43
#define XM_SQR        44
#define XM_LOG        45
#define XM_EXP        46
#define XM_COS        47
#define XM_SIN        48
#define XM_TAN        49
#define XM_FRCTYP     50
#define XM_FIXER      51
#define XM_RND        52
#define XM_NEGGO      53
#define XM_ADDGO      54
#define XM_SUBGO      55
#define XM_MULTGO     56
#define XM_DIVGO      57
#define XM_EXPGO      58
#define XM_IMODO      59
#define XM_IDIVO      60
#define XM_MOVFM      62
#define XM_MOVMF      63
#define XM_MOVAF      64
#define XM_FIN        65
#define XM_PUFOUT     66
#define XM_HOFOUT     67
#define XM_ATN        68
#define XM_CODE       69
#define XM_INICACHE   70

/* extramonitor RAM registers */
#define XM_DBLFLG   0x2103
#define XM_VALTYP   0x2105      /* 2 int, 4 single, 8 double */
#define XM_FAC      0x214E      /* FACEXP; FACHO 214F, FACMO 2150, FACLO 2151, FACSGN 2156 */
#define XM_FACMO    0x2150      /* 16-bit integer in FAC */
#define XM_ARG      0x2159
#define XM_DEBZON   0x216B      /* work area start (PAINT, CODE) */
#define XM_FINZON   0x216E      /* work area end */
#define XM_SAVSTK   0x2175
#define XM_EOFFLG   0x2178
#define XM_DPWID    0x217A
#define XM_FLDWID   0x217B
#define XM_PUMASK   0x217C
#define XM_ZPERR    0x2185      /* error routine pointer */
#define XM_NAMSEC   0x218E
#define XM_NAMSLT   0x218F
#define XM_CARCOU   0x2196
#define XM_SECBUF   0x2197
#define XM_COULEUR  0x219F
#define XM_TRATYP   0x21A0
#define XM_XXXXX    0x21A1      /* graphic cursor (word) */
#define XM_YYYYY    0x21A3
#define XM_XL       0x21A5      /* clipping window (words) */
#define XM_YB       0x21A7
#define XM_XR       0x21A9
#define XM_YT       0x21AB
#define XM_DEFTXT   0x21E0
#define XM_FILFLG   0x21EF
#define XM_AXEV     0x21F0
#define XM_AXEH     0x21F1
#define XM_CAMFLG   0x21F2
#define XM_ALPHA1   0x21F3
#define XM_ALPHA2   0x21F7
#define XM_FCBNUM   0x2244
#define XM_FILMOD   0x224B
#define XM_FILNAM   0x224F
#define XM_MACP     0x227D      /* pointer to an 8-byte fill pattern */
#define XM_WITH     0x2288      /* 0 = with colour, $FF = form plane only */

/* ------------------------------------------------------------------ extramonitor graphics
 * Select the screen mode with ol_screen_mode() first; xm_screen() sets a full-screen
 * window for it. Coordinates are clipped to the window. */
#define XM_PSET   0     /* TRATYP */
#define XM_OR     1
#define XM_XOR    2
#define XM_AND    3
void    xm_window(int x1, int y1, int x2, int y2);   /* clipping window: top-left, bottom-right (inclusive) */
ol_byte xm_screen(ol_byte mode);                     /* full-screen window for OL_MODE_xxx */
ol_byte xm_style(signed char color, ol_byte tratyp, ol_byte form_only);  /* CHOIX */
#define xm_color(c)  xm_style((c), XM_PSET, 0)
void    xm_moveto(int x, int y);                     /* graphic cursor XXXXX/YYYYY */
ol_byte xm_pset(int x, int y);
ol_byte xm_lineto(int x, int y);
ol_byte xm_line(int x1, int y1, int x2, int y2);
ol_byte xm_box(int x1, int y1, int x2, int y2, ol_byte filled);
ol_byte xm_ellipse(int cx, int cy, ol_byte rx, ol_byte ry, ol_byte filled);
#define xm_circle(cx, cy, r, filled)  xm_ellipse((cx), (cy), (r), (r), (filled))
ol_byte xm_paint(int x, int y, void *work, ol_word size);
void    xm_pattern(const ol_byte *pattern8);         /* NULL = solid */
ol_byte xm_mig(const ol_byte *program, int x, int y);

/* ------------------------------------------------------------------ extramonitor maths
 * xm_real is the 4-byte memory format (exponent, 3-byte mantissa with the sign in bit 7). */
typedef struct xm_real { ol_byte b[4]; } xm_real;
ol_byte xm_from_int(xm_real *r, int n);
ol_byte xm_to_int(const xm_real *a, int *n);              /* rounds like BASIC CINT */
ol_byte xm_from_str(xm_real *r, const char *s);           /* "3.14", "-1E3", "&H1F" ... */
ol_byte xm_to_str(const xm_real *a, char *buf);           /* buf >= 20 bytes */
ol_byte xm_op(ol_byte fn, const xm_real *a, const xm_real *b, xm_real *r);   /* r = a OP b */
ol_byte xm_func(ol_byte fn, const xm_real *a, xm_real *r);                   /* r = fn(a) */
#define xm_add(a, b, r)  xm_op(XM_ADDGO, (a), (b), (r))
#define xm_sub(a, b, r)  xm_op(XM_SUBGO, (a), (b), (r))
#define xm_mul(a, b, r)  xm_op(XM_MULTGO, (a), (b), (r))
#define xm_div(a, b, r)  xm_op(XM_DIVGO, (a), (b), (r))
#define xm_pow(a, b, r)  xm_op(XM_EXPGO, (a), (b), (r))
#define xm_neg(a, r)     xm_func(XM_NEGGO, (a), (r))
#define xm_abs(a, r)     xm_func(XM_ABS, (a), (r))
#define xm_int(a, r)     xm_func(XM_INT, (a), (r))
#define xm_fix(a, r)     xm_func(XM_FIXER, (a), (r))
#define xm_sgn(a, r)     xm_func(XM_SGN, (a), (r))
#define xm_sqr(a, r)     xm_func(XM_SQR, (a), (r))
#define xm_log(a, r)     xm_func(XM_LOG, (a), (r))
#define xm_exp(a, r)     xm_func(XM_EXP, (a), (r))
#define xm_sin(a, r)     xm_func(XM_SIN, (a), (r))
#define xm_cos(a, r)     xm_func(XM_COS, (a), (r))
#define xm_tan(a, r)     xm_func(XM_TAN, (a), (r))
#define xm_atn(a, r)     xm_func(XM_ATN, (a), (r))
ol_byte xm_rnd(xm_real *r);                               /* 0 <= r < 1 */
ol_byte xm_hex(int n, char *buf, ol_byte hex);            /* HOFOUT: hex (1) or octal (0) */

/* ------------------------------------------------------------------ extramonitor misc */
ol_byte xm_play(const char *music);                 /* BASIC PLAY syntax, e.g. "O4L24DOREMI" */
const char *xm_errmsg(ol_byte err, char *buf);      /* error text (buf >= 40 bytes) */

#endif
