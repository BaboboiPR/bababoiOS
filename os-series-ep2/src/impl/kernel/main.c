#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#define INPUT_BUF_SIZE 256
#define VGA_WIDTH 320
#define VGA_HEIGHT 200

static uint8_t *vga_buffer = (uint8_t *)0xA0000;

static inline int abs(int x) {
    return x < 0 ? -x : x;
}

static inline void outb(uint16_t port, uint8_t val) {
    asm volatile ("outb %0, %1" : : "a"(val), "Nd"(port));
}

static inline uint8_t inb(uint16_t port) {
    uint8_t ret;
    asm volatile ("inb %1, %0" : "=a"(ret) : "Nd"(port));
    return ret;
}

// VGA palette
void vga_set_palette() {
    outb(0x3C8, 0);
    for (int i = 0; i < 256; i++) {
        uint8_t val = i * 63 / 255;
        outb(0x3C9, val);
        outb(0x3C9, val);
        outb(0x3C9, val);
    }
}

// VGA mode 13h (320x200, 256 colors)
void vga_set_mode_13h() {
    outb(0x3C2, 0x63);
    uint8_t seq[5] = {0x03, 0x01, 0x0F, 0x00, 0x0E};
    for (int i = 0; i < 5; i++) {
        outb(0x3C4, i);
        outb(0x3C5, seq[i]);
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
        outb(0x3D4, i);
        outb(0x3D5, crtc[i]);
    }

    uint8_t gc[9] = {0x00,0x00,0x00,0x00,0x00,0x40,0x05,0x0F,0xFF};
    for (int i = 0; i < 9; i++) {
        outb(0x3CE, i);
        outb(0x3CF, gc[i]);
    }

    uint8_t ac[21] = {
        0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,
        0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F,
        0x41,0x00,0x0F,0x00,0x00
    };
    (void)inb(0x3DA);
    for (int i = 0; i < 21; i++) {
        outb(0x3C0, i);
        outb(0x3C0, ac[i]);
    }
    outb(0x3C0, 0x20);
}

void vga_clear_screen(uint8_t color) {
    for (int i = 0; i < VGA_WIDTH * VGA_HEIGHT; i++) {
        vga_buffer[i] = color;
    }
}

// External stub functions
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
    puts("  /calc <expr>  - Evaluate math (e.g., 3+4, 10-5, 6*7, 20/4)");
}

int eval_expr(const char* expr) {
    int a = 0, b = 0;
    char op = 0;
    while (*expr == ' ') expr++;
    while (*expr >= '0' && *expr <= '9') a = a * 10 + (*expr++ - '0');
    while (*expr == ' ') expr++;
    op = *expr++;
    while (*expr == ' ') expr++;
    while (*expr >= '0' && *expr <= '9') b = b * 10 + (*expr++ - '0');

    switch (op) {
        case '+': return a + b;
        case '-': return a - b;
        case '*': return a * b;
        case '/': return (b != 0) ? a / b : 0;
        default:  return 0;
    }
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
    puts("Type `/calc 3+4` for calculator.");
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
            } else if (strncmp(input_buffer, "/calc ", 6) == 0) {
                int result = eval_expr(input_buffer + 6);
                char output[32];
                int len = 0;
                bool negative = false;

                if (result < 0) {
                    negative = true;
                    result = -result;
                }

                do {
                    output[len++] = '0' + (result % 10);
                    result /= 10;
                } while (result > 0);

                if (negative) output[len++] = '-';

                for (int i = 0; i < len / 2; i++) {
                    char tmp = output[i];
                    output[i] = output[len - 1 - i];
                    output[len - 1 - i] = tmp;
                }

                output[len] = '\0';
                puts(output);
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
