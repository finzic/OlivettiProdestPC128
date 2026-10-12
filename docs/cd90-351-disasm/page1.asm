A000: 4D          TSTA
A001: 54          LSRB
A002: 44          LSRA
A003: 3A          ABX
A004: 16 00 24    LBRA   $A02B
A007: 16 00 2C    LBRA   $A036
A00A: 16 00 A2    LBRA   $A0AF
A00D: 16 00 3C    LBRA   $A04C
A010: 16 00 43    LBRA   $A056
A013: 16 00 4A    LBRA   $A060
A016: 16 00 51    LBRA   $A06A
A019: 16 00 58    LBRA   $A074
A01C: 16 00 5F    LBRA   $A07E
A01F: 16 00 66    LBRA   $A088
A022: 16 00 6D    LBRA   $A092
A025: 16 FF FD    LBRA   $A025
A028: 16 FF FD    LBRA   $A028
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
A0A4: AD C4       JSR    ,U
A0A6: 1F 03       TFR    D,U
A0A8: 35 04       PULS   B
A0AA: E7 8D 07 2A STB    $A7D8,PCR
A0AE: 39          RTS
A0AF: 34 7F       PSHS   U,Y,X,DP,D,CC
A0B1: 8D 50       BSR    $A103
A0B3: 8D 61       BSR    $A116
A0B5: 17 00 A3    LBSR   $A15B
A0B8: 25 42       BCS    $A0FC
A0BA: 17 00 C7    LBSR   $A184
A0BD: 25 3B       BCS    $A0FA
A0BF: 17 00 B6    LBSR   $A178
A0C2: 25 36       BCS    $A0FA
A0C4: 34 01       PSHS   CC
A0C6: 1A 50       ORCC   #$50
A0C8: 17 01 02    LBSR   $A1CD
A0CB: 86 02       LDA    #$02
A0CD: 34 02       PSHS   A
A0CF: 17 01 2D    LBSR   $A1FF
A0D2: 17 01 57    LBSR   $A22C
A0D5: 24 0B       BCC    $A0E2
A0D7: 6A E4       DEC    ,S
A0D9: 26 F4       BNE    $A0CF
A0DB: 35 02       PULS   A
A0DD: 35 01       PULS   CC
A0DF: 43          COMA
A0E0: 20 18       BRA    $A0FA
A0E2: 35 02       PULS   A
A0E4: 35 01       PULS   CC
A0E6: 96 4B       LDA    $4B
A0E8: 81 4F       CMPA   #$4F
A0EA: 27 05       BEQ    $A0F1
A0EC: 17 03 44    LBSR   $A433
A0EF: 20 D3       BRA    $A0C4
A0F1: 17 03 56    LBSR   $A44A
A0F4: 25 04       BCS    $A0FA
A0F6: 86 50       LDA    #$50
A0F8: 97 4B       STA    $4B
A0FA: 8D 77       BSR    $A173
A0FC: 35 02       PULS   A
A0FE: 1E 8A       EXG    A,CC
A100: 44          LSRA
A101: 35 FE       PULS   D,DP,X,Y,U,PC
A103: 1F 50       TFR    PC,D
A105: 84 70       ANDA   #$70
A107: 1F 8B       TFR    A,DP
A109: 96 48       LDA    $48
A10B: 84 80       ANDA   #$80
A10D: 97 48       STA    $48
A10F: 30 8D 06 BD LEAX   $A7D0,PCR
A113: 0F 4E       CLR    $4E
A115: 39          RTS
A116: 34 10       PSHS   X
A118: CE E9 41    LDU    #$E941
A11B: 8E 00 03    LDX    #$0003
A11E: C6 04       LDB    #$04
A120: A6 84       LDA    ,X
A122: A1 C4       CMPA   ,U
A124: 27 09       BEQ    $A12F
A126: 5C          INCB
A127: 33 C5       LEAU   B,U
A129: A6 C4       LDA    ,U
A12B: 26 EE       BNE    $A11B
A12D: 20 10       BRA    $A13F
A12F: 30 1F       LEAX   -$1,X
A131: 26 03       BNE    $A136
A133: 8E 00 1A    LDX    #$001A
A136: 33 41       LEAU   $1,U
A138: 5A          DECB
A139: 26 E5       BNE    $A120
A13B: A6 C4       LDA    ,U
A13D: 97 58       STA    $58
A13F: 35 90       PULS   X,PC
A141: 52          XNCB
A142: 45          LSRA
A143: 47          ASRA
A144: 6E FF 43 49 JMP    [$4349]
A148: 50          NEGB
A149: 4A          DECA
A14A: FF 4C 45    STU    $4C45
A14D: 4D          TSTA
A14E: 74 FF 4C    LSR    $FF4C
A151: 4F          CLRA
A152: 50          NEGB
A153: B5 00 53    BITA   >$0053
A156: 45          LSRA
A157: 47          ASRA
A158: B6 00 00    LDA    >$0000
A15B: 33 8D 00 10 LEAU   $A16F,PCR
A15F: D6 49       LDB    $49
A161: C1 04       CMPB   #$04
A163: 10 24 00 5F LBCC   $A1C6
A167: A6 C5       LDA    B,U
A169: A7 02       STA    $2,X
A16B: 97 57       STA    $57
A16D: 4F          CLRA
A16E: 39          RTS
A16F: 41          NEGA
A170: 01 42       NEG    $42
A172: 02 86       XNC    $86
A174: 40          NEGA
A175: A7 02       STA    $2,X
A177: 39          RTS
A178: A6 01       LDA    $1,X
A17A: 85 04       BITA   #$04
A17C: 26 02       BNE    $A180
A17E: 4F          CLRA
A17F: 39          RTS
A180: 86 01       LDA    #$01
A182: 20 44       BRA    $A1C8
A184: 8D 26       BSR    $A1AC
A186: 25 23       BCS    $A1AB
A188: C6 64       LDB    #$64
A18A: A6 01       LDA    $1,X
A18C: 85 08       BITA   #$08
A18E: 26 14       BNE    $A1A4
A190: 96 57       LDA    $57
A192: 8A 14       ORA    #$14
A194: A7 02       STA    $2,X
A196: 84 EB       ANDA   #$EB
A198: A7 02       STA    $2,X
A19A: 17 03 02    LBSR   $A49F
A19D: 5A          DECB
A19E: 10 27 00 24 LBEQ   $A1C6
A1A2: 20 E6       BRA    $A18A
A1A4: 17 02 F2    LBSR   $A499
A1A7: 0F 4B       CLR    $4B
A1A9: 6F 06       CLR    $6,X
A1AB: 39          RTS
A1AC: 10 8E 80 00 LDY    #$8000
A1B0: D6 57       LDB    $57
A1B2: CA 04       ORB    #$04
A1B4: E7 02       STB    $2,X
A1B6: C4 FB       ANDB   #$FB
A1B8: E7 02       STB    $2,X
A1BA: 31 3F       LEAY   -$1,Y
A1BC: 27 08       BEQ    $A1C6
A1BE: E6 01       LDB    $1,X
A1C0: C4 02       ANDB   #$02
A1C2: 27 EC       BEQ    $A1B0
A1C4: 4F          CLRA
A1C5: 39          RTS
A1C6: 86 10       LDA    #$10
A1C8: 34 01       PSHS   CC
A1CA: 16 04 16    LBRA   $A5E3
A1CD: 30 8D 7F 02 LEAX   $120D3,PCR
A1D1: C6 10       LDB    #$10
A1D3: 6F 85       CLR    B,X
A1D5: 5A          DECB
A1D6: 26 FB       BNE    $A1D3
A1D8: 30 88 10    LEAX   $10,X
A1DB: 34 10       PSHS   X
A1DD: 30 8D 7E F2 LEAX   $120D3,PCR
A1E1: 86 01       LDA    #$01
A1E3: D6 4D       LDB    $4D
A1E5: A7 84       STA    ,X
A1E7: 30 85       LEAX   B,X
A1E9: 4C          INCA
A1EA: 81 10       CMPA   #$10
A1EC: 22 0E       BHI    $A1FC
A1EE: AC E4       CMPX   ,S
A1F0: 25 02       BCS    $A1F4
A1F2: 30 10       LEAX   -$10,X
A1F4: 6D 84       TST    ,X
A1F6: 27 ED       BEQ    $A1E5
A1F8: 30 01       LEAX   $1,X
A1FA: 20 F2       BRA    $A1EE
A1FC: 32 62       LEAS   $2,S
A1FE: 39          RTS
A1FF: 30 8D 7E D0 LEAX   $120D3,PCR
A203: DE 4F       LDU    $4F
A205: E6 80       LDB    ,X+
A207: 27 1D       BEQ    $A226
A209: 96 4B       LDA    $4B
A20B: A7 C4       STA    ,U
A20D: 6F 41       CLR    $1,U
A20F: E7 42       STB    $2,U
A211: 10 8E 00 04 LDY    #$0004
A215: 96 58       LDA    $58
A217: 4C          INCA
A218: A7 43       STA    $3,U
A21A: 27 0B       BEQ    $A227
A21C: CC B2 30    LDD    #$B230
A21F: 17 03 90    LBSR   $A5B2
A222: ED C1       STD    ,U++
A224: 20 DF       BRA    $A205
A226: 39          RTS
A227: CC EF 21    LDD    #$EF21
A22A: 20 F3       BRA    $A21F
A22C: 86 10       LDA    #$10
A22E: 34 02       PSHS   A
A230: DE 4F       LDU    $4F
A232: 30 8D 05 9A LEAX   $A7D0,PCR
A236: 96 58       LDA    $58
A238: 10 26 00 F6 LBNE   $A332
A23C: 17 01 D5    LBSR   $A414
A23F: E6 01       LDB    $1,X
A241: C5 40       BITB   #$40
A243: 27 FA       BEQ    $A23F
A245: E6 03       LDB    $3,X
A247: E6 84       LDB    ,X
A249: 2A FA       BPL    $A245
A24B: E6 84       LDB    ,X
A24D: 2A FC       BPL    $A24B
A24F: CC 4E FF    LDD    #$4EFF
A252: ED 03       STD    $3,X
A254: C6 04       LDB    #$04
A256: E7 84       STB    ,X
A258: 86 1E       LDA    #$1E
A25A: E6 84       LDB    ,X
A25C: 2A FC       BPL    $A25A
A25E: C6 4E       LDB    #$4E
A260: E7 03       STB    $3,X
A262: 4A          DECA
A263: 26 F5       BNE    $A25A
A265: 86 0C       LDA    #$0C
A267: E6 84       LDB    ,X
A269: 2A FC       BPL    $A267
A26B: 6F 03       CLR    $3,X
A26D: 4A          DECA
A26E: 26 F7       BNE    $A267
A270: E6 84       LDB    ,X
A272: 2A FC       BPL    $A270
A274: CC A1 0A    LDD    #$A10A
A277: ED 03       STD    $3,X
A279: E6 84       LDB    ,X
A27B: 2A FC       BPL    $A279
A27D: A7 03       STA    $3,X
A27F: E6 84       LDB    ,X
A281: 2A FC       BPL    $A27F
A283: A7 03       STA    $3,X
A285: E6 84       LDB    ,X
A287: 2A FC       BPL    $A285
A289: CC FE FF    LDD    #$FEFF
A28C: ED 03       STD    $3,X
A28E: 86 06       LDA    #$06
A290: E6 84       LDB    ,X
A292: 2A FC       BPL    $A290
A294: E6 C0       LDB    ,U+
A296: E7 03       STB    $3,X
A298: 4A          DECA
A299: 26 F5       BNE    $A290
A29B: 86 16       LDA    #$16
A29D: E6 84       LDB    ,X
A29F: 2A FC       BPL    $A29D
A2A1: C6 4E       LDB    #$4E
A2A3: E7 03       STB    $3,X
A2A5: 4A          DECA
A2A6: 26 F5       BNE    $A29D
A2A8: 86 0C       LDA    #$0C
A2AA: E6 84       LDB    ,X
A2AC: 2A FC       BPL    $A2AA
A2AE: 6F 03       CLR    $3,X
A2B0: 4A          DECA
A2B1: 26 F7       BNE    $A2AA
A2B3: E6 84       LDB    ,X
A2B5: 2A FC       BPL    $A2B3
A2B7: CC A1 0A    LDD    #$A10A
A2BA: ED 03       STD    $3,X
A2BC: E6 84       LDB    ,X
A2BE: 2A FC       BPL    $A2BC
A2C0: A7 03       STA    $3,X
A2C2: E6 84       LDB    ,X
A2C4: 2A FC       BPL    $A2C2
A2C6: A7 03       STA    $3,X
A2C8: E6 84       LDB    ,X
A2CA: 2A FC       BPL    $A2C8
A2CC: CC FB FF    LDD    #$FBFF
A2CF: ED 03       STD    $3,X
A2D1: 4F          CLRA
A2D2: E6 84       LDB    ,X
A2D4: 2A FC       BPL    $A2D2
A2D6: C6 E5       LDB    #$E5
A2D8: E7 03       STB    $3,X
A2DA: 4A          DECA
A2DB: 26 F5       BNE    $A2D2
A2DD: E6 84       LDB    ,X
A2DF: 2A FC       BPL    $A2DD
A2E1: C6 78       LDB    #$78
A2E3: E7 03       STB    $3,X
A2E5: E6 84       LDB    ,X
A2E7: 2A FC       BPL    $A2E5
A2E9: C6 27       LDB    #$27
A2EB: E7 03       STB    $3,X
A2ED: 86 2C       LDA    #$2C
A2EF: E6 84       LDB    ,X
A2F1: 2A FC       BPL    $A2EF
A2F3: C6 4E       LDB    #$4E
A2F5: E7 03       STB    $3,X
A2F7: 4A          DECA
A2F8: 26 F5       BNE    $A2EF
A2FA: 6A E4       DEC    ,S
A2FC: 10 26 FF 65 LBNE   $A265
A300: A6 01       LDA    $1,X
A302: 85 40       BITA   #$40
A304: 26 08       BNE    $A30E
A306: A6 84       LDA    ,X
A308: 2A FC       BPL    $A306
A30A: E7 03       STB    $3,X
A30C: 20 F2       BRA    $A300
A30E: 35 02       PULS   A
A310: 6F 84       CLR    ,X
A312: 0D 48       TST    $48
A314: 2A 1B       BPL    $A331
A316: 86 E5       LDA    #$E5
A318: 17 01 0C    LBSR   $A427
A31B: 33 8D 7D B4 LEAU   $120D3,PCR
A31F: 17 FE 8A    LBSR   $A1AC
A322: A6 C0       LDA    ,U+
A324: 27 0B       BEQ    $A331
A326: 97 4C       STA    $4C
A328: 34 40       PSHS   U
A32A: 17 01 7B    LBSR   $A4A8
A32D: 35 40       PULS   U
A32F: 24 F1       BCC    $A322
A331: 39          RTS
A332: 17 02 6D    LBSR   $A5A2
A335: E6 01       LDB    $1,X
A337: C5 40       BITB   #$40
A339: 27 FA       BEQ    $A335
A33B: E6 03       LDB    $3,X
A33D: E6 84       LDB    ,X
A33F: 2A FA       BPL    $A33B
A341: E6 84       LDB    ,X
A343: 2A FC       BPL    $A341
A345: CC FF FF    LDD    #$FFFF
A348: ED 03       STD    $3,X
A34A: C6 24       LDB    #$24
A34C: E7 84       STB    ,X
A34E: 86 10       LDA    #$10
A350: E6 84       LDB    ,X
A352: 2A FC       BPL    $A350
A354: C6 FF       LDB    #$FF
A356: E7 03       STB    $3,X
A358: 4A          DECA
A359: 26 F5       BNE    $A350
A35B: 86 06       LDA    #$06
A35D: E6 84       LDB    ,X
A35F: 2A FC       BPL    $A35D
A361: 6F 03       CLR    $3,X
A363: 4A          DECA
A364: 26 F7       BNE    $A35D
A366: E6 84       LDB    ,X
A368: 2A FC       BPL    $A366
A36A: CC FE C7    LDD    #$FEC7
A36D: ED 03       STD    $3,X
A36F: E6 84       LDB    ,X
A371: 2A FC       BPL    $A36F
A373: C6 FF       LDB    #$FF
A375: A6 C0       LDA    ,U+
A377: ED 03       STD    $3,X
A379: 86 05       LDA    #$05
A37B: E6 84       LDB    ,X
A37D: 2A FC       BPL    $A37B
A37F: E6 C0       LDB    ,U+
A381: E7 03       STB    $3,X
A383: 4A          DECA
A384: 26 F5       BNE    $A37B
A386: 86 0C       LDA    #$0C
A388: E6 84       LDB    ,X
A38A: 2A FC       BPL    $A388
A38C: C6 FF       LDB    #$FF
A38E: E7 03       STB    $3,X
A390: 4A          DECA
A391: 26 F5       BNE    $A388
A393: 86 06       LDA    #$06
A395: E6 84       LDB    ,X
A397: 2A FC       BPL    $A395
A399: 6F 03       CLR    $3,X
A39B: 4A          DECA
A39C: 26 F7       BNE    $A395
A39E: E6 84       LDB    ,X
A3A0: 2A FC       BPL    $A39E
A3A2: CC FB C7    LDD    #$FBC7
A3A5: ED 03       STD    $3,X
A3A7: E6 84       LDB    ,X
A3A9: 2A FC       BPL    $A3A7
A3AB: CC E5 FF    LDD    #$E5FF
A3AE: ED 03       STD    $3,X
A3B0: 86 7F       LDA    #$7F
A3B2: E6 84       LDB    ,X
A3B4: 2A FC       BPL    $A3B2
A3B6: C6 E5       LDB    #$E5
A3B8: E7 03       STB    $3,X
A3BA: 4A          DECA
A3BB: 26 F5       BNE    $A3B2
A3BD: E6 84       LDB    ,X
A3BF: 2A FC       BPL    $A3BD
A3C1: C6 5D       LDB    #$5D
A3C3: E7 03       STB    $3,X
A3C5: E6 84       LDB    ,X
A3C7: 2A FC       BPL    $A3C5
A3C9: C6 30       LDB    #$30
A3CB: E7 03       STB    $3,X
A3CD: 86 16       LDA    #$16
A3CF: E6 84       LDB    ,X
A3D1: 2A FC       BPL    $A3CF
A3D3: C6 FF       LDB    #$FF
A3D5: E7 03       STB    $3,X
A3D7: 4A          DECA
A3D8: 26 F5       BNE    $A3CF
A3DA: 6A E4       DEC    ,S
A3DC: 10 26 FF 7B LBNE   $A35B
A3E0: A6 01       LDA    $1,X
A3E2: 85 40       BITA   #$40
A3E4: 26 08       BNE    $A3EE
A3E6: A6 84       LDA    ,X
A3E8: 2A FC       BPL    $A3E6
A3EA: E7 03       STB    $3,X
A3EC: 20 F2       BRA    $A3E0
A3EE: 35 02       PULS   A
A3F0: 6F 84       CLR    ,X
A3F2: 0D 48       TST    $48
A3F4: 2A 1D       BPL    $A413
A3F6: 86 E5       LDA    #$E5
A3F8: 8D 2D       BSR    $A427
A3FA: 33 8D 7C D5 LEAU   $120D3,PCR
A3FE: 17 FD AB    LBSR   $A1AC
A401: A6 C0       LDA    ,U+
A403: 27 0E       BEQ    $A413
A405: 97 4C       STA    $4C
A407: 34 40       PSHS   U
A409: CC 5D 30    LDD    #$5D30
A40C: 17 00 E7    LBSR   $A4F6
A40F: 35 40       PULS   U
A411: 24 EE       BCC    $A401
A413: 39          RTS
A414: D6 4B       LDB    $4B
A416: C1 39       CMPB   #$39
A418: 2A 05       BPL    $A41F
A41A: CC 9F 20    LDD    #$9F20
A41D: 20 03       BRA    $A422
A41F: CC 1F 22    LDD    #$1F22
A422: A7 07       STA    $7,X
A424: E7 01       STB    $1,X
A426: 39          RTS
A427: DE 4F       LDU    $4F
A429: D6 58       LDB    $58
A42B: C4 80       ANDB   #$80
A42D: A7 C0       STA    ,U+
A42F: 5A          DECB
A430: 26 FB       BNE    $A42D
A432: 39          RTS
A433: 8D 6A       BSR    $A49F
A435: 96 57       LDA    $57
A437: 8A 20       ORA    #$20
A439: A7 02       STA    $2,X
A43B: 8A 14       ORA    #$14
A43D: A7 02       STA    $2,X
A43F: 84 EB       ANDA   #$EB
A441: A7 02       STA    $2,X
A443: 0C 4B       INC    $4B
A445: 96 4B       LDA    $4B
A447: A7 06       STA    $6,X
A449: 39          RTS
A44A: C6 3B       LDB    #$3B
A44C: 96 57       LDA    $57
A44E: 84 DF       ANDA   #$DF
A450: A7 02       STA    $2,X
A452: 8A 10       ORA    #$10
A454: A7 02       STA    $2,X
A456: 84 EF       ANDA   #$EF
A458: A7 02       STA    $2,X
A45A: 8D 43       BSR    $A49F
A45C: 5A          DECB
A45D: 26 F3       BNE    $A452
A45F: 17 01 95    LBSR   $A5F7
A462: 86 14       LDA    #$14
A464: A7 A4       STA    ,Y
A466: A7 06       STA    $6,X
A468: 97 4B       STA    $4B
A46A: 86 FF       LDA    #$FF
A46C: 8D B9       BSR    $A427
A46E: 86 10       LDA    #$10
A470: 97 4C       STA    $4C
A472: 17 FD 37    LBSR   $A1AC
A475: 17 01 8A    LBSR   $A602
A478: 25 18       BCS    $A492
A47A: 0A 4C       DEC    $4C
A47C: 26 F4       BNE    $A472
A47E: DE 4F       LDU    $4F
A480: 6F C4       CLR    ,U
A482: CC FE FE    LDD    #$FEFE
A485: ED C8 29    STD    $29,U
A488: 86 02       LDA    #$02
A48A: 97 4C       STA    $4C
A48C: 17 01 73    LBSR   $A602
A48F: 25 01       BCS    $A492
A491: 4F          CLRA
A492: 39          RTS
A493: 10 8E 00 6C LDY    #$006C
A497: 20 0A       BRA    $A4A3
A499: 10 8E 07 50 LDY    #$0750
A49D: 20 04       BRA    $A4A3
A49F: 10 8E 02 EC LDY    #$02EC
A4A3: 31 3F       LEAY   -$1,Y
A4A5: 26 FC       BNE    $A4A3
A4A7: 39          RTS
A4A8: C6 1B       LDB    #$1B
A4AA: 34 01       PSHS   CC
A4AC: 17 00 91    LBSR   $A540
A4AF: 86 04       LDA    #$04
A4B1: 10 8E 75 00 LDY    #$7500
A4B5: 31 3F       LEAY   -$1,Y
A4B7: 10 27 00 80 LBEQ   $A53B
A4BB: E6 84       LDB    ,X
A4BD: C5 02       BITB   #$02
A4BF: 27 F4       BEQ    $A4B5
A4C1: E6 03       LDB    $3,X
A4C3: 4A          DECA
A4C4: 10 27 01 2B LBEQ   $A5F3
A4C8: E6 84       LDB    ,X
A4CA: 2A FC       BPL    $A4C8
A4CC: E6 03       LDB    $3,X
A4CE: C1 FB       CMPB   #$FB
A4D0: 26 F1       BNE    $A4C3
A4D2: 4F          CLRA
A4D3: E6 84       LDB    ,X
A4D5: 2A FC       BPL    $A4D3
A4D7: E6 03       LDB    $3,X
A4D9: E1 C0       CMPB   ,U+
A4DB: 26 03       BNE    $A4E0
A4DD: 4A          DECA
A4DE: 26 F3       BNE    $A4D3
A4E0: E6 84       LDB    ,X
A4E2: C5 08       BITB   #$08
A4E4: 27 FA       BEQ    $A4E0
A4E6: 4D          TSTA
A4E7: 10 26 00 50 LBNE   $A53B
A4EB: C5 04       BITB   #$04
A4ED: 10 26 00 4A LBNE   $A53B
A4F1: 35 01       PULS   CC
A4F3: 6F 84       CLR    ,X
A4F5: 39          RTS
A4F6: 34 01       PSHS   CC
A4F8: 34 06       PSHS   D
A4FA: 8D 57       BSR    $A553
A4FC: 25 3B       BCS    $A539
A4FE: C6 FB       LDB    #$FB
A500: E7 03       STB    $3,X
A502: 86 80       LDA    #$80
A504: C6 38       LDB    #$38
A506: E7 84       STB    ,X
A508: E6 84       LDB    ,X
A50A: C5 01       BITB   #$01
A50C: 27 FA       BEQ    $A508
A50E: E6 03       LDB    $3,X
A510: C6 28       LDB    #$28
A512: E7 84       STB    ,X
A514: E6 84       LDB    ,X
A516: 2A FC       BPL    $A514
A518: E6 03       LDB    $3,X
A51A: E1 C0       CMPB   ,U+
A51C: 26 1B       BNE    $A539
A51E: 4A          DECA
A51F: 26 F3       BNE    $A514
A521: A6 84       LDA    ,X
A523: 2A FC       BPL    $A521
A525: A6 03       LDA    $3,X
A527: E6 84       LDB    ,X
A529: 2A FC       BPL    $A527
A52B: E6 03       LDB    $3,X
A52D: 10 A3 E4    CMPD   ,S
A530: 26 07       BNE    $A539
A532: 35 06       PULS   D
A534: 35 01       PULS   CC
A536: 6F 84       CLR    ,X
A538: 39          RTS
A539: 35 06       PULS   D
A53B: 86 20       LDA    #$20
A53D: 16 00 A3    LBRA   $A5E3
A540: 96 4C       LDA    $4C
A542: A7 05       STA    $5,X
A544: 86 0A       LDA    #$0A
A546: A7 04       STA    $4,X
A548: 86 A1       LDA    #$A1
A54A: A7 03       STA    $3,X
A54C: 1A 50       ORCC   #$50
A54E: DE 4F       LDU    $4F
A550: E7 84       STB    ,X
A552: 39          RTS
A553: 86 C7       LDA    #$C7
A555: A7 04       STA    $4,X
A557: 86 FE       LDA    #$FE
A559: A7 03       STA    $3,X
A55B: 86 30       LDA    #$30
A55D: DE 4F       LDU    $4F
A55F: 1A 50       ORCC   #$50
A561: C6 38       LDB    #$38
A563: E7 84       STB    ,X
A565: E6 84       LDB    ,X
A567: C5 01       BITB   #$01
A569: 27 FA       BEQ    $A565
A56B: E6 03       LDB    $3,X
A56D: C6 28       LDB    #$28
A56F: E7 84       STB    ,X
A571: E6 84       LDB    ,X
A573: 2A FC       BPL    $A571
A575: E6 03       LDB    $3,X
A577: D1 4B       CMPB   $4B
A579: 26 21       BNE    $A59C
A57B: E6 84       LDB    ,X
A57D: 2A FC       BPL    $A57B
A57F: E6 03       LDB    $3,X
A581: 26 19       BNE    $A59C
A583: E6 84       LDB    ,X
A585: 2A FC       BPL    $A583
A587: E6 03       LDB    $3,X
A589: D1 4C       CMPB   $4C
A58B: 26 0F       BNE    $A59C
A58D: E6 84       LDB    ,X
A58F: 2A FC       BPL    $A58D
A591: E6 03       LDB    $3,X
A593: 26 07       BNE    $A59C
A595: 17 FE FB    LBSR   $A493
A598: 4F          CLRA
A599: A6 84       LDA    ,X
A59B: 39          RTS
A59C: 4A          DECA
A59D: 26 C2       BNE    $A561
A59F: 53          COMB
A5A0: 20 F7       BRA    $A599
A5A2: 86 BF       LDA    #$BF
A5A4: A7 07       STA    $7,X
A5A6: 6F 01       CLR    $1,X
A5A8: 39          RTS
A5A9: DE 4F       LDU    $4F
A5AB: 10 8E 00 80 LDY    #$0080
A5AF: CC BF 84    LDD    #$BF84
A5B2: 34 06       PSHS   D
A5B4: A6 E4       LDA    ,S
A5B6: A8 C0       EORA   ,U+
A5B8: 34 02       PSHS   A
A5BA: 44          LSRA
A5BB: 44          LSRA
A5BC: 44          LSRA
A5BD: 44          LSRA
A5BE: A8 E4       EORA   ,S
A5C0: A7 E4       STA    ,S
A5C2: 1F 89       TFR    A,B
A5C4: 54          LSRB
A5C5: 54          LSRB
A5C6: 54          LSRB
A5C7: 48          ASLA
A5C8: 48          ASLA
A5C9: 48          ASLA
A5CA: 48          ASLA
A5CB: E8 62       EORB   $2,S
A5CD: E7 62       STB    $2,S
A5CF: 1F 89       TFR    A,B
A5D1: A8 62       EORA   $2,S
A5D3: A7 61       STA    $1,S
A5D5: 58          ASLB
A5D6: E8 E4       EORB   ,S
A5D8: E7 62       STB    $2,S
A5DA: 32 61       LEAS   $1,S
A5DC: 31 3F       LEAY   -$1,Y
A5DE: 26 D4       BNE    $A5B4
A5E0: 35 06       PULS   D
A5E2: 39          RTS
A5E3: 97 4E       STA    $4E
A5E5: 6F 84       CLR    ,X
A5E7: 35 01       PULS   CC
A5E9: 43          COMA
A5EA: 39          RTS
A5EB: 86 04       LDA    #$04
A5ED: 20 F4       BRA    $A5E3
A5EF: 86 08       LDA    #$08
A5F1: 20 F0       BRA    $A5E3
A5F3: 86 02       LDA    #$02
A5F5: 20 EC       BRA    $A5E3
A5F7: 31 8D 7A 57 LEAY   $12052,PCR
A5FB: 96 49       LDA    $49
A5FD: 84 02       ANDA   #$02
A5FF: 31 A6       LEAY   A,Y
A601: 39          RTS
A602: 96 58       LDA    $58
A604: 26 47       BNE    $A64D
A606: 17 FE 0B    LBSR   $A414
A609: C6 19       LDB    #$19
A60B: 34 01       PSHS   CC
A60D: 17 FF 30    LBSR   $A540
A610: 10 8E 75 00 LDY    #$7500
A614: 31 3F       LEAY   -$1,Y
A616: 10 27 FF D1 LBEQ   $A5EB
A61A: E6 84       LDB    ,X
A61C: C5 02       BITB   #$02
A61E: 27 F4       BEQ    $A614
A620: A7 03       STA    $3,X
A622: E6 84       LDB    ,X
A624: 2A FC       BPL    $A622
A626: A7 03       STA    $3,X
A628: E6 84       LDB    ,X
A62A: 2A FC       BPL    $A628
A62C: C6 FB       LDB    #$FB
A62E: E7 03       STB    $3,X
A630: 4F          CLRA
A631: E6 84       LDB    ,X
A633: 2A FC       BPL    $A631
A635: E6 C0       LDB    ,U+
A637: E7 03       STB    $3,X
A639: 4A          DECA
A63A: 26 F5       BNE    $A631
A63C: E6 84       LDB    ,X
A63E: C5 08       BITB   #$08
A640: 27 FA       BEQ    $A63C
A642: 35 01       PULS   CC
A644: 6F 84       CLR    ,X
A646: 0D 48       TST    $48
A648: 10 2B FE 5C LBMI   $A4A8
A64C: 39          RTS
A64D: 17 FF 52    LBSR   $A5A2
A650: 17 FF 56    LBSR   $A5A9
A653: 34 01       PSHS   CC
A655: 34 06       PSHS   D
A657: 17 FE F9    LBSR   $A553
A65A: 10 25 FF 8D LBCS   $A5EB
A65E: C6 FF       LDB    #$FF
A660: E7 04       STB    $4,X
A662: 86 06       LDA    #$06
A664: C6 24       LDB    #$24
A666: E7 84       STB    ,X
A668: E6 84       LDB    ,X
A66A: 2A FC       BPL    $A668
A66C: 6F 03       CLR    $3,X
A66E: 4A          DECA
A66F: 26 F7       BNE    $A668
A671: E6 84       LDB    ,X
A673: 2A FC       BPL    $A671
A675: CC FB C7    LDD    #$FBC7
A678: ED 03       STD    $3,X
A67A: C6 FF       LDB    #$FF
A67C: A6 84       LDA    ,X
A67E: 2A FC       BPL    $A67C
A680: A6 C0       LDA    ,U+
A682: ED 03       STD    $3,X
A684: 86 7F       LDA    #$7F
A686: E6 84       LDB    ,X
A688: 2A FC       BPL    $A686
A68A: E6 C0       LDB    ,U+
A68C: E7 03       STB    $3,X
A68E: 4A          DECA
A68F: 26 F5       BNE    $A686
A691: E6 84       LDB    ,X
A693: 2A FC       BPL    $A691
A695: 35 04       PULS   B
A697: E7 03       STB    $3,X
A699: 43          COMA
A69A: 26 F5       BNE    $A691
A69C: E6 84       LDB    ,X
A69E: 2A FC       BPL    $A69C
A6A0: 6F 03       CLR    $3,X
A6A2: E6 84       LDB    ,X
A6A4: 2A FC       BPL    $A6A2
A6A6: C6 20       LDB    #$20
A6A8: E7 84       STB    ,X
A6AA: E6 84       LDB    ,X
A6AC: 2A FC       BPL    $A6AA
A6AE: E6 03       LDB    $3,X
A6B0: 43          COMA
A6B1: 26 F7       BNE    $A6AA
A6B3: EC 7E       LDD    -$2,S
A6B5: 35 01       PULS   CC
A6B7: 6F 84       CLR    ,X
A6B9: 0D 48       TST    $48
A6BB: 10 2B FE 37 LBMI   $A4F6
A6BF: 39          RTS
A6C0: FF FF FF    STU    $FFFF
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
