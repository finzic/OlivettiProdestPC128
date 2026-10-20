/* mixed.c - C calling assembly (asmlib.asm) and assembly calling back into C
 * pc128cc: sources=asmlib.asm
 */
#include <olivetti.h>

ol_word sum_bytes(const ol_byte *p, ol_word n);
void put_stars(ol_byte n);
void for_each_char(const char *s, void (*fn)(char));

unsigned int counter;                   /* incremented by put_stars() */

static void upper(char c)
{
    if (c >= 'a' && c <= 'z')
        c -= 32;
    ol_putc(c);
}

int main(void)
{
    static const ol_byte data[] = { 1, 2, 3, 250, 100 };
    ol_word s;

    ol_cls();
    s = sum_bytes(data, sizeof data);
    ol_puts("sum = ");
    ol_print_uint(s);
    ol_puts("\r\n");

    put_stars(10);
    ol_puts("\r\n");

    for_each_char("called back from asm", upper);
    ol_puts("\r\n");

    ol_debug_word(0, s);                /* 356 = 01 64 */
    ol_debug_word(2, counter);          /* 10 = 00 0A */
    ol_done();
    return 0;
}
