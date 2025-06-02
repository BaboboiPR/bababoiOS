// heap.c
#include <stddef.h>
#include <stdint.h>

#define HEAP_SIZE 1024 * 1024  // 1 MB heap
static uint8_t heap[HEAP_SIZE];
static size_t heap_index = 0;

void* kmalloc(size_t size) {
    if (heap_index + size > HEAP_SIZE) {
        return NULL; // Out of memory
    }

    void* ptr = &heap[heap_index];
    heap_index += size;

    // Optionally align heap_index to 4/8 bytes
    return ptr;
}
