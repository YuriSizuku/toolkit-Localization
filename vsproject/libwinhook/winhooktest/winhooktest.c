#define WINHOOK_IMPLEMENTATION
#define WINHOOK_NODETOURS
#include "winhook.h"

void test_searchpattern()
{
	char* str = "\x20\x21\x22\x34\x22\x33\x44\x00";
	char* pattern = "22 34??3?\0";
	size_t matchsize = 0;
	void *matchaddr = winhook_searchmemory(str, sizeof(str), pattern, &matchsize);
	printf("test_searchpattern matchaddr=%p, matchsize=%d", matchaddr, matchsize);
}

int main(int argc, char *argv[])
{
	test_searchpattern();
	return 0;
}