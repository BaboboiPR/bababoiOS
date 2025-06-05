#pragma once

#include <stdint.h>
#include <stddef.h>

static inline int abs(int x) {
    return x < 0 ? -x : x;
}

#define PI 3.14159265358979323846f


// Sine approximation
static float sinf(float x) {
    while (x > PI) x -= 2 * PI;
    while (x < -PI) x += 2 * PI;
    float x3 = x * x * x;
    return x - (x3 / 6.0f);
}

static float cosf(float x) {
    return sinf(x + PI / 2);
}

enum {
    PRINT_COLOR_BLACK = 0,
    PRINT_COLOR_BLUE,
    PRINT_COLOR_GREEN,
    PRINT_COLOR_CYAN,
    PRINT_COLOR_RED,
    PRINT_COLOR_MAGENTA,
    PRINT_COLOR_BROWN,
    PRINT_COLOR_LIGHT_GRAY,
    PRINT_COLOR_DARK_GRAY,
    PRINT_COLOR_LIGHT_BLUE,
    PRINT_COLOR_LIGHT_GREEN,
    PRINT_COLOR_LIGHT_CYAN,
    PRINT_COLOR_LIGHT_RED,
    PRINT_COLOR_PINK,
    PRINT_COLOR_YELLOW,
    PRINT_COLOR_WHITE,
};

void print_clear();
void print_char(char character);
void print_set_color(uint8_t foreground, uint8_t background);
void puts(const char* str);
void putchar(char c);
void print_backspace();

