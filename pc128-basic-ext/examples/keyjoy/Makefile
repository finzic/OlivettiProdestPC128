LWASM ?= ../../../tools/.local/lwtools-4.24/lwasm/lwasm
PYTHON ?= python3

all: keyjoy.fd keyjoy2.fd

%.bin: %.asm
	$(LWASM) --format=decb --list=$*.lst -o $@ $<

# The disks are formatted and written by BASIC 128 itself, in MAME
keyjoy.fd: keyjoy.bin demo.bas keyjoy.py
	$(PYTHON) keyjoy.py build keyjoy

keyjoy2.fd: keyjoy2.bin demo2.bas keyjoy.py
	$(PYTHON) keyjoy.py build keyjoy2

test: keyjoy.fd
	$(PYTHON) keyjoy.py test keyjoy

test2: keyjoy2.fd
	$(PYTHON) keyjoy.py test keyjoy2

clean:
	rm -f keyjoy.bin keyjoy.lst keyjoy.fd keyjoy2.bin keyjoy2.lst keyjoy2.fd

.PHONY: all test test2 clean
