#include <assert.h>
#include <stdint.h>
#include <Windows.h>
#define WINPE_IMPLEMENTATION
#define WINPE_NOASM
#include "winpe.h"

void test_findexpcrc()
{
	HMODULE kernel32 = (HMODULE)winpe_findkernel32();
	assert(GetModuleHandleA("kernel32") == kernel32);
	uint32_t LoadLibraryA_crc32 = _winpeinl_crc32("LoadLibraryA", 12);
	assert(LoadLibraryA_crc32 == 0x3fc1bd8d);
	assert(winpe_memfindexpcrc32(kernel32, LoadLibraryA_crc32)
		== GetProcAddress(kernel32, "LoadLibraryA"));
}

void test_getfunc(HMODULE hmod, const char* funcname)
{
	size_t expva = (size_t)GetProcAddress(hmod, funcname);
	size_t exprva = (size_t)winpe_memfindexp(hmod, funcname) - (size_t)hmod;
	void* func2 = winpe_memGetProcAddress(hmod, funcname);
	assert(exprva != 0  && func2 == expva);
	printf("test_getfunc %p %s passed!\n", hmod, funcname);
}

int main(int argc, char* argv[])
{
	test_getfunc(LoadLibraryA("kernel32.dll"), "GetProcessMitigationPolicy");
	test_findexpcrc();
	return 0;
}