A000: 4D          TSTA
A001: 4B          XDECA
A002: 43          COMA
A003: 30 16       LEAX   -$A,X
A005: 00 F3       NEG    $F3
A007: 16 00 A5    LBRA   $A0AF
A00A: 16 03 A7    LBRA   $A3B4
A00D: 16 05 5A    LBRA   $A56A
A010: 16 05 84    LBRA   $A597
A013: 16 06 7E    LBRA   $A694
A016: 16 05 71    LBRA   $A58A
A019: 16 05 DA    LBRA   $A5F6
A01C: 16 06 31    LBRA   $A650
A01F: 16 06 91    LBRA   $A6B3
A022: 16 05 08    LBRA   $A52D
A025: 16 00 CA    LBRA   $A0F2
A028: 16 00 D4    LBRA   $A0FF
A02B: 34 46       PSHS   U,D
A02D: 33 8C D4    LEAU   $A004,PCR
A030: 86 00       LDA    #$00
A032: 8D 68       BSR    $A09C
A034: 35 C6       PULS   D,U,PC
A036: 34 46       PSHS   U,D
A038: 33 8C CC    LEAU   $A007,PCR
A03B: 86 00       LDA    #$00
A03D: 8D 5D       BSR    $A09C
A03F: 35 C6       PULS   D,U,PC
A041: 34 46       PSHS   U,D
A043: 33 8C C4    LEAU   $A00A,PCR
A046: 86 01       LDA    #$01
A048: 8D 52       BSR    $A09C
A04A: 35 C6       PULS   D,U,PC
A04C: 33 8C BE    LEAU   $A00D,PCR
A04F: 86 02       LDA    #$02
A051: 8D 49       BSR    $A09C
A053: 1F 30       TFR    U,D
A055: 39          RTS
A056: 33 8C B7    LEAU   $A010,PCR
A059: 86 02       LDA    #$02
A05B: 8D 3F       BSR    $A09C
A05D: 1F 30       TFR    U,D
A05F: 39          RTS
A060: 33 8C B0    LEAU   $A013,PCR
A063: 86 02       LDA    #$02
A065: 8D 35       BSR    $A09C
A067: 1F 30       TFR    U,D
A069: 39          RTS
A06A: 33 8C A9    LEAU   $A016,PCR
A06D: 86 02       LDA    #$02
A06F: 8D 2B       BSR    $A09C
A071: 1F 30       TFR    U,D
A073: 39          RTS
A074: 33 8C A2    LEAU   $A019,PCR
A077: 86 02       LDA    #$02
A079: 8D 21       BSR    $A09C
A07B: 1F 30       TFR    U,D
A07D: 39          RTS
A07E: 33 8C 9B    LEAU   $A01C,PCR
A081: 86 02       LDA    #$02
A083: 8D 17       BSR    $A09C
A085: 1F 30       TFR    U,D
A087: 39          RTS
A088: 33 8C 94    LEAU   $A01F,PCR
A08B: 86 02       LDA    #$02
A08D: 8D 0D       BSR    $A09C
A08F: 1F 30       TFR    U,D
A091: 39          RTS
A092: 33 8C 8D    LEAU   $A022,PCR
A095: 86 02       LDA    #$02
A097: 8D 03       BSR    $A09C
A099: 1F 30       TFR    U,D
A09B: 39          RTS
A09C: C6 00       LDB    #$00
A09E: 34 04       PSHS   B
A0A0: A7 8D 07 34 STA    $A7D8,PCR
A0A4: 6E C4       JMP    ,U
A0A6: 1F 03       TFR    D,U
A0A8: 35 04       PULS   B
A0AA: E7 8D 07 2A STB    $A7D8,PCR
A0AE: 39          RTS
A0AF: 17 00 66    LBSR   $A118
A0B2: 0F 49       CLR    $49
A0B4: 17 00 7A    LBSR   $A131
A0B7: 17 00 AE    LBSR   $A168
A0BA: CC 00 44    LDD    #$0044
A0BD: DD 4C       STD    $4C
A0BF: 33 8D 81 3D LEAU   $2200,PCR
A0C3: DF 4F       STU    $4F
A0C5: 17 01 DC    LBSR   $A2A4
A0C8: DE 4F       LDU    $4F
A0CA: 25 20       BCS    $A0EC
A0CC: 17 00 7F    LBSR   $A14E
A0CF: 31 8D 81 AC LEAY   $227F,PCR
A0D3: 34 20       PSHS   Y
A0D5: 86 55       LDA    #$55
A0D7: 6A C4       DEC    ,U
A0D9: 63 C4       COM    ,U
A0DB: AB C0       ADDA   ,U+
A0DD: 11 A3 E4    CMPU   ,S
A0E0: 26 F5       BNE    $A0D7
A0E2: 35 20       PULS   Y
A0E4: A1 C4       CMPA   ,U
A0E6: 26 04       BNE    $A0EC
A0E8: 6E 8D 81 14 JMP    $2200,PCR
A0EC: 0F 80       CLR    $80
A0EE: 6E 9F 00 1E JMP    [$001E]
A0F2: 34 7F       PSHS   U,Y,X,DP,D,CC
A0F4: 8D 22       BSR    $A118
A0F6: 86 FF       LDA    #$FF
A0F8: 20 05       BRA    $A0FF
A0FA: 34 7F       PSHS   U,Y,X,DP,D,CC
A0FC: 8D 1A       BSR    $A118
A0FE: 4F          CLRA
A0FF: 97 4A       STA    $4A
A101: DC 4B       LDD    $4B
A103: 34 06       PSHS   D
A105: 8D 2A       BSR    $A131
A107: 25 04       BCS    $A10D
A109: 8D 4C       BSR    $A157
A10B: 8D 41       BSR    $A14E
A10D: 35 06       PULS   D
A10F: DD 4B       STD    $4B
A111: 35 02       PULS   A
A113: 1E 8A       EXG    A,CC
A115: 44          LSRA
A116: 35 FE       PULS   D,DP,X,Y,U,PC
A118: 1F 50       TFR    PC,D
A11A: 84 70       ANDA   #$70
A11C: 1F 8B       TFR    A,DP
A11E: 30 8D 06 AE LEAX   $A7D0,PCR
A122: 0F 4E       CLR    $4E
A124: 6F 84       CLR    ,X
A126: 86 CE       LDA    #$CE
A128: A7 07       STA    $7,X
A12A: 86 FF       LDA    #$FF
A12C: A7 04       STA    $4,X
A12E: 6F 01       CLR    $1,X
A130: 39          RTS
A131: D6 49       LDB    $49
A133: C5 FD       BITB   #$FD
A135: 26 12       BNE    $A149
A137: 33 8D 00 18 LEAU   $A153,PCR
A13B: A6 C5       LDA    B,U
A13D: A7 02       STA    $2,X
A13F: 97 57       STA    $57
A141: E6 01       LDB    $1,X
A143: C5 40       BITB   #$40
A145: 26 02       BNE    $A149
A147: 4F          CLRA
A148: 39          RTS
A149: 86 10       LDA    #$10
A14B: 16 01 BD    LBRA   $A30B
A14E: 86 00       LDA    #$00
A150: A7 02       STA    $2,X
A152: 39          RTS
A153: 01 00       NEG    $00
A155: 02 00       XNC    $00
A157: 96 48       LDA    $48
A159: 85 01       BITA   #$01
A15B: 26 0B       BNE    $A168
A15D: 85 08       BITA   #$08
A15F: 26 12       BNE    $A173
A161: 85 02       BITA   #$02
A163: 10 26 01 35 LBNE   $A29C
A167: 39          RTS
A168: 86 43       LDA    #$43
A16A: 97 4E       STA    $4E
A16C: 86 FF       LDA    #$FF
A16E: 97 58       STA    $58
A170: 6F 84       CLR    ,X
A172: 39          RTS
A173: 96 4A       LDA    $4A
A175: 26 05       BNE    $A17C
A177: 17 01 A3    LBSR   $A31D
A17A: 25 5A       BCS    $A1D6
A17C: 17 00 5C    LBSR   $A1DB
A17F: 25 55       BCS    $A1D6
A181: 17 00 E3    LBSR   $A267
A184: 25 50       BCS    $A1D6
A186: 34 01       PSHS   CC
A188: 17 00 5D    LBSR   $A1E8
A18B: 25 4A       BCS    $A1D7
A18D: C6 FF       LDB    #$FF
A18F: E7 04       STB    $4,X
A191: 86 06       LDA    #$06
A193: C6 04       LDB    #$04
A195: E7 84       STB    ,X
A197: E6 84       LDB    ,X
A199: 2A FC       BPL    $A197
A19B: C6 16       LDB    #$16
A19D: E7 03       STB    $3,X
A19F: 4A          DECA
A1A0: 26 F5       BNE    $A197
A1A2: E6 84       LDB    ,X
A1A4: 2A FC       BPL    $A1A2
A1A6: C6 5A       LDB    #$5A
A1A8: E7 03       STB    $3,X
A1AA: D7 4A       STB    $4A
A1AC: 86 80       LDA    #$80
A1AE: E6 84       LDB    ,X
A1B0: 2A FC       BPL    $A1AE
A1B2: E6 C0       LDB    ,U+
A1B4: E7 03       STB    $3,X
A1B6: DB 4A       ADDB   $4A
A1B8: D7 4A       STB    $4A
A1BA: 4A          DECA
A1BB: 26 F1       BNE    $A1AE
A1BD: E6 84       LDB    ,X
A1BF: 2A FC       BPL    $A1BD
A1C1: D6 4A       LDB    $4A
A1C3: E7 03       STB    $3,X
A1C5: E6 84       LDB    ,X
A1C7: 2A FC       BPL    $A1C5
A1C9: C6 16       LDB    #$16
A1CB: E7 03       STB    $3,X
A1CD: E6 84       LDB    ,X
A1CF: 2A FC       BPL    $A1CD
A1D1: 6F 84       CLR    ,X
A1D3: 35 01       PULS   CC
A1D5: 5F          CLRB
A1D6: 39          RTS
A1D7: 35 01       PULS   CC
A1D9: 43          COMA
A1DA: 39          RTS
A1DB: A6 01       LDA    $1,X
A1DD: 85 04       BITA   #$04
A1DF: 26 02       BNE    $A1E3
A1E1: 4F          CLRA
A1E2: 39          RTS
A1E3: 86 01       LDA    #$01
A1E5: 16 01 23    LBRA   $A30B
A1E8: DE 4F       LDU    $4F
A1EA: 86 02       LDA    #$02
A1EC: 1A 50       ORCC   #$50
A1EE: C6 E0       LDB    #$E0
A1F0: E7 04       STB    $4,X
A1F2: C6 16       LDB    #$16
A1F4: E7 03       STB    $3,X
A1F6: C6 18       LDB    #$18
A1F8: E7 84       STB    ,X
A1FA: C1 16       CMPB   #$16
A1FC: 27 0E       BEQ    $A20C
A1FE: E6 01       LDB    $1,X
A200: C5 02       BITB   #$02
A202: 27 47       BEQ    $A24B
A204: E6 84       LDB    ,X
A206: C5 01       BITB   #$01
A208: 27 F4       BEQ    $A1FE
A20A: E6 03       LDB    $3,X
A20C: E6 01       LDB    $1,X
A20E: C5 02       BITB   #$02
A210: 27 39       BEQ    $A24B
A212: E6 84       LDB    ,X
A214: 2A F6       BPL    $A20C
A216: E6 03       LDB    $3,X
A218: C1 A5       CMPB   #$A5
A21A: 26 DE       BNE    $A1FA
A21C: D7 4A       STB    $4A
A21E: C6 08       LDB    #$08
A220: E7 84       STB    ,X
A222: E6 84       LDB    ,X
A224: 2A FC       BPL    $A222
A226: E6 03       LDB    $3,X
A228: D1 4C       CMPB   $4C
A22A: 26 C6       BNE    $A1F2
A22C: DB 4A       ADDB   $4A
A22E: D7 4A       STB    $4A
A230: E6 84       LDB    ,X
A232: 2A FC       BPL    $A230
A234: E6 03       LDB    $3,X
A236: D1 4D       CMPB   $4D
A238: 26 B8       BNE    $A1F2
A23A: DB 4A       ADDB   $4A
A23C: D7 4A       STB    $4A
A23E: E6 84       LDB    ,X
A240: 2A FC       BPL    $A23E
A242: E6 03       LDB    $3,X
A244: D1 4A       CMPB   $4A
A246: 26 AA       BNE    $A1F2
A248: 6F 84       CLR    ,X
A24A: 39          RTS
A24B: 4D          TSTA
A24C: 27 05       BEQ    $A253
A24E: 4A          DECA
A24F: 8D 16       BSR    $A267
A251: 20 AB       BRA    $A1FE
A253: 86 04       LDA    #$04
A255: 16 00 B3    LBRA   $A30B
A258: 10 8E 35 B6 LDY    #$35B6
A25C: 20 04       BRA    $A262
A25E: 10 8E 4E 20 LDY    #$4E20
A262: 31 3F       LEAY   -$1,Y
A264: 26 FC       BNE    $A262
A266: 39          RTS
A267: 8D 0A       BSR    $A273
A269: 25 07       BCS    $A272
A26B: 81 12       CMPA   #$12
A26D: 27 02       BEQ    $A271
A26F: 8D E7       BSR    $A258
A271: 4F          CLRA
A272: 39          RTS
A273: 86 12       LDA    #$12
A275: D6 57       LDB    $57
A277: CA 40       ORB    #$40
A279: E7 02       STB    $2,X
A27B: E6 01       LDB    $1,X
A27D: C5 02       BITB   #$02
A27F: 26 15       BNE    $A296
A281: 4A          DECA
A282: 10 27 FE C3 LBEQ   $A149
A286: 10 8E 6C 80 LDY    #$6C80
A28A: 31 3F       LEAY   -$1,Y
A28C: 27 F3       BEQ    $A281
A28E: E6 01       LDB    $1,X
A290: C5 02       BITB   #$02
A292: 27 F6       BEQ    $A28A
A294: 8D C8       BSR    $A25E
A296: D6 57       LDB    $57
A298: E7 02       STB    $2,X
A29A: 5F          CLRB
A29B: 39          RTS
A29C: 96 4A       LDA    $4A
A29E: 26 04       BNE    $A2A4
A2A0: 8D 7B       BSR    $A31D
A2A2: 25 72       BCS    $A316
A2A4: 86 02       LDA    #$02
A2A6: 34 02       PSHS   A
A2A8: 17 FF BC    LBSR   $A267
A2AB: 25 67       BCS    $A314
A2AD: 34 01       PSHS   CC
A2AF: 17 FF 36    LBSR   $A1E8
A2B2: 25 5D       BCS    $A311
A2B4: 86 03       LDA    #$03
A2B6: E6 84       LDB    ,X
A2B8: 2A FC       BPL    $A2B6
A2BA: E6 03       LDB    $3,X
A2BC: 4A          DECA
A2BD: 26 F7       BNE    $A2B6
A2BF: 86 80       LDA    #$80
A2C1: C6 18       LDB    #$18
A2C3: E7 84       STB    ,X
A2C5: 10 8E 03 00 LDY    #$0300
A2C9: 31 3F       LEAY   -$1,Y
A2CB: 27 4A       BEQ    $A317
A2CD: E6 84       LDB    ,X
A2CF: C5 01       BITB   #$01
A2D1: 27 F6       BEQ    $A2C9
A2D3: E6 03       LDB    $3,X
A2D5: 31 3F       LEAY   -$1,Y
A2D7: 27 3E       BEQ    $A317
A2D9: E6 84       LDB    ,X
A2DB: 2A F8       BPL    $A2D5
A2DD: E6 03       LDB    $3,X
A2DF: C1 5A       CMPB   #$5A
A2E1: 26 F2       BNE    $A2D5
A2E3: D7 4A       STB    $4A
A2E5: C6 08       LDB    #$08
A2E7: E7 84       STB    ,X
A2E9: E6 84       LDB    ,X
A2EB: 2A FC       BPL    $A2E9
A2ED: E6 03       LDB    $3,X
A2EF: E7 C0       STB    ,U+
A2F1: DB 4A       ADDB   $4A
A2F3: D7 4A       STB    $4A
A2F5: 4A          DECA
A2F6: 26 F1       BNE    $A2E9
A2F8: E6 84       LDB    ,X
A2FA: 2A FC       BPL    $A2F8
A2FC: E6 03       LDB    $3,X
A2FE: 35 03       PULS   CC,A
A300: 6F 84       CLR    ,X
A302: D1 4A       CMPB   $4A
A304: 27 10       BEQ    $A316
A306: 4A          DECA
A307: 26 9D       BNE    $A2A6
A309: 86 08       LDA    #$08
A30B: 97 4E       STA    $4E
A30D: 6F 84       CLR    ,X
A30F: 43          COMA
A310: 39          RTS
A311: 35 01       PULS   CC
A313: 43          COMA
A314: 35 02       PULS   A
A316: 39          RTS
A317: 35 03       PULS   CC,A
A319: 86 02       LDA    #$02
A31B: 20 EE       BRA    $A30B
A31D: 96 4C       LDA    $4C
A31F: 27 19       BEQ    $A33A
A321: 81 10       CMPA   #$10
A323: 22 15       BHI    $A33A
A325: C6 04       LDB    #$04
A327: 3D          MUL
A328: DD 4C       STD    $4C
A32A: 96 4B       LDA    $4B
A32C: 81 02       CMPA   #$02
A32E: 23 19       BLS    $A349
A330: C6 40       LDB    #$40
A332: 81 14       CMPA   #$14
A334: 25 09       BCS    $A33F
A336: 81 18       CMPA   #$18
A338: 23 4D       BLS    $A387
A33A: 86 40       LDA    #$40
A33C: 16 FF CC    LBRA   $A30B
A33F: 81 08       CMPA   #$08
A341: 23 5F       BLS    $A3A2
A343: 81 0E       CMPA   #$0E
A345: 23 52       BLS    $A399
A347: 20 47       BRA    $A390
A349: 81 00       CMPA   #$00
A34B: 27 12       BEQ    $A35F
A34D: 81 01       CMPA   #$01
A34F: 27 07       BEQ    $A358
A351: DC 4C       LDD    $4C
A353: 83 00 02    SUBD   #$0002
A356: 20 50       BRA    $A3A8
A358: DC 4C       LDD    $4C
A35A: C3 01 3D    ADDD   #$013D
A35D: 20 49       BRA    $A3A8
A35F: DC 4C       LDD    $4C
A361: 10 83 00 10 CMPD   #$0010
A365: 23 11       BLS    $A378
A367: 10 83 00 20 CMPD   #$0020
A36B: 23 10       BLS    $A37D
A36D: 10 83 00 30 CMPD   #$0030
A371: 23 0F       BLS    $A382
A373: C3 01 50    ADDD   #$0150
A376: 20 30       BRA    $A3A8
A378: C3 01 7D    ADDD   #$017D
A37B: 20 2B       BRA    $A3A8
A37D: C3 01 6F    ADDD   #$016F
A380: 20 26       BRA    $A3A8
A382: C3 01 5E    ADDD   #$015E
A385: 20 21       BRA    $A3A8
A387: 80 14       SUBA   #$14
A389: 8D 23       BSR    $A3AE
A38B: 83 00 03    SUBD   #$0003
A38E: 20 16       BRA    $A3A6
A390: 86 14       LDA    #$14
A392: 8D 18       BSR    $A3AC
A394: 83 00 02    SUBD   #$0002
A397: 20 0D       BRA    $A3A6
A399: 86 0E       LDA    #$0E
A39B: 8D 0F       BSR    $A3AC
A39D: 83 00 01    SUBD   #$0001
A3A0: 20 04       BRA    $A3A6
A3A2: 86 08       LDA    #$08
A3A4: 8D 06       BSR    $A3AC
A3A6: D3 4A       ADDD   $4A
A3A8: DD 4C       STD    $4C
A3AA: 4F          CLRA
A3AB: 39          RTS
A3AC: 90 4B       SUBA   $4B
A3AE: 3D          MUL
A3AF: DD 4A       STD    $4A
A3B1: DC 4C       LDD    $4C
A3B3: 39          RTS
A3B4: 34 7F       PSHS   U,Y,X,DP,D,CC
A3B6: 17 FD 5F    LBSR   $A118
A3B9: 17 FD 75    LBSR   $A131
A3BC: 25 22       BCS    $A3E0
A3BE: 17 FE 1A    LBSR   $A1DB
A3C1: 25 1D       BCS    $A3E0
A3C3: 8D 25       BSR    $A3EA
A3C5: 86 02       LDA    #$02
A3C7: 34 02       PSHS   A
A3C9: 8D 3E       BSR    $A409
A3CB: 25 13       BCS    $A3E0
A3CD: 17 00 42    LBSR   $A412
A3D0: 17 00 D1    LBSR   $A4A4
A3D3: 35 02       PULS   A
A3D5: 24 05       BCC    $A3DC
A3D7: 4A          DECA
A3D8: 26 ED       BNE    $A3C7
A3DA: 20 04       BRA    $A3E0
A3DC: 86 19       LDA    #$19
A3DE: 97 4B       STA    $4B
A3E0: 17 FD 6B    LBSR   $A14E
A3E3: 35 02       PULS   A
A3E5: 1E 8A       EXG    A,CC
A3E7: 44          LSRA
A3E8: 35 FE       PULS   D,DP,X,Y,U,PC
A3EA: DE 4F       LDU    $4F
A3EC: CC 28 FF    LDD    #$28FF
A3EF: 8D 12       BSR    $A403
A3F1: CC 02 FE    LDD    #$02FE
A3F4: 8D 0D       BSR    $A403
A3F6: CC 08 FF    LDD    #$08FF
A3F9: 8D 08       BSR    $A403
A3FB: CC 4D FE    LDD    #$4DFE
A3FE: 8D 03       BSR    $A403
A400: CC 01 8C    LDD    #$018C
A403: E7 C0       STB    ,U+
A405: 4A          DECA
A406: 26 FB       BNE    $A403
A408: 39          RTS
A409: A6 01       LDA    $1,X
A40B: 85 02       BITA   #$02
A40D: 26 FA       BNE    $A409
A40F: 16 FE 61    LBRA   $A273
A412: 34 01       PSHS   CC
A414: 1A 50       ORCC   #$50
A416: DE 4F       LDU    $4F
A418: E6 03       LDB    $3,X
A41A: E6 84       LDB    ,X
A41C: 2A FA       BPL    $A418
A41E: E6 84       LDB    ,X
A420: 2A FC       BPL    $A41E
A422: C6 04       LDB    #$04
A424: E7 84       STB    ,X
A426: 10 8E 0A EC LDY    #$0AEC
A42A: 86 16       LDA    #$16
A42C: 8D 5E       BSR    $A48C
A42E: 10 8E 00 00 LDY    #$0000
A432: 31 21       LEAY   $1,Y
A434: 10 9F 4C    STY    $4C
A437: 86 A5       LDA    #$A5
A439: 8D 4D       BSR    $A488
A43B: 96 4C       LDA    $4C
A43D: 8D 49       BSR    $A488
A43F: 96 4D       LDA    $4D
A441: 8D 45       BSR    $A488
A443: 9B 4C       ADDA   $4C
A445: 8B A5       ADDA   #$A5
A447: 8D 3F       BSR    $A488
A449: 10 8E 00 07 LDY    #$0007
A44D: 86 16       LDA    #$16
A44F: 8D 3B       BSR    $A48C
A451: 86 5A       LDA    #$5A
A453: 8D 33       BSR    $A488
A455: 10 8E 00 05 LDY    #$0005
A459: 10 9C 4C    CMPY   $4C
A45C: 27 39       BEQ    $A497
A45E: 10 8E 00 80 LDY    #$0080
A462: 86 FF       LDA    #$FF
A464: 8D 26       BSR    $A48C
A466: 86 DA       LDA    #$DA
A468: 8D 1E       BSR    $A488
A46A: 10 8E 00 14 LDY    #$0014
A46E: 86 16       LDA    #$16
A470: 8D 1A       BSR    $A48C
A472: 10 9E 4C    LDY    $4C
A475: 10 8C 01 90 CMPY   #$0190
A479: 26 B7       BNE    $A432
A47B: 8D 0B       BSR    $A488
A47D: E6 01       LDB    $1,X
A47F: C5 02       BITB   #$02
A481: 26 F8       BNE    $A47B
A483: 6F 84       CLR    ,X
A485: 35 01       PULS   CC
A487: 39          RTS
A488: 10 8E 00 01 LDY    #$0001
A48C: E6 84       LDB    ,X
A48E: 2A FC       BPL    $A48C
A490: A7 03       STA    $3,X
A492: 31 3F       LEAY   -$1,Y
A494: 26 F6       BNE    $A48C
A496: 39          RTS
A497: DE 4F       LDU    $4F
A499: 4F          CLRA
A49A: 8D EC       BSR    $A488
A49C: 81 8C       CMPA   #$8C
A49E: 27 CA       BEQ    $A46A
A4A0: A6 C0       LDA    ,U+
A4A2: 20 F6       BRA    $A49A
A4A4: 10 8E 00 00 LDY    #$0000
A4A8: 31 21       LEAY   $1,Y
A4AA: 10 9F 4C    STY    $4C
A4AD: DE 4F       LDU    $4F
A4AF: 17 FD B5    LBSR   $A267
A4B2: 25 69       BCS    $A51D
A4B4: 34 01       PSHS   CC
A4B6: 17 FD 2F    LBSR   $A1E8
A4B9: 25 63       BCS    $A51E
A4BB: CC 5A 80    LDD    #$5A80
A4BE: ED 03       STD    $3,X
A4C0: 86 80       LDA    #$80
A4C2: C6 18       LDB    #$18
A4C4: E7 84       STB    ,X
A4C6: E6 84       LDB    ,X
A4C8: C5 01       BITB   #$01
A4CA: 27 FA       BEQ    $A4C6
A4CC: E6 03       LDB    $3,X
A4CE: C6 FF       LDB    #$FF
A4D0: E7 04       STB    $4,X
A4D2: C6 08       LDB    #$08
A4D4: E7 84       STB    ,X
A4D6: 10 9E 4C    LDY    $4C
A4D9: 10 8C 00 05 CMPY   #$0005
A4DD: 27 1E       BEQ    $A4FD
A4DF: E6 84       LDB    ,X
A4E1: 2A FC       BPL    $A4DF
A4E3: E6 03       LDB    $3,X
A4E5: C1 FF       CMPB   #$FF
A4E7: 26 0F       BNE    $A4F8
A4E9: 4A          DECA
A4EA: 26 F3       BNE    $A4DF
A4EC: E6 84       LDB    ,X
A4EE: 2A FC       BPL    $A4EC
A4F0: E6 03       LDB    $3,X
A4F2: 6F 84       CLR    ,X
A4F4: C1 DA       CMPB   #$DA
A4F6: 27 1A       BEQ    $A512
A4F8: 86 20       LDA    #$20
A4FA: 16 FE 0E    LBRA   $A30B
A4FD: E6 84       LDB    ,X
A4FF: 2A FC       BPL    $A4FD
A501: E6 03       LDB    $3,X
A503: 26 F3       BNE    $A4F8
A505: E6 84       LDB    ,X
A507: 2A FC       BPL    $A505
A509: E6 03       LDB    $3,X
A50B: E1 C0       CMPB   ,U+
A50D: 26 E9       BNE    $A4F8
A50F: 4A          DECA
A510: 26 F3       BNE    $A505
A512: 35 01       PULS   CC
A514: 10 9E 4C    LDY    $4C
A517: 10 8C 01 90 CMPY   #$0190
A51B: 26 8B       BNE    $A4A8
A51D: 39          RTS
A51E: 35 01       PULS   CC
A520: 43          COMA
A521: 39          RTS
A522: 53          COMB
A523: 43          COMA
A524: 52          XNCB
A525: 41          NEGA
A526: 54          LSRB
A527: 43          COMA
A528: 48          ASLA
A529: 20 44       BRA    $A56F
A52B: 4F          CLRA
A52C: 53          COMB
A52D: D6 F0       LDB    $F0
A52F: C1 02       CMPB   #$02
A531: 27 23       BEQ    $A556
A533: 0A F0       DEC    $F0
A535: 8D 60       BSR    $A597
A537: 25 30       BCS    $A569
A539: 5D          TSTB
A53A: 27 05       BEQ    $A541
A53C: 17 01 55    LBSR   $A694
A53F: 25 28       BCS    $A569
A541: 0C F0       INC    $F0
A543: 8D 52       BSR    $A597
A545: 25 22       BCS    $A569
A547: C6 0A       LDB    #$0A
A549: 9E E7       LDX    $E7
A54B: A6 85       LDA    B,X
A54D: A7 A5       STA    B,Y
A54F: 5A          DECB
A550: 2C F9       BGE    $A54B
A552: 8D 36       BSR    $A58A
A554: 25 13       BCS    $A569
A556: 86 02       LDA    #$02
A558: 97 4C       STA    $4C
A55A: C6 14       LDB    #$14
A55C: 4F          CLRA
A55D: DD 4A       STD    $4A
A55F: DC ED       LDD    $ED
A561: DD 4F       STD    $4F
A563: 8D 25       BSR    $A58A
A565: 25 02       BCS    $A569
A567: 0F F0       CLR    $F0
A569: 39          RTS
A56A: 9E ED       LDX    $ED
A56C: 9F 4F       STX    $4F
A56E: 86 02       LDA    #$02
A570: 20 0D       BRA    $A57F
A572: 97 E5       STA    $E5
A574: 43          COMA
A575: 43          COMA
A576: 39          RTS
A577: 4F          CLRA
A578: 39          RTS
A579: 86 03       LDA    #$03
A57B: 9E E9       LDX    $E9
A57D: 9F 4F       STX    $4F
A57F: 97 4C       STA    $4C
A581: C6 14       LDB    #$14
A583: 4F          CLRA
A584: DD 4A       STD    $4A
A586: 86 02       LDA    #$02
A588: 20 02       BRA    $A58C
A58A: 86 08       LDA    #$08
A58C: 97 48       STA    $48
A58E: 10 9E E9    LDY    $E9
A591: 17 FA 70    LBSR   $A004
A594: 86 03       LDA    #$03
A596: 39          RTS
A597: 8D E0       BSR    $A579
A599: 25 D7       BCS    $A572
A59B: 8E 00 04    LDX    #$0004
A59E: 10 9E E9    LDY    $E9
A5A1: DE E7       LDU    $E7
A5A3: D6 F0       LDB    $F0
A5A5: C1 03       CMPB   #$03
A5A7: 26 04       BNE    $A5AD
A5A9: 33 8D FF 75 LEAU   $A522,PCR
A5AD: 5F          CLRB
A5AE: C1 0B       CMPB   #$0B
A5B0: 24 24       BCC    $A5D6
A5B2: A6 A5       LDA    B,Y
A5B4: 81 FF       CMPA   #$FF
A5B6: 27 1B       BEQ    $A5D3
A5B8: 5C          INCB
A5B9: A1 C0       CMPA   ,U+
A5BB: 27 F1       BEQ    $A5AE
A5BD: 31 A8 20    LEAY   $20,Y
A5C0: 30 1F       LEAX   -$1,X
A5C2: 26 DD       BNE    $A5A1
A5C4: 0C 4C       INC    $4C
A5C6: 96 4C       LDA    $4C
A5C8: 81 10       CMPA   #$10
A5CA: 22 07       BHI    $A5D3
A5CC: 17 FA 35    LBSR   $A004
A5CF: 86 03       LDA    #$03
A5D1: 20 C6       BRA    $A599
A5D3: 5F          CLRB
A5D4: 20 1B       BRA    $A5F1
A5D6: E6 2B       LDB    $B,Y
A5D8: D1 EB       CMPB   $EB
A5DA: 26 E1       BNE    $A5BD
A5DC: E6 2C       LDB    $C,Y
A5DE: D1 EC       CMPB   $EC
A5E0: 26 DB       BNE    $A5BD
A5E2: D6 4C       LDB    $4C
A5E4: A6 2D       LDA    $D,Y
A5E6: 97 F6       STA    $F6
A5E8: 0F F5       CLR    $F5
A5EA: AE 2E       LDX    $E,Y
A5EC: 9F F7       STX    $F7
A5EE: 10 9F FA    STY    $FA
A5F1: D7 F9       STB    $F9
A5F3: 16 FF 81    LBRA   $A577
A5F6: 10 9E ED    LDY    $ED
A5F9: 8D 6F       BSR    $A66A
A5FB: 25 9C       BCS    $A599
A5FD: D7 F6       STB    $F6
A5FF: 17 FF 77    LBSR   $A579
A602: 25 F7       BCS    $A5FB
A604: 10 9E E9    LDY    $E9
A607: 8E 00 04    LDX    #$0004
A60A: E6 A4       LDB    ,Y
A60C: 27 20       BEQ    $A62E
A60E: 86 05       LDA    #$05
A610: C1 FF       CMPB   #$FF
A612: 27 1A       BEQ    $A62E
A614: 31 A8 20    LEAY   $20,Y
A617: 30 1F       LEAX   -$1,X
A619: 26 EF       BNE    $A60A
A61B: 0C 4C       INC    $4C
A61D: 96 4C       LDA    $4C
A61F: 81 10       CMPA   #$10
A621: 22 07       BHI    $A62A
A623: 17 F9 DE    LBSR   $A004
A626: 86 03       LDA    #$03
A628: 20 D8       BRA    $A602
A62A: 86 05       LDA    #$05
A62C: 20 CD       BRA    $A5FB
A62E: 9E E7       LDX    $E7
A630: D6 F0       LDB    $F0
A632: C1 03       CMPB   #$03
A634: 26 04       BNE    $A63A
A636: 30 8D FE E8 LEAX   $A522,PCR
A63A: C6 0A       LDB    #$0A
A63C: A6 85       LDA    B,X
A63E: A7 A5       STA    B,Y
A640: 5A          DECB
A641: 2C F9       BGE    $A63C
A643: 96 EB       LDA    $EB
A645: A7 2B       STA    $B,Y
A647: 96 EC       LDA    $EC
A649: D6 F6       LDB    $F6
A64B: ED 2C       STD    $C,Y
A64D: 16 FF 3A    LBRA   $A58A
A650: D6 F6       LDB    $F6
A652: C1 28       CMPB   #$28
A654: 22 0E       BHI    $A664
A656: 5D          TSTB
A657: 27 11       BEQ    $A66A
A659: A6 A5       LDA    B,Y
A65B: 81 FF       CMPA   #$FF
A65D: 27 2D       BEQ    $A68C
A65F: 5A          DECB
A660: C1 28       CMPB   #$28
A662: 23 F2       BLS    $A656
A664: CB 02       ADDB   #$02
A666: C1 51       CMPB   #$51
A668: 20 ED       BRA    $A657
A66A: 5F          CLRB
A66B: 31 A8 28    LEAY   $28,Y
A66E: 86 05       LDA    #$05
A670: C1 28       CMPB   #$28
A672: 10 22 FE FC LBHI   $A572
A676: A6 A5       LDA    B,Y
A678: 81 FF       CMPA   #$FF
A67A: 27 0B       BEQ    $A687
A67C: 50          NEGB
A67D: A6 A5       LDA    B,Y
A67F: 81 FF       CMPA   #$FF
A681: 27 04       BEQ    $A687
A683: 50          NEGB
A684: 5C          INCB
A685: 20 E7       BRA    $A66E
A687: CB 28       ADDB   #$28
A689: 31 A8 D8    LEAY   -$28,Y
A68C: 6F A5       CLR    B,Y
A68E: 5A          DECB
A68F: D7 F9       STB    $F9
A691: 16 FE E3    LBRA   $A577
A694: A6 2D       LDA    $D,Y
A696: 97 F6       STA    $F6
A698: 6F A4       CLR    ,Y
A69A: 17 FE ED    LBSR   $A58A
A69D: 25 8D       BCS    $A62C
A69F: 10 9E ED    LDY    $ED
A6A2: D6 F6       LDB    $F6
A6A4: 5C          INCB
A6A5: A6 A5       LDA    B,Y
A6A7: 6F A5       CLR    B,Y
A6A9: 6A A5       DEC    B,Y
A6AB: 1F 89       TFR    A,B
A6AD: 81 C0       CMPA   #$C0
A6AF: 25 F3       BCS    $A6A4
A6B1: 20 DE       BRA    $A691
A6B3: D6 F6       LDB    $F6
A6B5: 4F          CLRA
A6B6: 54          LSRB
A6B7: DD FB       STD    $FB
A6B9: 4C          INCA
A6BA: 97 F5       STA    $F5
A6BC: 24 02       BCC    $A6C0
A6BE: 86 09       LDA    #$09
A6C0: 97 FA       STA    $FA
A6C2: 39          RTS
A6C3: FF FF FF    STU    $FFFF
A6C6: FF FF FF    STU    $FFFF
A6C9: FF FF FF    STU    $FFFF
A6CC: FF FF FF    STU    $FFFF
A6CF: FF FF FF    STU    $FFFF
A6D2: FF FF FF    STU    $FFFF
A6D5: FF FF FF    STU    $FFFF
A6D8: FF FF FF    STU    $FFFF
A6DB: FF FF FF    STU    $FFFF
A6DE: FF FF FF    STU    $FFFF
A6E1: FF FF FF    STU    $FFFF
A6E4: FF FF FF    STU    $FFFF
A6E7: FF FF FF    STU    $FFFF
A6EA: FF FF FF    STU    $FFFF
A6ED: FF FF FF    STU    $FFFF
A6F0: FF FF FF    STU    $FFFF
A6F3: FF FF FF    STU    $FFFF
A6F6: FF FF FF    STU    $FFFF
A6F9: FF FF FF    STU    $FFFF
A6FC: FF FF FF    STU    $FFFF
A6FF: FF FF FF    STU    $FFFF
A702: FF FF FF    STU    $FFFF
A705: FF FF FF    STU    $FFFF
A708: FF FF FF    STU    $FFFF
A70B: FF FF FF    STU    $FFFF
A70E: FF FF FF    STU    $FFFF
A711: FF FF FF    STU    $FFFF
A714: FF FF FF    STU    $FFFF
A717: FF FF FF    STU    $FFFF
A71A: FF FF FF    STU    $FFFF
A71D: FF FF FF    STU    $FFFF
A720: FF FF FF    STU    $FFFF
A723: FF FF FF    STU    $FFFF
A726: FF FF FF    STU    $FFFF
A729: FF FF FF    STU    $FFFF
A72C: FF FF FF    STU    $FFFF
A72F: FF FF FF    STU    $FFFF
A732: FF FF FF    STU    $FFFF
A735: FF FF FF    STU    $FFFF
A738: FF FF FF    STU    $FFFF
A73B: FF FF FF    STU    $FFFF
A73E: FF FF FF    STU    $FFFF
A741: FF FF FF    STU    $FFFF
A744: FF FF FF    STU    $FFFF
A747: FF FF FF    STU    $FFFF
A74A: FF FF FF    STU    $FFFF
A74D: FF FF FF    STU    $FFFF
A750: FF FF FF    STU    $FFFF
A753: FF FF FF    STU    $FFFF
A756: FF FF FF    STU    $FFFF
A759: FF FF FF    STU    $FFFF
A75C: FF FF FF    STU    $FFFF
A75F: FF FF FF    STU    $FFFF
A762: FF FF FF    STU    $FFFF
A765: FF FF FF    STU    $FFFF
A768: FF FF FF    STU    $FFFF
A76B: FF FF FF    STU    $FFFF
A76E: FF FF FF    STU    $FFFF
A771: FF FF FF    STU    $FFFF
A774: FF FF FF    STU    $FFFF
A777: FF FF FF    STU    $FFFF
A77A: FF FF FF    STU    $FFFF
A77D: FF FF FF    STU    $FFFF
A780: FF FF FF    STU    $FFFF
A783: FF FF FF    STU    $FFFF
A786: FF FF FF    STU    $FFFF
A789: FF FF FF    STU    $FFFF
A78C: FF FF FF    STU    $FFFF
A78F: FF FF FF    STU    $FFFF
A792: FF FF FF    STU    $FFFF
A795: FF FF FF    STU    $FFFF
A798: FF FF FF    STU    $FFFF
A79B: FF FF FF    STU    $FFFF
A79E: FF FF FF    STU    $FFFF
A7A1: FF FF FF    STU    $FFFF
A7A4: FF FF FF    STU    $FFFF
A7A7: FF FF FF    STU    $FFFF
A7AA: FF FF FF    STU    $FFFF
A7AD: FF FF FF    STU    $FFFF
A7B0: FF FF FF    STU    $FFFF
A7B3: FF FF FF    STU    $FFFF
A7B6: FF FF FF    STU    $FFFF
A7B9: FF FF FF    STU    $FFFF
A7BC: FF FF FF    STU    $FFFF
A7BF: FF 38 80    STU    $3880
