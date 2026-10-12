LWASM ?= ../../../tools/.local/lwtools-4.24/lwasm/lwasm
PYTHON ?= python3

all: keyjoy.fd

%.bin: %.asm
	$(LWASM) --format=decb --list=$*.lst -o $@ $<

# One reusable disk with both routines and demos, written by tools/fdtool.py (no emulator needed)
keyjoy.fd: keyjoy.bin keyjoy2.bin demo.bas demo2.bas $(wildcard tests/*.bas) keyjoy.py
	$(PYTHON) keyjoy.py build

test: keyjoy.fd
	$(PYTHON) keyjoy.py test keyjoy

test2: keyjoy.fd
	$(PYTHON) keyjoy.py test keyjoy2

clean:
	rm -f keyjoy.bin keyjoy.lst keyjoy2.bin keyjoy2.lst keyjoy.fd keyjoy2.fd

.PHONY: all test test2 clean
