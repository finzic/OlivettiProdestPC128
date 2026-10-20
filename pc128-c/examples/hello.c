/* hello.c - text output with the monitor wrappers and printf */
#include <cmoc.h>
#include <olivetti.h>

int main(void)
{
    ol_byte i;
    ol_cls();
    ol_border(OL_BLUE);
    ol_color(OL_RED);
    ol_puts("Hello from C on the Olivetti PC128!\n");
    ol_color(OL_BLACK);
    for (i = 1; i <= 5; i++)
        printf("%u squared is %u\n", i, i * i);
    ol_locate(10, 12);
    ol_color(OL_BLUE);
    ol_puts("at column 10, row 12");
    ol_locate(0, 14);
    ol_puts("hex: $");
    ol_print_hex(0xBEEF, 4);
    ol_puts("  int: ");
    ol_print_int(-1234);
    ol_puts("\n");
    ol_color(OL_BLACK);

    ol_debug_byte(0, ol_screen_char(11, 12));   /* 'a' of "at" read back from the screen */
    ol_debug_word(2, 0x1234);
    ol_done();
    return 0;
}
