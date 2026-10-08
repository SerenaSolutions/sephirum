CC ?= gcc
CFLAGS ?= -O2 -Wall

all: nexa_core

nexa_core: nexa_core.c
	$(CC) $(CFLAGS) -o $@ $<

check: nexa_core
	python3 ../tests/cross_check_c.py

clean:
	rm -f nexa_core
