# kernel module
obj-m += crypto_kernel.o

ccflags-y := -Wno-unused-function

KERN_DIR := /lib/modules/$(shell uname -r)/build
PWD      := $(shell pwd)

all: module client

module:
	$(MAKE) -C $(KERN_DIR) M=$(PWD) modules

client: crypto_client
	@true

crypto_client: crypto_client.c crypto_ioctl.h
	$(CC) -Wall -O2 -o $@ crypto_client.c

clean:
	$(MAKE) -C $(KERN_DIR) M=$(PWD) clean
	rm -f crypto_client

.PHONY: all module client clean
