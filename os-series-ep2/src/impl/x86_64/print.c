#include "print.h"

const static size_t NUM_COLS = 80;
const static size_t NUM_ROWS = 25;

struct Char {
    uint8_t character;
    uint8_t color;
};

struct Char* buffer = (struct Char*) 0xb8000;
size_t col = 0;
size_t row = 0;
uint8_t color = PRINT_COLOR_WHITE | PRINT_COLOR_BLACK << 4;

// Correct outb function
static inline void outb(uint16_t port, uint8_t val) {
    asm volatile ("outb %0, %1" : : "a"(val), "Nd"(port));
}

// Internal function to update the hardware cursor
static void update_hardware_cursor() {
    uint16_t pos = row * NUM_COLS + col;

    outb(0x3D4, 0x0F);
    outb(0x3D5, (uint8_t)(pos & 0xFF));
    outb(0x3D4, 0x0E);
    outb(0x3D5, (uint8_t)((pos >> 8) & 0xFF));
}

void clear_row(size_t row) {
    struct Char empty = {
        .character = ' ',
        .color = color,
    };

    for (size_t col = 0; col < NUM_COLS; col++) {
        buffer[col + NUM_COLS * row] = empty;
    }
}

void print_clear() {
    for (size_t i = 0; i < NUM_ROWS; i++) {
        clear_row(i);
    }
    col = 0;
    row = 0;
    update_hardware_cursor();
}

void print_newline() {
    col = 0;

    if (row < NUM_ROWS - 1) {
        row++;
    } else {
        // Scroll up
        for (size_t r = 1; r < NUM_ROWS; r++) {
            for (size_t c = 0; c < NUM_COLS; c++) {
                buffer[c + NUM_COLS * (r - 1)] = buffer[c + NUM_COLS * r];
            }
        }
        clear_row(NUM_ROWS - 1);
    }

    update_hardware_cursor();
}

void print_char(char character) {
    if (character == '\n') {
        print_newline();
        return;
    }

    if (col >= NUM_COLS) {
        print_newline();
    }

    buffer[col + NUM_COLS * row] = (struct Char) {
        .character = (uint8_t)character,
        .color = color,
    };

    col++;
    update_hardware_cursor();
}

void print_str(char* str) {
    for (size_t i = 0; str[i] != '\0'; i++) {
        print_char(str[i]);
    }
}

void print_set_color(uint8_t foreground, uint8_t background) {
    color = foreground + (background << 4);
}

void putchar(char c) {
    print_char(c);
}

void puts(const char* str) {
    while (*str) {
        putchar(*str++);
    }
    putchar('\n');
}

// === BACKSPACE SUPPORT ===
void print_backspace() {
    if (col == 0 && row == 0) {
        return; // Nothing to backspace
    }

    if (col == 0) {
        row--;
        col = NUM_COLS - 1;
    } else {
        col--;
    }

    buffer[col + NUM_COLS * row] = (struct Char) {
        .character = ' ',
        .color = color,
    };

    update_hardware_cursor();
}