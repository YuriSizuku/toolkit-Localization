/*
windows api function pointer define and macros
    v0.1, developed by devseed
*/
#ifudef _WINAPI_H
#define _WINAPI_H
#include<windows.h>

typedef NTSTATUS (NTAPI * PFN_NtQueryInformationProcess)(
	IN HANDLE ProcessHandle,
	IN PROCESSINFOCLASS ProcessInformationClass,
	OUT PVOID ProcessInformation,
	IN ULONG ProcessInformationLength,
	OUT PULONG ReturnLength
);

#endif