LWASM ?= ../tools/.local/lwtools-4.24/lwasm/lwasm
PYTHON ?= python3

all: build/basext.bin build/basext.bas

build/basext.bin: src/basext.asm src/equ_pc128.asm
	mkdir -p build
	$(LWASM) --format=decb -I src --list=build/basext.lst -o $@ src/basext.asm

build/basext.bas: build/basext.bin ../tools/bin2bas.py
	$(PYTHON) ../tools/bin2bas.py $< $@ --clear 0x8FFF

clean:
	rm -rf build

.PHONY: all clean
