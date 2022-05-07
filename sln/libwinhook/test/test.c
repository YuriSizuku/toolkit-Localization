#define WINHOOK_IMPLEMENTATION
#define WINHOOK_NODETOURS
#include "winhook.h"

void test_searchpattern()
{
	char* str = "\x20\x21\x22\x34\x22\x33\x44\x00";
	char* pattern = "22 34??3?\0";
	size_t matchsize = 0;
	void* matchaddr = NULL;
	matchaddr = winhook_searchmemory(str, strlen(str), pattern, &matchsize);
	printf("winhook_searchmemory matchaddr=%p, matchsize=%zx\n", matchaddr, matchsize);
	matchaddr = winhook_searchmemoryex(GetCurrentProcess(), str, strlen(str), pattern, &matchsize);
	printf("winhook_searchmemoryex matchaddr=%p, matchsize=%zx\n", matchaddr, matchsize);
}

void test_startexeinject()
{
	DWORD pid = winhook_startexeinject("hello.exe", NULL, "hello.dll");
}

int main(int argc, char *argv[])
{
	test_searchpattern();
	test_startexeinject();
	return 0;
}