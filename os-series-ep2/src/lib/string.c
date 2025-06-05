#include "string.h"
#include <stdarg.h>

static int sscanf_internal(const char *str, int *a, char *op, int *b, int *offset);
static int sscanf_int(const char *str, int *value, int *read_chars);

void *memcpy(void *dest, const void *src, size_t n) {
    char *d = dest;
    const char *s = src;
    while (n--) *d++ = *s++;
    return dest;
}

int strncmp(const char *s1, const char *s2, size_t n) {
    for (size_t i = 0; i < n; i++) {
        if (s1[i] != s2[i] || s1[i] == '\0' || s2[i] == '\0')
            return (unsigned char)s1[i] - (unsigned char)s2[i];
    }
    return 0;
}

void *memset(void *s, int c, size_t n) {
    unsigned char *p = s;
    while (n--) *p++ = (unsigned char)c;
    return s;
}

size_t strlen(const char *s) {
    size_t len = 0;
    while (*s++) len++;
    return len;
}

int strcmp(const char *s1, const char *s2) {
    while (*s1 && (*s1 == *s2)) {
        s1++; s2++;
    }
    return *(const unsigned char *)s1 - *(const unsigned char *)s2;
}

char *strcpy(char *dest, const char *src) {
    char *ret = dest;
    while ((*dest++ = *src++));
    return ret;
}

char *strncpy(char *dest, const char *src, size_t n) {
    size_t i;
    for (i = 0; i < n && src[i]; i++) {
        dest[i] = src[i];
    }
    for (; i < n; i++) {
        dest[i] = '\0';
    }
    return dest;
}

static int int_to_str(int value, char *str, size_t size) {
    char buffer[16];
    int i = 0, j;
    int negative = 0;
    if (value < 0) {
        negative = 1;
        value = -value;
    }
    do {
        buffer[i++] = '0' + (value % 10);
        value /= 10;
    } while (value && i < 15);
    if (negative)
        buffer[i++] = '-';

    int len = (i < (int)size - 1) ? i : (int)size - 1;
    for (j = 0; j < len; j++) {
        str[j] = buffer[i - j - 1];
    }
    str[len] = '\0';
    return len;
}

int snprintf(char *str, size_t size, const char *format, ...) {
    va_list args;
    va_start(args, format);
    size_t pos = 0;
    for (size_t i = 0; format[i] && pos < size - 1; i++) {
        if (format[i] == '%') {
            i++;
            if (format[i] == 'd') {
                int val = va_arg(args, int);
                char buf[16];
                int len = int_to_str(val, buf, sizeof(buf));
                for (int j = 0; j < len && pos < size - 1; j++) {
                    str[pos++] = buf[j];
                }
            } else {
                str[pos++] = '%';
                if (pos < size - 1) {
                    str[pos++] = format[i];
                }
            }
        } else {
            str[pos++] = format[i];
        }
    }
    str[pos] = '\0';
    va_end(args);
    return pos;
}

int sscanf(const char *str, const char *format, ...) {
    va_list args;
    va_start(args, format);

    int a, b;
    char op;
    int matched = 0;

    if (format[0] == '%' && format[1] == 'd' && format[2] == ' ' &&
        format[3] == '%' && format[4] == 'c' && format[5] == ' ' &&
        format[6] == '%' && format[7] == 'd') {

        int offset = 0;
        int res = sscanf_internal(str, &a, &op, &b, &offset);
        if (res == 3) {
            int *pa = va_arg(args, int*);
            char *pop = va_arg(args, char*);
            int *pb = va_arg(args, int*);
            *pa = a;
            *pop = op;
            *pb = b;
            matched = 3;
        }
    }

    va_end(args);
    return matched;
}

static int sscanf_internal(const char *str, int *a, char *op, int *b, int *offset) {
    const char *start = str;
    while (*str == ' ') str++;
    int n = 0;
    if (!sscanf_int(str, a, &n)) return 0;
    str += n;
    while (*str == ' ') str++;
    *op = *str;
    str++;
    while (*str == ' ') str++;
    int n2 = 0;
    if (!sscanf_int(str, b, &n2)) return 0;
    str += n2;
    *offset = (int)(str - start);
    return 3;
}

static int sscanf_int(const char *str, int *value, int *read_chars) {
    int val = 0;
    int i = 0;
    int negative = 0;
    if (str[i] == '-') {
        negative = 1;
        i++;
    }
    if (str[i] < '0' || str[i] > '9')
        return 0;
    while (str[i] >= '0' && str[i] <= '9') {
        val = val * 10 + (str[i] - '0');
        i++;
    }
    *read_chars = i;
    *value = negative ? -val : val;
    return 1;
}
