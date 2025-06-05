# Compiler and flags
CC := x86_64-elf-gcc
CFLAGS := -ffreestanding -I src/intf -I src/lib/fatfs -I src/lib -DFF_USE_MKFS=1


# Kernel source and object files
kernel_source_files := $(shell find src/impl/kernel -name '*.c')
kernel_object_files := $(patsubst src/impl/kernel/%.c, build/kernel/%.o, $(kernel_source_files))

# Architecture-specific source and object files
x86_64_c_source_files := $(shell find src/impl/x86_64 -name '*.c')
x86_64_c_object_files := $(patsubst src/impl/x86_64/%.c, build/x86_64/%.o, $(x86_64_c_source_files))

x86_64_asm_source_files := $(shell find src/impl/x86_64 -name '*.asm')
x86_64_asm_object_files := $(patsubst src/impl/x86_64/%.asm, build/x86_64/%.o, $(x86_64_asm_source_files))


# FatFs source and object files (include diskio.c + helper glue)
fatfs_source_files := $(wildcard src/lib/fatfs/*.c)
fatfs_object_files := $(patsubst src/lib/fatfs/%.c, build/fatfs/%.o, $(fatfs_source_files))

# libc glue for memcmp, strchr, get_fattime
libc_source_files := $(wildcard src/lib/*.c)
libc_object_files := $(patsubst src/lib/%.c, build/lib/%.o, $(libc_source_files))

# Compile rules
build/kernel/%.o: src/impl/kernel/%.c
	mkdir -p $(dir $@) && \
	$(CC) -c $(CFLAGS) $< -o $@

build/x86_64/%.o: src/impl/x86_64/%.c
	mkdir -p $(dir $@) && \
	$(CC) -c $(CFLAGS) $< -o $@

build/x86_64/%.o: src/impl/x86_64/%.asm
	mkdir -p $(dir $@) && \
	nasm -f elf64 $< -o $@

build/fatfs/%.o: src/lib/fatfs/%.c
	mkdir -p $(dir $@) && \
	$(CC) -c $(CFLAGS) $< -o $@

build/lib/%.o: src/lib/%.c
	mkdir -p $(dir $@) && \
	$(CC) -c $(CFLAGS) $< -o $@
	echo $(fatfs_source_files)
# Final build target
.PHONY: build-x86_64
build-x86_64: $(kernel_object_files) $(x86_64_c_object_files) $(x86_64_asm_object_files) $(fatfs_object_files) $(libc_object_files)
	mkdir -p dist/x86_64 && \
	x86_64-elf-ld -n -o dist/x86_64/kernel.bin -T targets/x86_64/linker.ld \
		$(kernel_object_files) \
		$(x86_64_c_object_files) \
		$(x86_64_asm_object_files) \
		$(fatfs_object_files) \
		$(libc_object_files) && \
	cp dist/x86_64/kernel.bin targets/x86_64/iso/boot/kernel.bin && \
	grub-mkrescue /usr/lib/grub/i386-pc -o dist/x86_64/kernel.iso targets/x86_64/iso

# Clean build artifacts
.PHONY: clean
clean:
	rm -rf build dist
