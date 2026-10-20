/* xm_gfx.c - extramonitor graphics (clipped to the XL/YB/XR/YT window) */
#include <olivetti.h>

static const ol_byte xm_solid[8] = { 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };
static const ol_byte *xm_cur_pattern;

void xm_window(int x1, int y1, int x2, int y2)
{
    OL_POKEW(XM_XL, x1);
    OL_POKEW(XM_YB, y1);
    OL_POKEW(XM_XR, x2);
    OL_POKEW(XM_YT, y2);
}

ol_byte xm_screen(ol_byte mode)
{
    int w = 319;
    if (mode == OL_MODE_80COL)
        w = 639;
    else if (mode == OL_MODE_BITMAP16)
        w = 159;
    xm_window(0, 0, w, 199);
    return xm_style(OL_WHITE, XM_PSET, 0);
}

ol_byte xm_style(signed char color, ol_byte tratyp, ol_byte form_only)
{
    OL_POKE(XM_COULEUR, color);
    OL_POKE(XM_TRATYP, tratyp);
    OL_POKE(XM_WITH, form_only ? 0xFF : 0);
    return xm_fn(XM_CHOIX);
}

void xm_moveto(int x, int y)
{
    OL_POKEW(XM_XXXXX, x);
    OL_POKEW(XM_YYYYY, y);
}

static ol_byte xy_call(ol_byte fn, int x, int y)
{
    ol_regs r;
    r.x = (ol_word) x;
    r.y = (ol_word) y;
    return xm_call(fn, &r);
}

ol_byte xm_pset(int x, int y)   { return xy_call(XM_PSETXY, x, y); }
ol_byte xm_lineto(int x, int y) { return xy_call(XM_LINE, x, y); }

ol_byte xm_line(int x1, int y1, int x2, int y2)
{
    xm_moveto(x1, y1);
    return xy_call(XM_LINE, x2, y2);
}

static void set_fill(ol_byte filled)
{
    OL_POKE(XM_FILFLG, filled ? 0xFF : 0);
    if (filled)
        OL_POKEW(XM_MACP, (ol_word) (xm_cur_pattern ? xm_cur_pattern : xm_solid));
}

ol_byte xm_box(int x1, int y1, int x2, int y2, ol_byte filled)
{
    set_fill(filled);
    xm_moveto(x1, y1);
    return xy_call(XM_BOX, x2, y2);
}

ol_byte xm_ellipse(int cx, int cy, ol_byte rx, ol_byte ry, ol_byte filled)
{
    set_fill(filled);
    OL_POKE(XM_CAMFLG, 0);
    OL_POKE(XM_AXEH, rx);
    OL_POKE(XM_AXEV, ry);
    xm_moveto(cx, cy);
    return xm_fn(XM_CIRCLE);
}

ol_byte xm_paint(int x, int y, void *work, ol_word size)
{
    OL_POKEW(XM_DEBZON, (ol_word) work);
    OL_POKEW(XM_FINZON, (ol_word) work + size);
    OL_POKEW(XM_MACP, (ol_word) (xm_cur_pattern ? xm_cur_pattern : xm_solid));
    xm_moveto(x, y);
    return xm_fn(XM_PAINT);
}

void xm_pattern(const ol_byte *pattern8)
{
    xm_cur_pattern = pattern8;
}

ol_byte xm_mig(const ol_byte *program, int x, int y)
{
    ol_regs r;
    xm_moveto(x, y);
    r.x = (ol_word) program;
    return xm_call(XM_MIG, &r);
}
