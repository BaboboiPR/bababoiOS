AS = nasm
CC = x86_64-elf-gcc
LD = x86_64-elf-ld

CFLAGS = -ffreestanding -m64 -Wall -Wextra -nostdlib
LDFLAGS = -T linker.ld

.PHONY: all clean run

all: build/os.iso

build/boot.o: kernel/boot.s
	mkdir -p build
	$(AS) -f elf64 $< -o $@

build/kernel.o: kernel/main.c
	mkdir -p build
	$(CC) $(CFLAGS) -c $< -o $@

build/kernel.elf: build/boot.o build/kernel.o
	$(LD) $(LDFLAGS) -o $@ $^

build/os.iso: build/kernel.elf
	mkdir -p build/iso/boot/grub
	cp $< build/iso/boot/
	cp boot/grub/grub.cfg build/iso/boot/grub/
	grub-mkrescue -o $@ build/iso

run: all
	qemu-system-x86_64 -cdrom build/os.iso

clean:
	rm -rf build
