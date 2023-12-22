/**
 * A flexible format and low memory use implementation 
 * for general dynamic localization
 *   v0.1.1, developed by devseed
 *    
 *  use ftextpack_index_t.py to generate data.fp01
 *  you can pack all the ftexts files in a folder to single data file
*/

#ifndef _FTEXTPACK_H
#define _FTEXTPACK_H
#include <stdint.h>
#include <stdio.h>

#define FTEXTPACK_VERSION 110

typedef struct _ftextpack_textinfo_t {
    union 
    {
        uint32_t hash; // crc32
        uint32_t extra; // user defined information
    };
    uint32_t offset; // offset in pack
    uint32_t addr; // addr in script
    uint32_t size; // text size
}ftextpack_textinfo_t;

#ifdef FTEXTPACK_COMPACT
/**
 *  some trick to save index memory
 *  with memory overlap by union
*/
typedef struct _ftextpack_info_t {
    union {
    ftextpack_textinfo_t org;
    ftextpack_textinfo_t now;
    };
} ftextpack_info_t;
#else
typedef struct _ftextpack_info_t {
    ftextpack_textinfo_t org;
    ftextpack_textinfo_t now;
} ftextpack_info_t;
#endif

/**
 * use smaller memory for store index information
*/
typedef struct _ftextpack_textmap_t
{
    union
    {
        uint32_t value;
        uint32_t hash;
        uint32_t addr;
    };
    uint32_t offset;
}ftextpack_textmap_t;


typedef struct _ftextpack_map_t {
    union
    {
        ftextpack_textmap_t org;
        ftextpack_textmap_t now;
    };
}ftextpack_map_t;

typedef struct _ftextpack_index_t {
    char magic[4]; // FP01, LP01 fp for full info, lp for brief info
    uint32_t count; // text info count
    uint32_t offset; // text offset
    uint32_t reserved; 
    union 
    {
        ftextpack_info_t info[1];
        ftextpack_map_t map[1];
    };
}ftextpack_index_t;


/**
 * general crc32 method
*/
uint32_t ftextpack_crc32(const void *buf, int n);

/**
 * load index or index map (brief index) from file
 * @return whole index size 
*/
int ftextpack_loadindex(FILE *fp, void *outbuf, int bufsize);
int ftextpack_loadindexmap(FILE *fp, void *outbuf, int bufsize);

/**
 * directly load text from file to outbuf
 * the text should be end with \0
 * @param offset start from ftell, and it recover fp position
 * @return outtext size, error with 0
*/
int ftextpack_loadtext(FILE *fp, ftextpack_info_t *info, void *outbuf, int bufsize);

/**
 * search the index by hash, it must be sorted by org hash
 * @return index of ftextpack_info_t, not find with -1
*/
int ftextpack_searchbyhash(ftextpack_index_t *index, uint32_t hash, int start);

/**
 * search the index by addr, it must be sorted by org addr
 * @return index of ftextpack_info_t, not find with -1
*/
int ftextpack_searchbyaddr(ftextpack_index_t *index, uint32_t addr, int start);

#ifdef FTEXTPACK_IMPLEMENT
uint32_t ftextpack_crc32(const void *buf, int n)
{
    uint32_t crc32 = ~0;
    for(int i=0; i< n; i++)
    {
        crc32 ^= *(const uint8_t*)((uint8_t*)buf+i);

        for(int i = 0; i < 8; i++)
        {
            uint32_t t = ~((crc32&1) - 1); 
            crc32 = (crc32>>1) ^ (0xEDB88320 & t);
        }
    }
    return ~crc32;
}

