JDK_HOME ?= $(shell java -XshowSettings:properties -version 2>&1 \
                | grep 'java\.home' | awk '{print $$3}')

CC      = gcc
CFLAGS  = -fPIC -O2 -Wall -Wextra -std=c11
INCLUDES = -I$(JDK_HOME)/include -I$(JDK_HOME)/include/linux

.PHONY: all clean

all: libksm_helper.so libcap_dropper.so

libksm_helper.so: ksm_helper.c
	$(CC) $(CFLAGS) $(INCLUDES) -shared -o $@ $<
	@echo "Built $@"

libcap_dropper.so: cap_dropper.c
	$(CC) $(CFLAGS) $(INCLUDES) -shared -o $@ $<
	@echo "Built $@"

clean:
	rm -f *.so
