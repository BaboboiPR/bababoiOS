#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

static inline int abs(int x) {
    return x < 0 ? -x : x;
}

// VGA ports for mode setting
#define VGA_MISC_WRITE 0x3C2
#define VGA_SEQ_INDEX 0x3C4
#define VGA_SEQ_DATA 0x3C5
#define VGA_CRTC_INDEX 0x3D4
#define VGA_CRTC_DATA 0x3D5
#define VGA_GC_INDEX 0x3CE
#define VGA_GC_DATA 0x3CF
#define VGA_AC_INDEX 0x3C0
#define VGA_AC_WRITE 0x3C0
#define VGA_INSTAT_READ 0x3DA

#define INPUT_BUF_SIZE 256
#define VGA_WIDTH 320
#define VGA_HEIGHT 200

static inline void outb(uint16_t port, uint8_t val) {
    asm volatile ("outb %0, %1" : : "a"(val), "Nd"(port));
}

static inline uint8_t inb(uint16_t port) {
    uint8_t ret;
    asm volatile ("inb %1, %0" : "=a"(ret) : "Nd"(port));
    return ret;
}

// Set a simple grayscale palette (256 colors)
void vga_set_palette() {
    outb(0x3C8, 0); // Start at palette index 0
    for (int i = 0; i < 256; i++) {
        uint8_t val = i * 63 / 255;  // scale 0..255 to 0..63 for VGA DAC
        outb(0x3C9, val); // Red
        outb(0x3C9, val); // Green
        outb(0x3C9, val); // Blue
    }
}

// VGA buffer pointer for mode 13h
static uint8_t *vga_buffer = (uint8_t *)0xA0000;

// Set VGA mode 13h (320x200, 256 colors) via port programming
void vga_set_mode_13h() {
    // Misc Output
    outb(VGA_MISC_WRITE, 0x63);

    // Sequencer Registers
    uint8_t seq_regs[5] = {0x03, 0x01, 0x0F, 0x00, 0x0E};
    for (int i = 0; i < 5; i++) {
        outb(VGA_SEQ_INDEX, i);
        outb(VGA_SEQ_DATA, seq_regs[i]);
    }

    // Unlock CRTC Registers 0-7
    outb(VGA_CRTC_INDEX, 0x03);
    outb(VGA_CRTC_DATA, inb(VGA_CRTC_DATA) | 0x80);
    outb(VGA_CRTC_INDEX, 0x11);
    outb(VGA_CRTC_DATA, inb(VGA_CRTC_DATA) & ~0x80);

    // CRT Controller Registers (25)
    uint8_t crtc_regs[25] = {
        0x5F, 0x4F, 0x50, 0x82, 0x54, 0x80, 0xBF, 0x1F,
        0x00, 0x41, 0x00, 0x00, 0x00, 0x00, 0x00, 0x9C,
        0x0E, 0x8F, 0x28, 0x40, 0x96, 0xB9, 0xA3, 0xFF,
        0x00
    };
    for (int i = 0; i < 25; i++) {
        outb(VGA_CRTC_INDEX, i);
        outb(VGA_CRTC_DATA, crtc_regs[i]);
    }

    // Graphics Controller Registers (9)
    uint8_t gc_regs[9] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x40, 0x05, 0x0F, 0xFF};
    for (int i = 0; i < 9; i++) {
        outb(VGA_GC_INDEX, i);
        outb(VGA_GC_DATA, gc_regs[i]);
    }

    // Attribute Controller Registers (21)
    uint8_t ac_regs[21] = {
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
        0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
        0x41, 0x00, 0x0F, 0x00, 0x00
    };

    (void)inb(VGA_INSTAT_READ); // reset flip-flop

    for (int i = 0; i < 21; i++) {
        outb(VGA_AC_INDEX, i);
        outb(VGA_AC_WRITE, ac_regs[i]);
    }

    outb(VGA_AC_INDEX, 0x20); // enable video output
}

// Clear the VGA screen with a given color
void vga_clear_screen(uint8_t color) {
    for (int i = 0; i < VGA_WIDTH * VGA_HEIGHT; i++) {
        vga_buffer[i] = color;
    }
}


// Bresenham's line drawing algorithm
void draw_line(int x0, int y0, int x1, int y1, uint8_t color) {
    int dx = abs(x1 - x0);
    int dy = abs(y1 - y0);
    int sx = (x0 < x1) ? 1 : -1;
    int sy = (y0 < y1) ? 1 : -1;
    int err = dx - dy;
    int e2;

    while (true) {
        if (x0 >= 0 && x0 < VGA_WIDTH && y0 >= 0 && y0 < VGA_HEIGHT)
            vga_buffer[y0 * VGA_WIDTH + x0] = color;

        if (x0 == x1 && y0 == y1) break;

        e2 = 2 * err;
        if (e2 > -dy) {
            err -= dy;
            x0 += sx;
        }
        if (e2 < dx) {
            err += dx;
            y0 += sy;
        }
    }
}

