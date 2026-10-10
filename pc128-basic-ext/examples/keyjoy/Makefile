LWASM ?= $(firstword $(wildcard ../../.tools/lwtools-4.24/lwasm/lwasm) lwasm)
PYTHON ?= python3

all: keyjoy.fd

keyjoy.bin: keyjoy.asm
	$(LWASM) --format=decb --list=keyjoy.lst -o $@ $<

# The disk is formatted and written by BASIC 128 itself, in MAME
keyjoy.fd: keyjoy.bin demo.bas keyjoy.py
	$(PYTHON) keyjoy.py build

test: keyjoy.fd
	$(PYTHON) keyjoy.py test

clean:
	rm -f keyjoy.bin keyjoy.lst keyjoy.fd

.PHONY: all test clean
