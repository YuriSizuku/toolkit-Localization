#include <stdio.h>
#include <assert.h>

#define WINHOOK_IMPLEMENTATION
#define WINHOOK_NOINLINEHOOK
#define WINHOOK_USESHELLCODE
#include "winhook.h"

void test_patchpattern()
{
	printf("\n## test_patchpattern\n");
	char pattern[256];
	char tmp[256];
	uint8_t v1 = 1;
	uint32_t v2 = 2;
	int res = 0;

	printf("v1(%p)=%x v2(%p)=%x\n", &v1, v1, &v2, v2);
	strcpy(pattern, "# test winhook_patchmemorypattern\n");
	res = sprintf(tmp, "%p:ff\r\n", &v1);
	strcat(pattern, tmp);
	res = sprintf(tmp, "%p:12 ab ; %p :CD \n", &v2, (void*)((size_t)&v2+2));
	strcat(pattern, tmp);
	res = sprintf(tmp, "%p:09\r\n", (void*)((size_t)&v2 + 3));
	strcat(pattern, tmp);
	puts(pattern);
	res = winhook_patchmemorypattern(pattern);
	printf("v1(%p)=%x v2(%p)=%x\n", &v1, v1, &v2, v2);
	assert(res == 5);
	assert(v1 == 0xff);
	assert(v2 == 0x09cdab12);
}

void test_searchpattern()
{
	printf("\n## test_searchpattern\n");
	char target[] = "\x20\x21\x22\x34\x22\x33\x44\x00";
	char* pattern = "22 34??3?\0";
	size_t matchsize = 0;
	void* matchaddr = NULL;
	matchaddr = winhook_searchmemory(target, sizeof(target), pattern, &matchsize);
	printf("winhook_searchmemory matchaddr=%p, matchsize=0x%zx\n", matchaddr, matchsize);
	matchaddr = winhook_searchmemoryex(GetCurrentProcess(), target, sizeof(target), pattern, &matchsize);
	printf("winhook_searchmemoryex matchaddr=%p, matchsize=0x%zx\n", matchaddr, matchsize);
}

void test_searchpattern2()
{
	printf("\n## test_searchpattern2\n");
	char target[] = "\x8B\x4D\xF8\x83\x61\x70\xFD\xC9\xC3\x8B\xFF\x55\x8B\xEC\x6A\x04\x6A\x00\xFF\x75\x08\x6A\x00\xE8\x9A\xFF\xFF\xFF\x83\xC4\x10\x5D\x00";
	char* pattern = "55 8b ec 6a 04 6a 00 ff 75 08 6a 00 e8";
	size_t matchsize = 0;
	void* matchaddr = NULL;
	matchaddr = winhook_searchmemory(target, sizeof(target), pattern, &matchsize);
	printf("winhook_searchmemory matchaddr=%p, matchsize=0x%zx\n", matchaddr, matchsize);
	matchaddr = winhook_searchmemoryex(GetCurrentProcess(), target, sizeof(target), pattern, &matchsize);
	printf("winhook_searchmemoryex matchaddr=%p, matchsize=0x%zx\n", matchaddr, matchsize);
}

void test_startexeinject()
{
	printf("\n## test_startexeinject\n");
	DWORD pid = winhook_startexeinject("hello.exe", NULL, "hello.dll");
}

void test_windyn()
{
#ifdef WINDYN_IMPLEMENTATION
#endif
}

int main(int argc, char *argv[])
{
	test_patchpattern();
	test_searchpattern();
	test_searchpattern2();
	test_startexeinject();
	test_windyn();
	return 0;
}