// Draw a simple cube wireframe in 2D screen space
void draw_simple_cube() {
    int cube_points[8][2] = {
        {120, 70},   {200, 70},   {200, 130},  {120, 130},
        {140, 90},   {220, 90},   {220, 150},  {140, 150}
    };

    int edges[12][2] = {
        {0,1},{1,2},{2,3},{3,0},
        {4,5},{5,6},{6,7},{7,4},
        {0,4},{1,5},{2,6},{3,7}
    };

    for (int i = 0; i < 12; i++) {
        int p1 = edges[i][0];
        int p2 = edges[i][1];
        draw_line(cube_points[p1][0], cube_points[p1][1], cube_points[p2][0], cube_points[p2][1], 4);
    }
}

// Stub functions for printing and keyboard input (replace with your own implementations)
extern void puts(const char* str);
extern void putchar(char c);
extern char keyboard_getchar(void);
extern void print_backspace(void);
extern void print_clear(void);
extern void print_str(const char* str);
extern void print_char(char c);

int strncmp(const char *s1, const char *s2, size_t n) {
    for (size_t i = 0; i < n; i++) {
        if (s1[i] != s2[i] || s1[i] == '\0' || s2[i] == '\0')
            return (unsigned char)s1[i] - (unsigned char)s2[i];
    }
    return 0;
}

void print_help() {
    puts("Available commands:");
    puts("  hello <text>  - Echo text");
    puts("  /art          - Display ASCII art");
    puts("  /clear        - Clear the screen");
    puts("  /help         - Show this help message");
    puts("  /shutdown     - Shutdown the machine");
    puts("  /restart      - Restart the machine");
    puts("  /gfxmode      - Switch to VGA 320x200 mode");
    puts("  /gfxclear     - Clear graphics screen");
    puts("  /cube         - Draw a simple red cube wireframe");
}

void command_line_loop() {
    char input_buffer[INPUT_BUF_SIZE];
    size_t input_len = 0;

    bool vga_mode_active = false;

    puts("Welcome to mini-kernel CLI!");
    puts("Type `hello your text` to echo.");
    puts("Type `/art` to see ASCII art.");
    puts("Type `/clear` to clear the screen.");
    puts("Type `/help` for help.");
    puts("Type `/shutdown` or `/restart` for power control.");
    puts("Type `/gfxmode` to enter VGA 320x200 graphics mode.");
    puts("Type `/gfxclear` to clear graphics screen.");
    puts("Type `/cube` to draw a simple red cube wireframe.");
    puts("Press Enter to run.\n");
    print_str("> ");

    while (1) {
        char c = keyboard_getchar();
        if (c == 0) continue;

        if (c == '\b') {
            if (input_len > 0) {
                input_len--;
                print_backspace();
            }
        } else if (c == '\n' || c == '\r') {
            input_buffer[input_len] = '\0';
            print_char('\n');

            if (strncmp(input_buffer, "hello ", 6) == 0) {
                puts(input_buffer + 6);
            } else if (strncmp(input_buffer, "/art", 4) == 0) {
                puts("   /\\_/\\  ");
                puts("  ( o.o ) ");
                puts("   > ^ <  ");
            } else if (strncmp(input_buffer, "/clear", 6) == 0) {
                print_clear();
            } else if (strncmp(input_buffer, "/help", 5) == 0) {
                print_help();
            } else if (strncmp(input_buffer, "/gfxmode", 8) == 0) {
                vga_set_mode_13h();
                vga_set_palette();
                vga_clear_screen(0);
                vga_mode_active = true;
                puts("Switched to VGA mode 13h.");
            } else if (strncmp(input_buffer, "/gfxclear", 9) == 0) {
                if (vga_mode_active) {
                    vga_clear_screen(0);
                    puts("Graphics screen cleared.");
                } else {
                    puts("Graphics mode not active.");
                }
            } else if (strncmp(input_buffer, "/cube", 5) == 0) {
                if (!vga_mode_active) {
                    vga_set_mode_13h();
                    vga_set_palette();
                    vga_clear_screen(0);
                    vga_mode_active = true;
                }
                draw_simple_cube();
                puts("Drew simple cube wireframe in VGA mode.");
            } else {
                puts("Unknown command.");
            }

            input_len = 0;
            print_str("> ");
        } else {
            if (input_len < INPUT_BUF_SIZE - 1) {
                input_buffer[input_len++] = c;
                putchar(c);
            }
        }
    }
}

void kernel_main(void) {
    command_line_loop();
}
