/* graphics.c - ROM monitor graphics: PLOT, DRAW, GETP, palette */
#include <olivetti.h>

int main(void)
{
    int i;
    ol_cls();
    ol_border(OL_BLACK);
    /* star of lines from the centre */
    for (i = 0; i <= 320; i += 20) {
        ol_line(160, 100, i, 0, (signed char) (i / 20 % 15 + 1));
        ol_line(160, 100, 319 - i, 199, (signed char) ((i / 20 + 7) % 15 + 1));
    }
    /* a box drawn with moveto/lineto */
    ol_moveto(20, 20);
    ol_lineto(100, 20, OL_RED);
    ol_lineto(100, 60, OL_RED);
    ol_lineto(20, 60, OL_RED);
    ol_lineto(20, 20, OL_RED);
    /* a dotted row of points */
    for (i = 0; i < 320; i += 4)
        ol_plot(i, 190, OL_BLUE);

    ol_debug_byte(0, (ol_byte) ol_point(40, 20));   /* 1 = red */
    ol_debug_byte(1, (ol_byte) ol_point(4, 190));   /* 4 = blue */
    ol_debug_word(2, ol_get_palette(OL_RED));
    ol_set_palette(OL_RED, OL_RGB(15, 8, 0));       /* make "red" orange */
    ol_debug_word(4, ol_get_palette(OL_RED));
    ol_locate(1, 23);
    ol_puts("monitor PLOT/DRAW");
    ol_done();
    return 0;
}
