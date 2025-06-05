#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include "string.h"
#include "ff.h"
#include "diskio.h"

// --- Constants ---
#define INPUT_BUF_SIZE 256
#define VGA_WIDTH 320
#define VGA_HEIGHT 200

#define DISK_SECTOR_SIZE 512
#define DISK_SECTOR_COUNT 2048
#define DISK_SIZE (DISK_SECTOR_SIZE * DISK_SECTOR_COUNT)

// --- VGA buffer ---
static uint8_t *vga_buffer = (uint8_t *)0xA0000;

// --- Mock disk storage (replaces diskio.c) ---
static uint8_t mock_disk[DISK_SIZE];

// --- Low-level disk read/write implementation ---

// --- External console functions ---
extern void puts(const char* str);
extern void putchar(char c);
extern char keyboard_getchar(void);
extern void print_backspace(void);
extern void print_clear(void);
extern void print_str(const char* str);
extern void print_char(char c);

// --- VGA helpers ---
static inline void outb(uint16_t port, uint8_t val) {
    asm volatile ("outb %0, %1" : : "a"(val), "Nd"(port));
}
static inline uint8_t inb(uint16_t port) {
    uint8_t ret;
    asm volatile ("inb %1, %0" : "=a"(ret) : "Nd"(port));
    return ret;
}

void vga_set_palette() {
    outb(0x3C8, 0);
    for (int i = 0; i < 256; i++) {
        uint8_t val = i * 63 / 255;
        outb(0x3C9, val); outb(0x3C9, val); outb(0x3C9, val);
    }
}

void vga_set_mode_13h() {
    outb(0x3C2, 0x63);
    uint8_t seq[5] = {0x03, 0x01, 0x0F, 0x00, 0x0E};
    for (int i = 0; i < 5; i++) {
        outb(0x3C4, i); outb(0x3C5, seq[i]);
    }
    outb(0x3D4, 0x03); outb(0x3D5, inb(0x3D5) | 0x80);
    outb(0x3D4, 0x11); outb(0x3D5, inb(0x3D5) & ~0x80);
    uint8_t crtc[25] = {
        0x5F,0x4F,0x50,0x82,0x54,0x80,0xBF,0x1F,
        0x00,0x41,0x00,0x00,0x00,0x00,0x00,0x9C,
        0x0E,0x8F,0x28,0x40,0x96,0xB9,0xA3,0xFF,
        0x00
    };
    for (int i = 0; i < 25; i++) {
        outb(0x3D4, i); outb(0x3D5, crtc[i]);
    }
    uint8_t gc[9] = {0x00,0x00,0x00,0x00,0x00,0x40,0x05,0x0F,0xFF};
    for (int i = 0; i < 9; i++) {
        outb(0x3CE, i); outb(0x3CF, gc[i]);
    }
    uint8_t ac[21] = {
        0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,
        0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F,
        0x41,0x00,0x0F,0x00,0x00
    };
    (void)inb(0x3DA);
    for (int i = 0; i < 21; i++) {
        outb(0x3C0, i); outb(0x3C0, ac[i]);
    }
    outb(0x3C0, 0x20);
}

void vga_clear_screen(uint8_t color) {
    for (int i = 0; i < VGA_WIDTH * VGA_HEIGHT; i++) {
        vga_buffer[i] = color;
    }
}

// --- FatFS state ---
static FATFS fs;

// --- Utility ---

static int atoi_simple(const char *str) {
    int res = 0;
    while (*str >= '0' && *str <= '9') res = res * 10 + (*str++ - '0');
    return res;
}

// --- CLI file commands ---
void fatfs_init() {
    if (f_mount(&fs, "", 1) != FR_OK) {
        BYTE work[4096];
        MKFS_PARM opt = { .fmt = FM_FAT | FM_SFD, .n_fat = 1, .align = 0, .n_root = 0, .au_size = 0 };
        if (f_mkfs("", &opt, work, sizeof(work)) != FR_OK || f_mount(&fs, "", 1) != FR_OK) {
            puts("Failed to initialize FAT filesystem.");
            return;
        }
    }
    puts("FAT filesystem initialized.");
}

void save_file(const char* filename, const char* content) {
    FIL file;
    UINT bw;
    if (f_open(&file, filename, FA_WRITE | FA_CREATE_ALWAYS) == FR_OK) {
        f_write(&file, content, strlen(content), &bw);
        f_close(&file);
        puts("File saved.");
    } else puts("Error saving file.");
}

void read_file(const char* filename) {
    FIL file;
    char buf[128];
    UINT br;
    if (f_open(&file, filename, FA_READ) == FR_OK) {
        while (f_read(&file, buf, sizeof(buf)-1, &br) == FR_OK && br > 0) {
            buf[br] = 0;
            puts(buf);
        }
        f_close(&file);
    } else puts("Error reading file.");
}

