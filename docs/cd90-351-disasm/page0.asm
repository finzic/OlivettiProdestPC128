A000: 4D          TSTA
A001: 54          LSRB
A002: 44          LSRA
A003: 3A          ABX
A004: 16 01 0B    LBRA   $A112
A007: 16 00 A5    LBRA   $A0AF
A00A: 16 00 34    LBRA   $A041
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
A02D: 33 8C F8    LEAU   $A028,PCR
A030: 86 03       LDA    #$03
A032: 20 6C       BRA    $A0A0
A034: 35 C6       PULS   D,U,PC
A036: 34 46       PSHS   U,D
A038: 33 8C CC    LEAU   $A007,PCR
A03B: 86 03       LDA    #$03
A03D: 20 61       BRA    $A0A0
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
A0AF: 17 00 86    LBSR   $A138
A0B2: 0F 49       CLR    $49
A0B4: 17 00 8C    LBSR   $A143
A0B7: 17 01 0B    LBSR   $A1C5
A0BA: 25 50       BCS    $A10C
A0BC: 96 4E       LDA    $4E
A0BE: 81 43       CMPA   #$43
A0C0: 10 27 FF 74 LBEQ   $A038
A0C4: 86 02       LDA    #$02
A0C6: 34 02       PSHS   A
A0C8: 0F 58       CLR    $58
A0CA: 0F 4A       CLR    $4A
A0CC: 0F 4B       CLR    $4B
A0CE: 86 01       LDA    #$01
A0D0: 97 4C       STA    $4C
A0D2: 33 8D 81 2A LEAU   $2200,PCR
A0D6: DF 4F       STU    $4F
A0D8: 17 03 8D    LBSR   $A468
A0DB: 17 00 83    LBSR   $A161
A0DE: DE 4F       LDU    $4F
A0E0: 24 08       BCC    $A0EA
A0E2: 96 58       LDA    $58
A0E4: 26 21       BNE    $A107
A0E6: 03 58       COM    $58
A0E8: 20 E0       BRA    $A0CA
A0EA: 31 8D 81 91 LEAY   $227F,PCR
A0EE: 34 20       PSHS   Y
A0F0: 86 55       LDA    #$55
A0F2: 6A C4       DEC    ,U
A0F4: 63 C4       COM    ,U
A0F6: AB C0       ADDA   ,U+
A0F8: 11 A3 E4    CMPU   ,S
A0FB: 26 F5       BNE    $A0F2
A0FD: 35 20       PULS   Y
A0FF: A1 C4       CMPA   ,U
A101: 26 09       BNE    $A10C
A103: 6E 8D 80 F9 JMP    $2200,PCR
A107: 35 02       PULS   A
A109: 4A          DECA
A10A: 26 BA       BNE    $A0C6
A10C: 0F 80       CLR    $80
A10E: 6E 9F 00 1E JMP    [$001E]
A112: 34 7F       PSHS   U,Y,X,DP,D,CC
A114: 8D 22       BSR    $A138
A116: 8D 2B       BSR    $A143
A118: 25 06       BCS    $A120
A11A: 8D 4E       BSR    $A16A
A11C: 8D 43       BSR    $A161
A11E: 24 07       BCC    $A127
A120: 35 02       PULS   A
A122: 1E 8A       EXG    A,CC
A124: 44          LSRA
A125: 35 FE       PULS   D,DP,X,Y,U,PC
A127: 96 48       LDA    $48
A129: 81 01       CMPA   #$01
A12B: 26 08       BNE    $A135
A12D: 96 4E       LDA    $4E
A12F: 81 43       CMPA   #$43
A131: 10 27 FE F8 LBEQ   $A02D
A135: 4F          CLRA
A136: 20 E8       BRA    $A120
A138: 1F 50       TFR    PC,D
A13A: 84 70       ANDA   #$70
A13C: 1F 8B       TFR    A,DP
A13E: 30 8D 06 8E LEAX   $A7D0,PCR
A142: 39          RTS
A143: 96 48       LDA    $48
A145: 81 01       CMPA   #$01
A147: 26 0E       BNE    $A157
A149: C6 01       LDB    #$01
A14B: 33 8D 00 17 LEAU   $A166,PCR
A14F: A6 C5       LDA    B,U
A151: A7 02       STA    $2,X
A153: 97 57       STA    $57
A155: 4F          CLRA
A156: 39          RTS
A157: D6 49       LDB    $49
A159: C1 04       CMPB   #$04
A15B: 10 24 03 DD LBCC   $A53C
A15F: 20 EA       BRA    $A14B
A161: 86 40       LDA    #$40
A163: A7 02       STA    $2,X
A165: 39          RTS
A166: 41          NEGA
A167: 01 42       NEG    $42
A169: 02 86       XNC    $86
A16B: 02 34       XNC    $34
A16D: 02 96       XNC    $96
A16F: 48          ASLA
A170: 31 8D 00 51 LEAY   $A1C5,PCR
A174: 85 01       BITA   #$01
A176: 26 30       BNE    $A1A8
A178: 31 8D 02 EC LEAY   $A468,PCR
A17C: 85 02       BITA   #$02
A17E: 26 28       BNE    $A1A8
A180: 31 8D 00 BA LEAY   $A23E,PCR
A184: 85 08       BITA   #$08
A186: 26 20       BNE    $A1A8
A188: 31 8D 00 6F LEAY   $A1FB,PCR
A18C: 85 20       BITA   #$20
A18E: 26 18       BNE    $A1A8
A190: 31 8D 03 86 LEAY   $A51A,PCR
A194: 85 40       BITA   #$40
A196: 26 10       BNE    $A1A8
A198: 31 8D 00 99 LEAY   $A235,PCR
A19C: 85 04       BITA   #$04
A19E: 26 08       BNE    $A1A8
A1A0: 31 8D 00 97 LEAY   $A23B,PCR
A1A4: 85 10       BITA   #$10
A1A6: 27 1A       BEQ    $A1C2
A1A8: AD A4       JSR    ,Y
A1AA: 24 17       BCC    $A1C3
A1AC: 96 4E       LDA    $4E
A1AE: 85 51       BITA   #$51
A1B0: 26 11       BNE    $A1C3
A1B2: 6A E4       DEC    ,S
A1B4: 27 0C       BEQ    $A1C2
A1B6: 0F 4E       CLR    $4E
A1B8: 81 08       CMPA   #$08
A1BA: 27 B2       BEQ    $A16E
A1BC: 8D 3D       BSR    $A1FB
A1BE: 25 F2       BCS    $A1B2
A1C0: 20 AC       BRA    $A16E
A1C2: 53          COMB
A1C3: 35 82       PULS   A,PC
A1C5: 8D 34       BSR    $A1FB
A1C7: 25 31       BCS    $A1FA
A1C9: 86 01       LDA    #$01
A1CB: 97 4B       STA    $4B
A1CD: 17 03 72    LBSR   $A542
A1D0: C6 44       LDB    #$44
A1D2: A6 01       LDA    $1,X
A1D4: 85 08       BITA   #$08
A1D6: 27 02       BEQ    $A1DA
A1D8: C6 43       LDB    #$43
A1DA: D7 4E       STB    $4E
A1DC: 8D 1D       BSR    $A1FB
A1DE: 0F 52       CLR    $52
A1E0: 0F 54       CLR    $54
A1E2: 6F 84       CLR    ,X
A1E4: 0F 58       CLR    $58
A1E6: DC E9       LDD    $E9
A1E8: 93 ED       SUBD   $ED
A1EA: 2C 05       BGE    $A1F1
A1EC: 43          COMA
A1ED: 53          COMB
A1EE: C3 00 01    ADDD   #$0001
A1F1: 4D          TSTA
A1F2: 26 05       BNE    $A1F9
A1F4: 5D          TSTB
A1F5: 2A 02       BPL    $A1F9
A1F7: 03 58       COM    $58
A1F9: 4F          CLRA
A1FA: 39          RTS
A1FB: C6 64       LDB    #$64
A1FD: A6 01       LDA    $1,X
A1FF: 85 08       BITA   #$08
A201: 26 13       BNE    $A216
A203: 96 57       LDA    $57
A205: 8A 10       ORA    #$10
A207: A7 02       STA    $2,X
A209: 84 EF       ANDA   #$EF
A20B: A7 02       STA    $2,X
A20D: 8D 1D       BSR    $A22C
A20F: 5A          DECB
A210: 10 27 03 28 LBEQ   $A53C
A214: 20 E7       BRA    $A1FD
A216: 8D 0E       BSR    $A226
A218: 17 03 55    LBSR   $A570
A21B: 6F A4       CLR    ,Y
A21D: 6F 06       CLR    $6,X
A21F: 39          RTS
A220: 10 8E 00 6C LDY    #$006C
A224: 20 0A       BRA    $A230
A226: 10 8E 07 50 LDY    #$0750
A22A: 20 04       BRA    $A230
A22C: 10 8E 02 EC LDY    #$02EC
A230: 31 3F       LEAY   -$1,Y
A232: 26 FC       BNE    $A230
A234: 39          RTS
A235: 86 FF       LDA    #$FF
A237: 97 58       STA    $58
A239: 4F          CLRA
A23A: 39          RTS
A23B: 0F 58       CLR    $58
A23D: 39          RTS
A23E: 17 02 D9    LBSR   $A51A
A241: 10 25 00 9E LBCS   $A2E3
A245: A6 01       LDA    $1,X
A247: 85 04       BITA   #$04
A249: 27 05       BEQ    $A250
A24B: 86 01       LDA    #$01
A24D: 16 02 EE    LBRA   $A53E
A250: 96 58       LDA    $58
A252: 10 26 00 92 LBNE   $A2E8
A256: 17 01 BD    LBSR   $A416
A259: C6 19       LDB    #$19
A25B: 34 01       PSHS   CC
A25D: 17 01 4C    LBSR   $A3AC
A260: 10 8E 75 00 LDY    #$7500
A264: 31 3F       LEAY   -$1,Y
A266: 10 27 02 9E LBEQ   $A508
A26A: E6 84       LDB    ,X
A26C: C5 02       BITB   #$02
A26E: 27 F4       BEQ    $A264
A270: A7 03       STA    $3,X
A272: E6 84       LDB    ,X
A274: 2A FC       BPL    $A272
A276: A7 03       STA    $3,X
A278: E6 84       LDB    ,X
A27A: 2A FC       BPL    $A278
A27C: C6 FB       LDB    #$FB
A27E: E7 03       STB    $3,X
A280: 4F          CLRA
A281: E6 84       LDB    ,X
A283: 2A FC       BPL    $A281
A285: E6 C0       LDB    ,U+
A287: E7 03       STB    $3,X
A289: 4A          DECA
A28A: 26 F5       BNE    $A281
A28C: E6 84       LDB    ,X
A28E: C5 08       BITB   #$08
A290: 27 FA       BEQ    $A28C
A292: 17 FF 8B    LBSR   $A220
A295: 0D 48       TST    $48
A297: 2A 4A       BPL    $A2E3
A299: 17 02 86    LBSR   $A522
A29C: C6 1B       LDB    #$1B
A29E: 17 01 0B    LBSR   $A3AC
A2A1: 86 04       LDA    #$04
A2A3: 10 8E 75 00 LDY    #$7500
A2A7: 31 3F       LEAY   -$1,Y
A2A9: 10 27 00 FA LBEQ   $A3A7
A2AD: E6 84       LDB    ,X
A2AF: C5 02       BITB   #$02
A2B1: 27 F4       BEQ    $A2A7
A2B3: E6 03       LDB    $3,X
A2B5: 4A          DECA
A2B6: 10 27 02 56 LBEQ   $A510
A2BA: E6 84       LDB    ,X
A2BC: 2A FC       BPL    $A2BA
A2BE: E6 03       LDB    $3,X
A2C0: C1 FB       CMPB   #$FB
A2C2: 26 F1       BNE    $A2B5
A2C4: 4F          CLRA
A2C5: E6 84       LDB    ,X
A2C7: 2A FC       BPL    $A2C5
A2C9: E6 03       LDB    $3,X
A2CB: E1 C0       CMPB   ,U+
A2CD: 26 03       BNE    $A2D2
A2CF: 4A          DECA
A2D0: 26 F3       BNE    $A2C5
A2D2: E6 84       LDB    ,X
A2D4: C5 08       BITB   #$08
A2D6: 27 FA       BEQ    $A2D2
A2D8: 4D          TSTA
A2D9: 10 26 00 CA LBNE   $A3A7
A2DD: C5 04       BITB   #$04
A2DF: 10 26 00 C4 LBNE   $A3A7
A2E3: 35 01       PULS   CC
A2E5: 6F 84       CLR    ,X
A2E7: 39          RTS
A2E8: 17 01 3C    LBSR   $A427
A2EB: 17 01 40    LBSR   $A42E
A2EE: 34 01       PSHS   CC
A2F0: 34 06       PSHS   D
A2F2: 17 00 CA    LBSR   $A3BF
A2F5: 24 05       BCC    $A2FC
A2F7: 35 06       PULS   D
A2F9: 16 02 0C    LBRA   $A508
A2FC: C6 FF       LDB    #$FF
A2FE: E7 04       STB    $4,X
A300: 86 06       LDA    #$06
A302: C6 24       LDB    #$24
A304: E7 84       STB    ,X
A306: E6 84       LDB    ,X
A308: 2A FC       BPL    $A306
A30A: 6F 03       CLR    $3,X
A30C: 4A          DECA
A30D: 26 F7       BNE    $A306
A30F: E6 84       LDB    ,X
A311: 2A FC       BPL    $A30F
A313: CC FB C7    LDD    #$FBC7
A316: ED 03       STD    $3,X
A318: C6 FF       LDB    #$FF
A31A: A6 84       LDA    ,X
A31C: 2A FC       BPL    $A31A
A31E: A6 C0       LDA    ,U+
A320: ED 03       STD    $3,X
A322: 86 7F       LDA    #$7F
A324: E6 84       LDB    ,X
A326: 2A FC       BPL    $A324
A328: E6 C0       LDB    ,U+
A32A: E7 03       STB    $3,X
A32C: 4A          DECA
A32D: 26 F5       BNE    $A324
A32F: E6 84       LDB    ,X
A331: 2A FC       BPL    $A32F
A333: 35 04       PULS   B
A335: E7 03       STB    $3,X
A337: 43          COMA
A338: 26 F5       BNE    $A32F
A33A: E6 84       LDB    ,X
A33C: 2A FC       BPL    $A33A
A33E: 6F 03       CLR    $3,X
A340: E6 84       LDB    ,X
A342: 2A FC       BPL    $A340
A344: C6 20       LDB    #$20
A346: E7 84       STB    ,X
A348: E6 84       LDB    ,X
A34A: 2A FC       BPL    $A348
A34C: E6 03       LDB    $3,X
A34E: 43          COMA
A34F: 26 F7       BNE    $A348
A351: 32 7E       LEAS   -$2,S
A353: 17 FE CA    LBSR   $A220
A356: 0D 48       TST    $48
A358: 2A 44       BPL    $A39E
A35A: 17 01 C5    LBSR   $A522
A35D: 17 00 5F    LBSR   $A3BF
A360: 25 43       BCS    $A3A5
A362: C6 FB       LDB    #$FB
A364: E7 03       STB    $3,X
A366: 86 80       LDA    #$80
A368: C6 38       LDB    #$38
A36A: E7 84       STB    ,X
A36C: 10 8E 01 00 LDY    #$0100
A370: 31 3F       LEAY   -$1,Y
A372: 27 31       BEQ    $A3A5
A374: E6 84       LDB    ,X
A376: C5 01       BITB   #$01
A378: 27 F6       BEQ    $A370
A37A: E6 03       LDB    $3,X
A37C: C6 28       LDB    #$28
A37E: E7 84       STB    ,X
A380: E6 84       LDB    ,X
A382: 2A FC       BPL    $A380
A384: E6 03       LDB    $3,X
A386: E1 C0       CMPB   ,U+
A388: 26 1B       BNE    $A3A5
A38A: 4A          DECA
A38B: 26 F3       BNE    $A380
A38D: A6 84       LDA    ,X
A38F: 2A FC       BPL    $A38D
A391: A6 03       LDA    $3,X
A393: E6 84       LDB    ,X
A395: 2A FC       BPL    $A393
A397: E6 03       LDB    $3,X
A399: 10 A3 E4    CMPD   ,S
A39C: 26 07       BNE    $A3A5
A39E: 35 06       PULS   D
A3A0: 35 01       PULS   CC
A3A2: 6F 84       CLR    ,X
A3A4: 39          RTS
A3A5: 35 06       PULS   D
A3A7: 86 20       LDA    #$20
A3A9: 16 01 66    LBRA   $A512
A3AC: 96 4C       LDA    $4C
A3AE: A7 05       STA    $5,X
A3B0: 86 0A       LDA    #$0A
A3B2: A7 04       STA    $4,X
A3B4: 86 A1       LDA    #$A1
A3B6: A7 03       STA    $3,X
A3B8: 1A 50       ORCC   #$50
A3BA: DE 4F       LDU    $4F
A3BC: E7 84       STB    ,X
A3BE: 39          RTS
A3BF: 86 C7       LDA    #$C7
A3C1: A7 04       STA    $4,X
A3C3: 86 FE       LDA    #$FE
A3C5: A7 03       STA    $3,X
A3C7: 86 30       LDA    #$30
A3C9: DE 4F       LDU    $4F
A3CB: 1A 50       ORCC   #$50
A3CD: C6 38       LDB    #$38
A3CF: E7 84       STB    ,X
A3D1: 10 8E 17 00 LDY    #$1700
A3D5: 31 3F       LEAY   -$1,Y
A3D7: 27 3A       BEQ    $A413
A3D9: E6 84       LDB    ,X
A3DB: C5 01       BITB   #$01
A3DD: 27 F6       BEQ    $A3D5
A3DF: E6 03       LDB    $3,X
A3E1: C6 28       LDB    #$28
A3E3: E7 84       STB    ,X
A3E5: E6 84       LDB    ,X
A3E7: 2A FC       BPL    $A3E5
A3E9: E6 03       LDB    $3,X
A3EB: D1 4B       CMPB   $4B
A3ED: 26 21       BNE    $A410
A3EF: E6 84       LDB    ,X
A3F1: 2A FC       BPL    $A3EF
A3F3: E6 03       LDB    $3,X
A3F5: 26 19       BNE    $A410
A3F7: E6 84       LDB    ,X
A3F9: 2A FC       BPL    $A3F7
A3FB: E6 03       LDB    $3,X
A3FD: D1 4C       CMPB   $4C
A3FF: 26 0F       BNE    $A410
A401: E6 84       LDB    ,X
A403: 2A FC       BPL    $A401
A405: E6 03       LDB    $3,X
A407: 26 07       BNE    $A410
A409: 17 FE 14    LBSR   $A220
A40C: 4F          CLRA
A40D: A6 84       LDA    ,X
A40F: 39          RTS
A410: 4A          DECA
A411: 26 BA       BNE    $A3CD
A413: 53          COMB
A414: 20 F7       BRA    $A40D
A416: C1 39       CMPB   #$39
A418: 2A 05       BPL    $A41F
A41A: CC 9F 20    LDD    #$9F20
A41D: 20 03       BRA    $A422
A41F: CC 1F 22    LDD    #$1F22
A422: A7 07       STA    $7,X
A424: E7 01       STB    $1,X
A426: 39          RTS
A427: 86 BF       LDA    #$BF
A429: A7 07       STA    $7,X
A42B: 6F 01       CLR    $1,X
A42D: 39          RTS
A42E: DE 4F       LDU    $4F
A430: 10 8E 00 80 LDY    #$0080
A434: CC BF 84    LDD    #$BF84
A437: 34 06       PSHS   D
A439: A6 E4       LDA    ,S
A43B: A8 C0       EORA   ,U+
A43D: 34 02       PSHS   A
A43F: 44          LSRA
A440: 44          LSRA
A441: 44          LSRA
A442: 44          LSRA
A443: A8 E4       EORA   ,S
A445: A7 E4       STA    ,S
A447: 1F 89       TFR    A,B
A449: 54          LSRB
A44A: 54          LSRB
A44B: 54          LSRB
A44C: 48          ASLA
A44D: 48          ASLA
A44E: 48          ASLA
A44F: 48          ASLA
A450: E8 62       EORB   $2,S
A452: E7 62       STB    $2,S
A454: 1F 89       TFR    A,B
A456: A8 62       EORA   $2,S
A458: A7 61       STA    $1,S
A45A: 58          ASLB
A45B: E8 E4       EORB   ,S
A45D: E7 62       STB    $2,S
A45F: 32 61       LEAS   $1,S
A461: 31 3F       LEAY   -$1,Y
A463: 26 D4       BNE    $A439
A465: 35 06       PULS   D
A467: 39          RTS
A468: 17 00 AF    LBSR   $A51A
A46B: 10 25 00 98 LBCS   $A507
A46F: 34 01       PSHS   CC
A471: 96 58       LDA    $58
A473: 26 43       BNE    $A4B8
A475: 17 FF 9E    LBSR   $A416
A478: C6 1B       LDB    #$1B
A47A: 17 FF 2F    LBSR   $A3AC
A47D: 86 04       LDA    #$04
A47F: 10 8E 75 00 LDY    #$7500
A483: 31 3F       LEAY   -$1,Y
A485: 10 27 00 7F LBEQ   $A508
A489: E6 84       LDB    ,X
A48B: C5 02       BITB   #$02
A48D: 27 F4       BEQ    $A483
A48F: E6 03       LDB    $3,X
A491: 4A          DECA
A492: 10 27 00 7A LBEQ   $A510
A496: E6 84       LDB    ,X
A498: 2A FC       BPL    $A496
A49A: E6 03       LDB    $3,X
A49C: C1 FB       CMPB   #$FB
A49E: 26 F1       BNE    $A491
A4A0: 4F          CLRA
A4A1: E6 84       LDB    ,X
A4A3: 2A FC       BPL    $A4A1
A4A5: E6 03       LDB    $3,X
A4A7: E7 C0       STB    ,U+
A4A9: 4A          DECA
A4AA: 26 F5       BNE    $A4A1
A4AC: E6 84       LDB    ,X
A4AE: C5 08       BITB   #$08
A4B0: 27 FA       BEQ    $A4AC
A4B2: C5 04       BITB   #$04
A4B4: 26 56       BNE    $A50C
A4B6: 20 4B       BRA    $A503
A4B8: 17 FF 6C    LBSR   $A427
A4BB: 17 FF 01    LBSR   $A3BF
A4BE: 25 48       BCS    $A508
A4C0: 31 23       LEAY   $3,Y
A4C2: 17 FD 6B    LBSR   $A230
A4C5: C6 FB       LDB    #$FB
A4C7: E7 03       STB    $3,X
A4C9: 86 80       LDA    #$80
A4CB: C6 38       LDB    #$38
A4CD: E7 84       STB    ,X
A4CF: 10 8E 01 00 LDY    #$0100
A4D3: 31 3F       LEAY   -$1,Y
A4D5: 27 39       BEQ    $A510
A4D7: E6 84       LDB    ,X
A4D9: C5 01       BITB   #$01
A4DB: 27 F6       BEQ    $A4D3
A4DD: E6 03       LDB    $3,X
A4DF: C6 28       LDB    #$28
A4E1: E7 84       STB    ,X
A4E3: E6 84       LDB    ,X
A4E5: 2A FC       BPL    $A4E3
A4E7: E6 03       LDB    $3,X
A4E9: E7 C0       STB    ,U+
A4EB: 4A          DECA
A4EC: 26 F5       BNE    $A4E3
A4EE: E6 84       LDB    ,X
A4F0: 2A FC       BPL    $A4EE
A4F2: E6 03       LDB    $3,X
A4F4: 34 04       PSHS   B
A4F6: 43          COMA
A4F7: 26 F5       BNE    $A4EE
A4F9: 17 FF 32    LBSR   $A42E
A4FC: 1E 89       EXG    A,B
A4FE: 10 A3 E1    CMPD   ,S++
A501: 26 09       BNE    $A50C
A503: 35 01       PULS   CC
A505: 6F 84       CLR    ,X
A507: 39          RTS
A508: 86 04       LDA    #$04
A50A: 20 06       BRA    $A512
A50C: 86 08       LDA    #$08
A50E: 20 02       BRA    $A512
A510: 86 02       LDA    #$02
A512: 97 4E       STA    $4E
A514: 6F 84       CLR    ,X
A516: 35 01       PULS   CC
A518: 43          COMA
A519: 39          RTS
A51A: 8D 06       BSR    $A522
A51C: 25 03       BCS    $A521
A51E: 8D 22       BSR    $A542
A520: 4F          CLRA
A521: 39          RTS
A522: 10 8E 80 00 LDY    #$8000
A526: D6 57       LDB    $57
A528: CA 04       ORB    #$04
A52A: E7 02       STB    $2,X
A52C: C4 FB       ANDB   #$FB
A52E: E7 02       STB    $2,X
A530: 31 3F       LEAY   -$1,Y
A532: 27 08       BEQ    $A53C
A534: E6 01       LDB    $1,X
A536: C4 02       ANDB   #$02
A538: 27 EC       BEQ    $A526
A53A: 4F          CLRA
A53B: 39          RTS
A53C: 86 10       LDA    #$10
A53E: 34 01       PSHS   CC
A540: 20 D0       BRA    $A512
A542: 17 FC E7    LBSR   $A22C
A545: 8D 29       BSR    $A570
A547: E6 A4       LDB    ,Y
A549: 96 57       LDA    $57
A54B: D0 4B       SUBB   $4B
A54D: 27 18       BEQ    $A567
A54F: 2A 03       BPL    $A554
A551: 8A 20       ORA    #$20
A553: 50          NEGB
A554: A7 02       STA    $2,X
A556: 8A 14       ORA    #$14
A558: A7 02       STA    $2,X
A55A: 84 EB       ANDA   #$EB
A55C: A7 02       STA    $2,X
A55E: 17 FC CB    LBSR   $A22C
A561: 5A          DECB
A562: 26 F2       BNE    $A556
A564: 17 FC BF    LBSR   $A226
A567: 8D 07       BSR    $A570
A569: D6 4B       LDB    $4B
A56B: E7 06       STB    $6,X
A56D: E7 A4       STB    ,Y
A56F: 39          RTS
A570: 31 8D 7A DE LEAY   $12052,PCR
A574: 96 49       LDA    $49
A576: 84 02       ANDA   #$02
A578: 31 A6       LEAY   A,Y
A57A: 39          RTS
A57B: FF FF FF    STU    $FFFF
A57E: FF FF FF    STU    $FFFF
A581: FF FF FF    STU    $FFFF
A584: FF FF FF    STU    $FFFF
A587: FF FF FF    STU    $FFFF
A58A: FF FF FF    STU    $FFFF
A58D: FF FF FF    STU    $FFFF
A590: FF FF FF    STU    $FFFF
A593: FF FF FF    STU    $FFFF
A596: FF FF FF    STU    $FFFF
A599: FF FF FF    STU    $FFFF
A59C: FF FF FF    STU    $FFFF
A59F: FF FF FF    STU    $FFFF
A5A2: FF FF FF    STU    $FFFF
A5A5: FF FF FF    STU    $FFFF
A5A8: FF FF FF    STU    $FFFF
A5AB: FF FF FF    STU    $FFFF
A5AE: FF FF FF    STU    $FFFF
A5B1: FF FF FF    STU    $FFFF
A5B4: FF FF FF    STU    $FFFF
A5B7: FF FF FF    STU    $FFFF
A5BA: FF FF FF    STU    $FFFF
A5BD: FF FF FF    STU    $FFFF
A5C0: FF FF FF    STU    $FFFF
A5C3: FF FF FF    STU    $FFFF
A5C6: FF FF FF    STU    $FFFF
A5C9: FF FF FF    STU    $FFFF
A5CC: FF FF FF    STU    $FFFF
A5CF: FF FF FF    STU    $FFFF
A5D2: FF FF FF    STU    $FFFF
A5D5: FF FF FF    STU    $FFFF
A5D8: FF FF FF    STU    $FFFF
A5DB: FF FF FF    STU    $FFFF
A5DE: FF FF FF    STU    $FFFF
A5E1: FF FF FF    STU    $FFFF
A5E4: FF FF FF    STU    $FFFF
A5E7: FF FF FF    STU    $FFFF
A5EA: FF FF FF    STU    $FFFF
A5ED: FF FF FF    STU    $FFFF
A5F0: FF FF FF    STU    $FFFF
A5F3: FF FF FF    STU    $FFFF
A5F6: FF FF FF    STU    $FFFF
A5F9: FF FF FF    STU    $FFFF
A5FC: FF FF FF    STU    $FFFF
A5FF: FF FF FF    STU    $FFFF
A602: FF FF FF    STU    $FFFF
A605: FF FF FF    STU    $FFFF
A608: FF FF FF    STU    $FFFF
A60B: FF FF FF    STU    $FFFF
A60E: FF FF FF    STU    $FFFF
A611: FF FF FF    STU    $FFFF
A614: FF FF FF    STU    $FFFF
A617: FF FF FF    STU    $FFFF
A61A: FF FF FF    STU    $FFFF
A61D: FF FF FF    STU    $FFFF
A620: FF FF FF    STU    $FFFF
A623: FF FF FF    STU    $FFFF
A626: FF FF FF    STU    $FFFF
A629: FF FF FF    STU    $FFFF
A62C: FF FF FF    STU    $FFFF
A62F: FF FF FF    STU    $FFFF
A632: FF FF FF    STU    $FFFF
A635: FF FF FF    STU    $FFFF
A638: FF FF FF    STU    $FFFF
A63B: FF FF FF    STU    $FFFF
A63E: FF FF FF    STU    $FFFF
A641: FF FF FF    STU    $FFFF
A644: FF FF FF    STU    $FFFF
A647: FF FF FF    STU    $FFFF
A64A: FF FF FF    STU    $FFFF
A64D: FF FF FF    STU    $FFFF
A650: FF FF FF    STU    $FFFF
A653: FF FF FF    STU    $FFFF
A656: FF FF FF    STU    $FFFF
A659: FF FF FF    STU    $FFFF
A65C: FF FF FF    STU    $FFFF
A65F: FF FF FF    STU    $FFFF
A662: FF FF FF    STU    $FFFF
A665: FF FF FF    STU    $FFFF
A668: FF FF FF    STU    $FFFF
A66B: FF FF FF    STU    $FFFF
A66E: FF FF FF    STU    $FFFF
A671: FF FF FF    STU    $FFFF
A674: FF FF FF    STU    $FFFF
A677: FF FF FF    STU    $FFFF
A67A: FF FF FF    STU    $FFFF
A67D: FF FF FF    STU    $FFFF
A680: FF FF FF    STU    $FFFF
A683: FF FF FF    STU    $FFFF
A686: FF FF FF    STU    $FFFF
A689: FF FF FF    STU    $FFFF
A68C: FF FF FF    STU    $FFFF
A68F: FF FF FF    STU    $FFFF
A692: FF FF FF    STU    $FFFF
A695: FF FF FF    STU    $FFFF
A698: FF FF FF    STU    $FFFF
A69B: FF FF FF    STU    $FFFF
A69E: FF FF FF    STU    $FFFF
A6A1: FF FF FF    STU    $FFFF
A6A4: FF FF FF    STU    $FFFF
A6A7: FF FF FF    STU    $FFFF
A6AA: FF FF FF    STU    $FFFF
A6AD: FF FF FF    STU    $FFFF
A6B0: FF FF FF    STU    $FFFF
A6B3: FF FF FF    STU    $FFFF
A6B6: FF FF FF    STU    $FFFF
A6B9: FF FF FF    STU    $FFFF
A6BC: FF FF FF    STU    $FFFF
A6BF: FF FF FF    STU    $FFFF
A6C2: FF FF FF    STU    $FFFF
A6C5: FF FF FF    STU    $FFFF
A6C8: FF FF FF    STU    $FFFF
A6CB: FF FF FF    STU    $FFFF
A6CE: FF FF FF    STU    $FFFF
A6D1: FF FF FF    STU    $FFFF
A6D4: FF FF FF    STU    $FFFF
A6D7: FF FF FF    STU    $FFFF
A6DA: FF FF FF    STU    $FFFF
A6DD: FF FF FF    STU    $FFFF
A6E0: FF FF FF    STU    $FFFF
A6E3: FF FF FF    STU    $FFFF
A6E6: FF FF FF    STU    $FFFF
A6E9: FF FF FF    STU    $FFFF
A6EC: FF FF FF    STU    $FFFF
A6EF: FF FF FF    STU    $FFFF
A6F2: FF FF FF    STU    $FFFF
A6F5: FF FF FF    STU    $FFFF
A6F8: FF FF FF    STU    $FFFF
A6FB: FF FF FF    STU    $FFFF
A6FE: FF FF FF    STU    $FFFF
A701: FF FF FF    STU    $FFFF
A704: FF FF FF    STU    $FFFF
A707: FF FF FF    STU    $FFFF
A70A: FF FF FF    STU    $FFFF
A70D: FF FF FF    STU    $FFFF
A710: FF FF FF    STU    $FFFF
A713: FF FF FF    STU    $FFFF
A716: FF FF FF    STU    $FFFF
A719: FF FF FF    STU    $FFFF
A71C: FF FF FF    STU    $FFFF
A71F: FF FF FF    STU    $FFFF
A722: FF FF FF    STU    $FFFF
A725: FF FF FF    STU    $FFFF
A728: FF FF FF    STU    $FFFF
A72B: FF FF FF    STU    $FFFF
A72E: FF FF FF    STU    $FFFF
A731: FF FF FF    STU    $FFFF
A734: FF FF FF    STU    $FFFF
A737: FF FF FF    STU    $FFFF
A73A: FF FF FF    STU    $FFFF
A73D: FF FF FF    STU    $FFFF
A740: FF FF FF    STU    $FFFF
A743: FF FF FF    STU    $FFFF
A746: FF FF FF    STU    $FFFF
A749: FF FF FF    STU    $FFFF
A74C: FF FF FF    STU    $FFFF
A74F: FF FF FF    STU    $FFFF
A752: FF FF FF    STU    $FFFF
A755: FF FF FF    STU    $FFFF
A758: FF FF FF    STU    $FFFF
A75B: FF FF FF    STU    $FFFF
A75E: FF FF FF    STU    $FFFF
A761: FF FF FF    STU    $FFFF
A764: FF FF FF    STU    $FFFF
A767: FF FF FF    STU    $FFFF
A76A: FF FF FF    STU    $FFFF
A76D: FF FF FF    STU    $FFFF
A770: FF FF FF    STU    $FFFF
A773: FF FF FF    STU    $FFFF
A776: FF FF FF    STU    $FFFF
A779: FF FF FF    STU    $FFFF
A77C: FF FF FF    STU    $FFFF
A77F: FF FF FF    STU    $FFFF
A782: FF FF FF    STU    $FFFF
A785: FF FF FF    STU    $FFFF
A788: FF FF FF    STU    $FFFF
A78B: FF FF FF    STU    $FFFF
A78E: FF FF FF    STU    $FFFF
A791: FF FF FF    STU    $FFFF
A794: FF FF FF    STU    $FFFF
A797: FF FF FF    STU    $FFFF
A79A: FF FF FF    STU    $FFFF
A79D: FF FF FF    STU    $FFFF
A7A0: FF FF FF    STU    $FFFF
A7A3: FF FF FF    STU    $FFFF
A7A6: FF FF FF    STU    $FFFF
A7A9: FF FF FF    STU    $FFFF
A7AC: FF FF FF    STU    $FFFF
A7AF: FF FF FF    STU    $FFFF
A7B2: FF FF FF    STU    $FFFF
A7B5: FF FF FF    STU    $FFFF
A7B8: FF FF FF    STU    $FFFF
A7BB: FF FF FF    STU    $FFFF
A7BE: FF FF 38    STU    $FF38
