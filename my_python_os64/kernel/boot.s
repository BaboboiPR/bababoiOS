section .multiboot align=8
    dd 0xE85250D6          ; magic number
    dd 0                   ; architecture (0 = i386)
    dd header_end - header ; total header length
    dd -(0xE85250D6 + 0 + (header_end - header)) ; checksum

header:
    dd 4       ; tag type = 4 (Framebuffer info request)
    dd 8       ; tag size
    dd 0       ; framebuffer type - 0 means all
    dd 0       ; padding

    dd 0       ; end tag type
    dd 8       ; end tag size

header_end:
