#include <assert.h>
#include <stdint.h>
#include <Windows.h>
#define WINPE_IMPLEMENTATION
#define WINPE_NOASM
#include "winpe.h"

void test_winpe()
{
	HMODULE kernel32 = (HMODULE)winpe_findkernel32();
	assert(GetModuleHandleA("kernel32") == kernel32);
	uint32_t LoadLibraryA_crc32 = _winpeinl_crc32("LoadLibraryA", 12);
	assert(LoadLibraryA_crc32 == 0x3fc1bd8d);
	assert(winpe_memfindexpcrc32(kernel32, LoadLibraryA_crc32)
		== GetProcAddress(kernel32, "LoadLibraryA"));
}

int main(int argc, char* argv[])
{
	test_winpe();
	return 0;
}