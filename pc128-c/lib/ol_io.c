/* ol_io.c - printer (PRCO), RS-232 (RSCO) and disk sectors (DKCO) */
#include <olivetti.h>

static ol_byte prco(ol_byte opcode, char c)
{
    ol_regs r;
    OL_POKE(OL_PR_OPC, opcode);
    r.b = (ol_byte) c;
    return ol_swi(OL_SWI_PRCO, &r) & OL_CC_C;
}

ol_byte ol_printer_open(void)     { return prco(0x04, 0); }
ol_byte ol_printer_putc(char c)   { return prco(0x01, c); }
ol_byte ol_printer_close(void)    { return prco(0x10, 0); }
ol_byte ol_printer_hardcopy(void) { return prco(0x02, 0); }

ol_byte ol_rs232(ol_byte opcode, ol_byte data)
{
    ol_regs r;
    OL_POKE(OL_RS_OPC, opcode);
    r.b = data;
    return ol_swi(OL_SWI_RSCO, &r) & OL_CC_C;
}

ol_byte ol_disk(ol_byte opcode, ol_byte drive, ol_word track, ol_byte sector, void *buf)
{
    ol_regs r;
    OL_POKE(OL_DK_OPC, opcode);
    OL_POKE(OL_DK_DRV, drive);
    OL_POKEW(OL_DK_TRK, track);
    OL_POKE(OL_DK_SEC, sector);
    OL_POKEW(OL_DK_BUF, (ol_word) buf);
    if (ol_swi(OL_SWI_DKCO, &r) & OL_CC_C)
        return OL_PEEK(OL_DK_STA) ? OL_PEEK(OL_DK_STA) : 0xFF;
    return 0;
}
