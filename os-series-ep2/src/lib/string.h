#ifndef STRING_H
#define STRING_H

#include <stddef.h>
#include <stdarg.h>  // for va_list in implementation

void *memcpy(void *dest, const void *src, size_t n);
void *memset(void *s, int c, size_t n);
size_t strlen(const char *s);
int strcmp(const char *s1, const char *s2);
char *strcpy(char *dest, const char *src);
char *strncpy(char *dest, const char *src, size_t n);

int snprintf(char *str, size_t size, const char *format, ...);  // variadic

int sscanf(const char *str, const char *format, ...);  // variadic

#endif
