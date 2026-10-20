/* xm_misc.c - PLAY and error messages */
#include <olivetti.h>

ol_byte xm_play(const char *music)
{
    ol_regs r;
    const char *p = music;
    while (*p)
        p++;
    r.a = (ol_byte) (p - music);
    r.y = (ol_word) music;
    return xm_call(XM_PLAY, &r);
}

const char *xm_errmsg(ol_byte err, char *buf)
{
    ol_regs r;
    buf[0] = 0;
    r.a = err;
    r.x = (ol_word) buf;
    if (xm_call(XM_ERRMSG, &r))
        return buf;
    return (const char *) r.x;
}
