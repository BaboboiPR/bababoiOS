// heap.c
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#define HEAP_SIZE (1024 * 1024)  // 1 MB heap

static uint8_t heap[HEAP_SIZE];

typedef struct block_header {
    size_t size;              // Size of the block excluding header
    bool free;                // Is this block free?
    struct block_header* next;
} block_header_t;

static block_header_t* free_list = NULL;
static uint8_t* heap_end = heap;

static const size_t header_size = sizeof(block_header_t);

// Align size up to multiple of align (power of two)
static size_t align_up(size_t size, size_t align) {
    return (size + align - 1) & ~(align - 1);
}

void* kmalloc(size_t size) {
    size = align_up(size, 8);  // Align to 8 bytes

    // First, try to find a free block large enough
    block_header_t** current = &free_list;
    while (*current) {
        if ((*current)->free && (*current)->size >= size) {
            (*current)->free = false;
            return (void*)((uint8_t*)(*current) + header_size);
        }
        current = &((*current)->next);
    }

    // No suitable free block found, allocate new block if there is space
    if ((heap_end + header_size + size) > (heap + HEAP_SIZE)) {
        // Out of memory
        return NULL;
    }

    block_header_t* block = (block_header_t*)heap_end;
    block->size = size;
    block->free = false;
    block->next = NULL;

    heap_end += header_size + size;

    // Add block to free list (not free, but to track allocations)
    if (free_list == NULL) {
        free_list = block;
    } else {
        // Append to end of list
        block_header_t* temp = free_list;
        while (temp->next) {
            temp = temp->next;
        }
        temp->next = block;
    }

    return (void*)(block + 1); // Return pointer after header
}

void kfree(void* ptr) {
    if (!ptr) return;

    block_header_t* block = (block_header_t*)ptr - 1;
    block->free = true;

    // Optional: coalesce adjacent free blocks (not implemented here)
}
