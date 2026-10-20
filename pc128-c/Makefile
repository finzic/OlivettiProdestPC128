# Convenience wrapper around tools/pc128cc.py (which does the real work).
#   make            library + all examples
#   make lib        build/pc128-c/lib/libolivetti.a
#   make run-hello  build and run examples/hello.c in MAME
#   make test       offline + build tests for the toolchain
ROOT     := ..
PY       ?= python3
CC128    := $(PY) $(ROOT)/tools/pc128cc.py
EXAMPLES := $(basename $(notdir $(wildcard examples/*.c)))

.PHONY: all lib examples test clean $(EXAMPLES)

all: lib examples

lib:
	$(CC128) --lib

examples: $(EXAMPLES)

$(EXAMPLES):
	$(CC128) examples/$@.c

run-%:
	$(PY) $(ROOT)/pc128.py c examples/$*.c --done-addr 9F01 --dump 9F10:16

test:
	cd $(ROOT) && $(PY) -m unittest tests.test_pc128cc -v

clean:
	rm -rf $(ROOT)/build/pc128-c
