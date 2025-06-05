#include <stdint.h>
#include "ff.h"

// Return a fixed time or your RTC time if you have it
DWORD get_fattime(void) {
    return ((DWORD)(2024 - 1980) << 25)  // Year
         | ((DWORD)6 << 21)              // Month
         | ((DWORD)3 << 16)              // Day
         | ((DWORD)12 << 11)             // Hour
         | ((DWORD)0 << 5)               // Minute
         | ((DWORD)0 >> 1);              // Second / 2
}
