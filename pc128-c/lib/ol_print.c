/* ol_print.c - small number printing without printf */
#include <olivetti.h>

void ol_print_uint(ol_word n)
{
    char buf[6];
    ol_byte i = 5;
    buf[5] = 0;
    do {
        buf[--i] = (char) ('0' + n % 10);
        n /= 10;
    } while (n != 0);
    ol_puts(buf + i);
}

void ol_print_int(int n)
{
    if (n < 0) {
        ol_putc('-');
        ol_print_uint((ol_word) -n);
    } else
        ol_print_uint((ol_word) n);
}

void ol_print_hex(ol_word n, ol_byte digits)
{
    char buf[5];
    ol_byte i;
    if (digits > 4)
        digits = 4;
    for (i = digits; i > 0; i--) {
        ol_byte d = (ol_byte) (n & 15);
        buf[i - 1] = (char) (d < 10 ? d + 48 : d + 55);
        n >>= 4;
    }
    buf[digits] = 0;
    ol_puts(buf);
}