void list_files() {
    DIR dir; FILINFO fno;
    if (f_opendir(&dir, "/") == FR_OK) {
        while (f_readdir(&dir, &fno) == FR_OK && fno.fname[0]) {
            puts(fno.fname);
        }
        f_closedir(&dir);
    } else puts("Failed to list files.");
}

// --- Help ---
void print_help() {
    puts("Available commands:");
    puts("  hello <text>           - Echo text");
    puts("  /art                   - Display ASCII art");
    puts("  /clear                 - Clear the screen");
    puts("  /gfxmode, /gfxclear    - VGA graphics mode");
    puts("  /calc <expr>           - Simple math");
    puts("  /diskread <sector>     - Read disk sector");
    puts("  /diskwrite <s> <data>  - Write to disk");
    puts("  /fsinit                - Init FAT FS");
    puts("  /savefile <f> <text>   - Save file");
    puts("  /readfile <f>          - Read file");
    puts("  /ls                    - List files");
}

// --- Command interpreter ---
void command_line_loop() {
    char input[INPUT_BUF_SIZE];
    size_t len = 0;
    bool vga_mode_active = false;

    puts("Welcome to mini-kernel CLI!");
    print_help();
    print_str("> ");

    while (1) {
        char c = keyboard_getchar();
        if (!c) continue;

        if (c == '\b') {
            if (len > 0) { len--; print_backspace(); }
        } else if (c == '\n' || c == '\r') {
            input[len] = '\0';
            print_char('\n');

            if (strncmp(input, "hello ", 6) == 0) puts(input + 6);
            else if (strncmp(input, "/art", 4) == 0) {
                puts("   /\\_/\\  ");
                puts("  ( o.o ) ");
                puts("   > ^ <  ");
            } else if (strncmp(input, "/clear", 6) == 0) print_clear();
            else if (strncmp(input, "/help", 5) == 0) print_help();
            else if (strncmp(input, "/gfxmode", 8) == 0) {
                vga_set_mode_13h(); vga_set_palette(); vga_clear_screen(0);
                vga_mode_active = true;
                puts("Graphics mode enabled.");
            } else if (strncmp(input, "/gfxclear", 9) == 0) {
                if (vga_mode_active) { vga_clear_screen(0); puts("Graphics cleared."); }
                else puts("Not in graphics mode.");
            } else if (strncmp(input, "/calc ", 6) == 0) {
                int a = 0, b = 0; char op; sscanf(input + 6, "%d %c %d", &a, &op, &b);
                int r = 0;
                switch (op) {
                    case '+': r = a + b; break;
                    case '-': r = a - b; break;
                    case '*': r = a * b; break;
                    case '/': r = b ? a / b : 0; break;
                    default: puts("Bad op."); r = 0;
                }
                char buf[32]; snprintf(buf, sizeof(buf), "%d", r); puts(buf);
            } else if (strncmp(input, "/diskread ", 10) == 0) {
                int sec = atoi_simple(input + 10);
                if (sec >= 0 && sec < DISK_SECTOR_COUNT) {
                    uint8_t buf[DISK_SECTOR_SIZE];
                    if (os_disk_read(0, buf, sec, 1) == 0) {
                        for (int i = 0; i < DISK_SECTOR_SIZE; i++) {
                            putchar((buf[i] >= 32 && buf[i] < 127) ? buf[i] : '.');
                            if ((i+1)%64 == 0) puts("");
                        }
                    } else puts("Disk read error.");
                } else puts("Invalid sector.");
            } else if (strncmp(input, "/diskwrite ", 11) == 0) {
                char *ptr = input + 11;
                int sec = atoi_simple(ptr);
                while (*ptr >= '0' && *ptr <= '9') ptr++;
                while (*ptr == ' ') ptr++;
                uint8_t buf[DISK_SECTOR_SIZE] = {0};
                strncpy((char*)buf, ptr, DISK_SECTOR_SIZE);
                if (os_disk_write(0, buf, sec, 1) == 0) puts("Sector written.");
                else puts("Disk write error.");
            } else if (strncmp(input, "/fsinit", 7) == 0) fatfs_init();
            else if (strncmp(input, "/savefile ", 10) == 0) {
                char *ptr = input + 10, *filename = ptr;
                while (*ptr && *ptr != ' ') ptr++;
                if (*ptr == '\0') puts("Missing filename or text.");
                else {
                    *ptr++ = '\0';
                    while (*ptr == ' ') ptr++;
                    save_file(filename, ptr);
                }
            } else if (strncmp(input, "/readfile ", 10) == 0) read_file(input + 10);
            else if (strncmp(input, "/ls", 3) == 0) list_files();
            else puts("Unknown command.");

            len = 0;
            print_str("> ");
        } else if (len < INPUT_BUF_SIZE - 1) {
            input[len++] = c;
            putchar(c);
        }
    }
}

// --- Entry point ---
void kernel_main(void) {
    command_line_loop();
}
