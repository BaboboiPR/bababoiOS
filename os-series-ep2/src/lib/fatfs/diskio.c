#include "ff.h"
#include "diskio.h"
#include <stdint.h>
#include <string.h>

#define DISK_SECTOR_SIZE 512
#define DISK_SECTOR_COUNT 2048
#define DISK_SIZE (DISK_SECTOR_SIZE * DISK_SECTOR_COUNT)

// --- Mock disk storage ---
static uint8_t mock_disk[DISK_SIZE];

// --- Low-level disk read/write implementation for FatFS ---

int os_disk_read(uint8_t pdrv, uint8_t* buff, uint32_t sector, unsigned int count) {
    if (sector + count > DISK_SECTOR_COUNT || count == 0) return -1;
    memcpy(buff, &mock_disk[sector * DISK_SECTOR_SIZE], count * DISK_SECTOR_SIZE);
    return 0;
}

int os_disk_write(uint8_t pdrv, const uint8_t* buff, uint32_t sector, unsigned int count) {
    if (sector + count > DISK_SECTOR_COUNT || count == 0) return -1;
    memcpy(&mock_disk[sector * DISK_SECTOR_SIZE], buff, count * DISK_SECTOR_SIZE);
    return 0;
}

// --- FatFS disk interface functions ---

DSTATUS disk_initialize(BYTE pdrv) {
    (void)pdrv;
    return 0;
}

DSTATUS disk_status(BYTE pdrv) {
    (void)pdrv;
    return 0;
}

DRESULT disk_read(BYTE pdrv, BYTE* buff, LBA_t sector, UINT count) {
    return os_disk_read(pdrv, buff, sector, count) == 0 ? RES_OK : RES_ERROR;
}

DRESULT disk_write(BYTE pdrv, const BYTE* buff, LBA_t sector, UINT count) {
    return os_disk_write(pdrv, buff, sector, count) == 0 ? RES_OK : RES_ERROR;
}

DRESULT disk_ioctl(BYTE pdrv, BYTE cmd, void* buff) {
    switch (cmd) {
        case GET_SECTOR_COUNT:
            *(DWORD*)buff = DISK_SECTOR_COUNT;
            return RES_OK;
        case GET_SECTOR_SIZE:
            *(WORD*)buff = DISK_SECTOR_SIZE;
            return RES_OK;
        case GET_BLOCK_SIZE:
            *(DWORD*)buff = 1;
            return RES_OK;
        case CTRL_SYNC:
            return RES_OK;
        default:
            return RES_PARERR;
    }
}

// --- Main program ---

static FATFS fs;

int mount_and_format() {
    FRESULT res;

    res = f_mount(&fs, "", 1);
    if (res != FR_OK) {
        BYTE work[4096];

        MKFS_PARM opt = {
            .fmt = FM_FAT | FM_SFD,
            .n_fat = 1,
            .align = 0,
            .n_root = 0,
            .au_size = 0
        };

        res = f_mkfs("", &opt, work, sizeof(work));
        if (res != FR_OK) {
            return -1;
        }

        res = f_mount(&fs, "", 1);
        if (res != FR_OK) {
            return -1;
        }
    }

    return 0;
}

void save_file_example() {
    FIL file;
    FRESULT res;
    UINT bw;

    res = f_open(&file, "hello.txt", FA_WRITE | FA_CREATE_ALWAYS);
    if (res == FR_OK) {
        const char *text = "Hello, FatFS!\n";
        f_write(&file, text, strlen(text), &bw);
        f_close(&file);
    }
}

int main(void) {
    if (mount_and_format() != 0) {
        return -1;
    }

    save_file_example();

    return 0;
}