int ftextpack_loadindex(FILE *fp, void *outbuf, int bufsize)
{
    if(!fp) return 0;

    ftextpack_index_t *index = (ftextpack_index_t*)outbuf;
    uint8_t *cur = (uint8_t*)outbuf;
    if(bufsize < sizeof(ftextpack_index_t)) return 0;
    cur += sizeof(ftextpack_index_t) * fread(cur, sizeof(ftextpack_index_t), 1, fp);
    index->magic[0] = 'f';
    
    int n = index->count;
    int leftsize = bufsize - sizeof(ftextpack_index_t);
    int leftn = (n-1) * sizeof(ftextpack_info_t) < leftsize ? n-1 : leftsize/sizeof(ftextpack_info_t);
    cur += sizeof(ftextpack_info_t) * fread(cur, sizeof(ftextpack_info_t), leftn, fp);
    return (int)(cur - (uint8_t*)outbuf);
}

int ftextpack_loadindexmap(FILE *fp, void *outbuf, int bufsize)
{
    if(!fp) return 0;

    ftextpack_index_t *index = (ftextpack_index_t*)outbuf;
    ftextpack_map_t *map = index->map;
    ftextpack_info_t tmpinfo;
    
    uint8_t *cur = (uint8_t*)outbuf;
    if(bufsize < sizeof(ftextpack_index_t)) return 0;
    cur += sizeof(ftextpack_index_t) * fread(cur, sizeof(ftextpack_index_t), 1, fp);
    index->magic[0] = 'l';
    
    int n = index->count;
    int leftsize = bufsize - sizeof(ftextpack_index_t);
    int leftn = (n-1) * sizeof(ftextpack_map_t) < leftsize ? n -1 : leftsize/sizeof(ftextpack_map_t);
    
    memcpy(&tmpinfo, map, sizeof(tmpinfo));
    map->org.addr = tmpinfo.org.addr;
    map->now.offset = tmpinfo.now.offset;
    cur = (uint8_t*)&index->map[1];
    for(int i=0; i<leftn;i++)
    {
        fread(&tmpinfo, sizeof(ftextpack_info_t), 1, fp);
        map = (ftextpack_map_t *)cur;
        map->org.addr = tmpinfo.org.addr;
        map->now.offset = tmpinfo.now.offset;
        cur += sizeof(ftextpack_map_t);
    }
    return (int)(cur - (uint8_t*)outbuf);
}

int ftextpack_searchbyaddr(ftextpack_index_t *index, uint32_t addr, int start)
{
    if(!index) return -1;

    int mid = -1;
    int end = index->count;
    ftextpack_map_t* map = index->map;
    ftextpack_info_t* info =  index->info;
    //LOG("ftextpack_searchbyaddr: index=%p, addr=%x, start=%d, end=%d\n", index, addr, start, end)

    while (start<=end)
    {
        mid = (start + end) / 2;
        uint32_t addr_mid = index->magic[0] == 'l' ? map[mid].org.addr: info[mid].org.addr;
        // LOG("start=%d, end=%d, addr=%x, addr_mid=%x, index=%p, map[mid]=%p\n", 
        //     start, end, addr, addr_mid, index, &map[mid]);
        if(addr_mid > addr) end = mid - 1;
        else if(addr_mid < addr) start = mid + 1;
        else return mid;
    }
    return -1;
}

int ftextpack_loadtext(FILE *fp, ftextpack_info_t *info, void *outbuf, int bufsize)
{
    if(!fp) return 0;
    size_t offset = ftell(fp);
    
    int c;
    int pos = 0;
    
    fseek(fp, info->now.offset, SEEK_CUR);
    uint8_t* out = (uint8_t*)outbuf;
    while ((c=fgetc(fp))>0)
    {
        out[pos++] = (uint8_t)c;
        if(pos>=bufsize-1) break;
    }
    out[pos++] = 0;
    fseek(fp, offset, SEEK_SET);
    // LOG("%p, %x, %x, %d \n", info, offset, info->now.offset, pos);
    return pos;
}

#endif
#endif

/**
 * history:
 * v0.1, initial version with data.fp01
 * v0.1.1, add ftextpack_loadindexmap for smaller memory use
*/