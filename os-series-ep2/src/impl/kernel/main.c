#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include "string.h"
#include "print.h"

#define INPUT_BUF_SIZE 256

extern void putchar(char c);
extern void puts(const char* str);
extern char keyboard_getchar(void);
extern void print_backspace(void);
extern void print_clear(void);  // clears the screen

int strncmp(const char *s1, const char *s2, size_t n) {
    for (size_t i = 0; i < n; i++) {
        if (s1[i] != s2[i] || s1[i] == '\0' || s2[i] == '\0')
            return (unsigned char)s1[i] - (unsigned char)s2[i];
    }
    return 0;
}

void print_ascii_art() {
    puts("   /\\_/\\  ");
    puts("  ( o.o ) ");
    puts("   > ^ <  ");
}

void print_help() {
    puts("Available commands:");
    puts("  hello <text>  - Echo text");
    puts("  /art          - Display ASCII art");
    puts("  /clear        - Clear the screen");
    puts("  /help         - Show this help message");
}

void command_line_loop() {
    char input_buffer[INPUT_BUF_SIZE];
    size_t input_len = 0;

    puts("Welcome to mini-kernel CLI!");
    puts("Type `hello your text` to echo.");
    puts("Type `/art` to see ASCII art.");
    puts("Type `/clear` to clear the screen.");
    puts("Type `/help` for help.");
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
                puts(input_buffer + 6);  // Echo after 'hello '
            } else if (strncmp(input_buffer, "/art", 4) == 0) {
                print_ascii_art();
            } else if (strncmp(input_buffer, "/clear", 6) == 0) {
                print_clear();
            } else if (strncmp(input_buffer, "/help", 5) == 0) {
                print_help();
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
