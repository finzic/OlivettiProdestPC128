/* xmdemo.c - EXTRAMONITOR from C: clipped graphics, real maths, PLAY, error messages */
#include <olivetti.h>

static void print_real(const char *label, const xm_real *v)
{
    char buf[24];
    ol_puts(label);
    if (xm_to_str(v, buf) == 0)
        ol_puts(buf);
    ol_puts("\n");
}

static const ol_byte hatch[8] = { 0x88, 0x44, 0x22, 0x11, 0x88, 0x44, 0x22, 0x11 };

int main(void)
{
    xm_real a, b, r;
    char msg[48];
    ol_byte e;
    int i;

    ol_cls();
    xm_screen(OL_MODE_40COL);           /* full-screen window, CHOIX white */
    xm_window(0, 64, 319, 199);         /* graphics below the text */
    xm_color(OL_RED);
    xm_box(10, 70, 150, 190, 0);
    xm_color(OL_BLUE);
    xm_box(20, 80, 140, 120, 1);
    xm_pattern(hatch);
    xm_color(OL_MAGENTA);
    xm_box(20, 130, 140, 180, 1);
    xm_pattern(NULL);
    xm_color(OL_GREEN);
    xm_circle(235, 130, 50, 0);
    xm_color(OL_YELLOW);
    xm_ellipse(235, 130, 30, 15, 1);
    xm_style(OL_BLACK, XM_XOR, 0);
    for (i = 0; i < 320; i += 16)
        xm_line(i, 0, 319 - i, 199);    /* clipped to the window */

    /* maths: 4-byte reals */
    xm_from_int(&a, 2);
    xm_sqr(&a, &r);
    ol_color(OL_BLACK);
    print_real("SQR(2)   = ", &r);
    xm_from_str(&a, "3.14159265");
    xm_from_int(&b, 4);
    xm_div(&a, &b, &r);
    xm_sin(&r, &r);
    print_real("SIN(PI/4)= ", &r);
    xm_from_str(&a, "1E10");
    xm_from_str(&b, "7");
    xm_div(&a, &b, &r);
    print_real("1E10/7   = ", &r);
    xm_from_int(&b, 0);
    e = xm_div(&a, &b, &r);             /* error trapped, returns code 11 */
    ol_puts("1/0 -> ");
    ol_print_uint(e);
    ol_puts(" ");
    ol_puts(xm_errmsg(e, msg));
    ol_puts("\n");

    xm_play("T5O4L24DOREMI");
    xm_end();                           /* optional: exit()/return also does it */

    ol_debug_byte(0, e);
    ol_debug_byte(1, xm_active());
    ol_done();
    return 0;
}
