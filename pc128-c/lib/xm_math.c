/* xm_math.c - extramonitor real-number maths on 4-byte reals */
#include <olivetti.h>

static ol_byte load(const xm_real *a)           /* FAC := *a (single) */
{
    ol_regs r;
    OL_POKE(XM_DBLFLG, 0);
    OL_POKE(XM_VALTYP, 4);
    r.x = (ol_word) a;
    return xm_call(XM_MOVFM, &r);
}

static ol_byte force(ol_byte type)              /* FRCTYP */
{
    ol_regs r;
    if (OL_PEEK(XM_VALTYP) == type)
        return 0;
    r.a = type;
    return xm_call(XM_FRCTYP, &r);
}

static ol_byte store(xm_real *res)              /* *res := FAC as a single */
{
    ol_regs r;
    ol_byte e = force(4);
    if (e)
        return e;
    r.x = (ol_word) res;
    return xm_call(XM_MOVMF, &r);
}

ol_byte xm_from_int(xm_real *res, int n)
{
    OL_POKE(XM_DBLFLG, 0);
    OL_POKEW(XM_FACMO, n);
    OL_POKE(XM_VALTYP, 2);
    return store(res);
}

ol_byte xm_to_int(const xm_real *a, int *n)
{
    ol_byte e = load(a);
    if (!e)
        e = force(2);
    if (!e)
        *n = (int) OL_PEEKW(XM_FACMO);
    return e;
}

ol_byte xm_from_str(xm_real *res, const char *s)
{
    ol_regs r;
    ol_byte e;
    OL_POKE(XM_DBLFLG, 0);
    r.y = (ol_word) s;
    e = xm_call(XM_FIN, &r);
    return e ? e : store(res);
}

ol_byte xm_to_str(const xm_real *a, char *buf)
{
    static char tmp[24];
    ol_regs r;
    ol_byte e, i;
    const char *p;
    for (i = 0; i < sizeof(tmp); i++)
        tmp[i] = 0;
    e = load(a);
    if (e)
        return e;
    OL_POKE(XM_PUMASK, 0);
    r.y = (ol_word) tmp;
    e = xm_call(XM_PUFOUT, &r);
    if (e)
        return e;
    /* the manual says FACMO points to the text; in practice it is written a byte or
       two into the buffer and FACMO is not updated: take the first non-NUL byte */
    p = (const char *) OL_PEEKW(XM_FACMO);
    if (p < tmp || p >= tmp + sizeof(tmp)) {
        p = tmp;
        while (*p == 0 && p < tmp + sizeof(tmp) - 1)
            p++;
    }
    while (*p == ' ')
        p++;
    while ((*buf++ = *p++) != 0)
        ;
    return 0;
}

ol_byte xm_op(ol_byte fn, const xm_real *a, const xm_real *b, xm_real *res)
{
    ol_byte e = load(a);
    if (!e)
        e = xm_fn(XM_MOVAF);
    if (!e)
        e = load(b);
    if (!e)
        e = xm_fn(fn);
    return e ? e : store(res);
}

ol_byte xm_func(ol_byte fn, const xm_real *a, xm_real *res)
{
    ol_byte e = load(a);
    if (!e)
        e = xm_fn(fn);
    return e ? e : store(res);
}

ol_byte xm_rnd(xm_real *res)
{
    ol_byte e;
    OL_POKE(XM_DBLFLG, 0);
    e = xm_fn(XM_RND);
    return e ? e : store(res);
}

ol_byte xm_hex(int n, char *buf, ol_byte hex)
{
    ol_regs r;
    OL_POKEW(XM_FACMO, n);
    OL_POKE(XM_VALTYP, 2);
    buf[0] = 0;
    r.a = hex ? 0xFF : 0;
    r.y = (ol_word) buf;
    return xm_call(XM_HOFOUT, &r);
}
