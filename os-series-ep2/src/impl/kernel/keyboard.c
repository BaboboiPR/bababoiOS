#include <stdint.h>
#include <stdbool.h>

#define KBD_DATA_PORT 0x60
#define KBD_STATUS_PORT 0x64

// ASCII map with unshifted and shifted values
static const char scancode_to_ascii[128] = {
    0,  27, '1','2','3','4','5','6','7','8','9','0','-','=','\b',
    '\t','q','w','e','r','t','y','u','i','o','p','[',']','\n',
    0, 'a','s','d','f','g','h','j','k','l',';','\'','`',0, '\\',
    'z','x','c','v','b','n','m',',','.','/',0, '*',0, ' ', 0,
    // rest zeros...
};

static const char scancode_to_ascii_shift[128] = {
    0,  27, '!','@','#','$','%','^','&','*','(',')','_','+','\b',
    '\t','Q','W','E','R','T','Y','U','I','O','P','{','}','\n',
    0, 'A','S','D','F','G','H','J','K','L',':','"','~',0, '|',
    'Z','X','C','V','B','N','M','<','>','?',0, '*',0, ' ', 0,
    // rest zeros...
};

// Shift state tracking
static bool shift_pressed = false;

// Check if data is ready
static bool kbd_data_ready() {
    uint8_t status;
    asm volatile ("inb %1, %0" : "=a"(status) : "Nd"(KBD_STATUS_PORT));
    return status & 1;
}

// Read data from keyboard
static uint8_t kbd_read_data() {
    uint8_t data;
    asm volatile ("inb %1, %0" : "=a"(data) : "Nd"(KBD_DATA_PORT));
    return data;
}

// Get one character from keyboard
char keyboard_getchar() {
    uint8_t scancode;

    while (!kbd_data_ready());

    scancode = kbd_read_data();

    // Key released (ignore)
    if (scancode & 0x80) {
        uint8_t released = scancode & 0x7F;

        if (released == 0x2A || released == 0x36) { // Left or Right Shift
            shift_pressed = false;
        }

        return 0;
    }
    

    // Shift press
    if (scancode == 0x2A || scancode == 0x36) {
        shift_pressed = true;
        return 0;
    }

    char c = shift_pressed ? scancode_to_ascii_shift[scancode] : scancode_to_ascii[scancode];
    return c ? c : 0;
}
