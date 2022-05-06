#include <assert.h>
#include <Windows.h>
#define WINPE_IMPLEMENTATION
#define WINPE_NOASM
#include "winpe.h"

void test_winpe()
{
	HMODULE kernel32 = (HMODULE)winpe_findkernel32();
	assert(GetModuleHandleA("kernel32") == kernel32);
}

int main(int argc, char* argv[])
{
	test_winpe();
	return 0;
}