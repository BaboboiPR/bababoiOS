void kernel_main() {
    volatile char *video = (volatile char*) 0xB8000;
    const char *msg = "Hello from 64-bit Python OS with Multiboot2!";
    for (int i = 0; msg[i] != 0; i++) {
        video[i * 2] = msg[i];
        video[i * 2 + 1] = 0x07;
    }

    while (1); // halt
}
