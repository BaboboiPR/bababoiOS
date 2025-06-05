#include <stddef.h>
#include <stdint.h>
int memcmp(const void *s1, const void *s2, unsigned long n) {
    const unsigned char *a = s1, *b = s2;
    for (unsigned long i = 0; i < n; i++) {
        if (a[i] != b[i]) return a[i] - b[i];
    }
    return 0;
}
