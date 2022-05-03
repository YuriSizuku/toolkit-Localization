/*
windows dyamic hook util functions wrappers
    v0.2.5, developed by devseed
*/

#ifndef _WINHOOK_H
#define _WINHOOK_H
#include <Windows.h>

#ifndef WINHOOKDEF
#ifdef WINHOOK_STATIC
#define WINHOOKDEF static
#else
#define WINHOOKDEF extern
#endif
#endif

#ifndef WINHOOK_SHARED
#define WINHOOK_EXPORT
#else
#ifdef _WIN32
#define WINHOOK_EXPORT __declspec(dllexport)
#else
#define WINHOOK_EXPORT __attribute__((visibility("default")))
#endif
#endif

#ifdef __cplusplus
extern "C" {
#endif
// loader functions
/* 
    start a exe by CreateProcess
*/
WINHOOKDEF WINHOOK_EXPORT 
HANDLE winhook_startexe(LPCSTR exepath, LPSTR cmdstr);

/*
    get the process handle by exename
*/
WINHOOKDEF WINHOOK_EXPORT 
HANDLE winhook_getprocess(LPCWSTR exename); 

/*
    dynamic inject a dll into a process
 */ 
WINHOOKDEF WINHOOK_EXPORT 
BOOL winhook_injectdll(HANDLE hProcess, LPCSTR dllname); 

/*
    alloc a console for the program
*/
WINHOOKDEF WINHOOK_EXPORT 
void winhook_installconsole();


// dynamic hook functions
/*
    winhook_patchmemory, patch addr by buf with bufsize
*/
WINHOOKDEF WINHOOK_EXPORT 
BOOL winhook_patchmemory(LPVOID addr, 
    void* buf, size_t bufsize);

/*
    winhook_patchmemorys, batch patch memories
*/
WINHOOKDEF WINHOOK_EXPORT 
BOOL winhook_patchmemorys(LPVOID addrs[], 
    void* bufs[], size_t bufsizes[], int n);

/*
    winhook_searchpattern, search the pattern like "ab 12 ?? 34"
    return the matched address, matchend
*/
WINHOOKDEF WINHOOK_EXPORT
void* winhook_searchmemory(void* addr, size_t memsize, 
    const char* pattern, size_t *pmatchsize);

/* 
    winhook_iathookmodule is for windows dll, 
    moduleDllName is which dll to hook iat
*/
WINHOOKDEF WINHOOK_EXPORT 
BOOL winhook_iathookmodule(LPCSTR targetDllName, 
    LPCSTR moduleDllName, PROC pfnOrg, PROC pfnNew);

/*
    iat dynamiclly hook, 
    replace the pfgNew with pfnOrg function 
    in targetDllName, 
    winhook_iathook is for windows EXE, 
    targetDllName is like "user32.dll", "kernel32.dll"
*/
WINHOOKDEF WINHOOK_EXPORT 
BOOL winhook_iathook(LPCSTR targetDllName, 
    PROC pfnOrg, PROC pfgNew);

/*
    inline hooks wrapper, 
    pfnTargets -> pfnNews, save origin pointers in pfnOlds
*/
WINHOOKDEF WINHOOK_EXPORT
int winhook_inlinehooks(PVOID pfnTargets[], 
    PVOID pfnNews[], PVOID pfnOlds[], size_t n);

WINHOOKDEF WINHOOK_EXPORT
int winhook_inlineunhooks(PVOID pfnTargets[], 
    PVOID pfnNews[], PVOID pfnOlds[], size_t n);

#endif 

#ifdef __cplusplus
}
#endif

#ifdef WINHOOK_IMPLEMENTATION
#include <stdio.h>
#include <stdint.h>
#include <Windows.h>
#include <tlhelp32.h>

// loader functions
WINHOOKDEF WINHOOK_EXPORT 
HANDLE winhook_startexe(LPCSTR exepath, LPSTR cmdstr)
{
    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&pi, sizeof(pi));
    ZeroMemory(&si, sizeof(si));
    if (!CreateProcessA(exepath, cmdstr, 
        NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi))
        return NULL;
    return pi.hProcess;
}

WINHOOKDEF WINHOOK_EXPORT 
HANDLE winhook_getprocess(LPCWSTR exename)
{
    // Create toolhelp snapshot.
    DWORD pid = 0;
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    PROCESSENTRY32 process;
    ZeroMemory(&process, sizeof(process));
    process.dwSize = sizeof(process);

    // Walkthrough all processes.
    if (Process32First(snapshot, &process))
    {
        do
        {
            if (wcscmp((const wchar_t*)process.szExeFile, exename) == 0)
            {
                pid = process.th32ProcessID;
                break;
            }
        } while (Process32Next(snapshot, &process));
    }
    CloseHandle(snapshot);
    if (pid != 0) return OpenProcess(PROCESS_ALL_ACCESS, FALSE, pid);
    return NULL;     // Not found
}

WINHOOKDEF WINHOOK_EXPORT
BOOL winhook_injectdll(HANDLE hProcess, LPCSTR dllname)
{
    LPVOID param_addr = VirtualAllocEx(hProcess, 0, 0x100, MEM_COMMIT, PAGE_READWRITE);
    SIZE_T count;
    if (param_addr == NULL) return FALSE;
    WriteProcessMemory(hProcess, param_addr, dllname, strlen(dllname)+1, &count);

    HMODULE kernel32 = GetModuleHandleA("Kernel32");
    FARPROC pfnLoadlibraryA = GetProcAddress(kernel32, "LoadLibraryA");
    HANDLE threadHandle = CreateRemoteThread(hProcess, NULL, 0, 
        (LPTHREAD_START_ROUTINE)pfnLoadlibraryA, param_addr, 0, NULL); 
   
    if (threadHandle == NULL) return FALSE;
    WaitForSingleObject(threadHandle, -1);
    VirtualFreeEx(hProcess, param_addr, 0x100, MEM_COMMIT);

    return TRUE;
}

WINHOOKDEF WINHOOK_EXPORT 
void winhook_installconsole()
{
    AllocConsole();
    freopen("CONOUT$", "w", stdout);    
}

// dynamic hook functions
WINHOOKDEF WINHOOK_EXPORT 
BOOL winhook_patchmemory(LPVOID addr, 
    void* buf, size_t bufsize)
{
    if(addr==NULL || buf==NULL) return FALSE;
	DWORD oldprotect;
    BOOL ret = VirtualProtect(addr, bufsize, PAGE_EXECUTE_READWRITE, &oldprotect);
	if(ret)
	{
		CopyMemory(addr, buf, bufsize);
        VirtualProtect(addr, bufsize, oldprotect, &oldprotect);
	}
    return ret;
}

WINHOOKDEF WINHOOK_EXPORT 
int winhook_patchmemorys(LPVOID addrs[], 
    void* bufs[], size_t bufsizes[], int n)
{
    int ret = 0;
    for(int i=0; i<n;i++)
    {
        ret += winhook_patchmemory(
            addrs[i], bufs[i], bufsizes[i]);
    }
    return ret;
}

void* winhook_searchmemory(void* addr,  size_t memsize, 
    const char* pattern, size_t* pmatchsize)
{
    size_t i = 0;
    int matchend = 0;
    void* matchaddr = NULL;
    while (i < memsize)
    {
        int j = 0;
        int matchflag = 1;
        matchend = 0;
        while (pattern[j])
        {
            if (pattern[j] == 0x20)
            {
                j++;
                continue;
            }
            char _c1 = (((char*)addr)[i+matchend]>>4);
            _c1 = _c1 < 10 ? _c1 + 0x30 : _c1 + 0x41;
            char _c2 = (((char*)addr)[i+matchend]&0xf);
            _c2 = _c2 < 10 ? _c2 + 0x30 : _c2 + 0x41;
            if (pattern[j] != '?')
            {
                if (_c1 != pattern[j] && _c1 + 0x20 != pattern[j])
                {
                    matchflag = 0;
                    break;
                }
            }
            if (pattern[j + 1] != '?')
            {
                if (_c2 != pattern[j+1] && _c2 + 0x20 != pattern[j+1])
                {
                    matchflag = 0;
                    break;
                }
            }
            j += 2;
            matchend++;
        }
        if (matchflag)
        {
            matchaddr = (void*)((uint8_t*)addr + i);
            break;
        }
        i++;
    }
    if (pmatchsize) *pmatchsize = matchend;
    return matchaddr;
}

WINHOOKDEF WINHOOK_EXPORT 
BOOL winhook_iathookmodule(LPCSTR targetDllName, 
    LPCSTR moduleDllName, PROC pfnOrg, PROC pfnNew)
{
    size_t imageBase = (size_t)GetModuleHandleA(moduleDllName);
    PIMAGE_DOS_HEADER pDosHeader = (PIMAGE_DOS_HEADER)imageBase;
    PIMAGE_NT_HEADERS  pNtHeader = (PIMAGE_NT_HEADERS)
        ((uint8_t*)imageBase + pDosHeader->e_lfanew);
    PIMAGE_FILE_HEADER pFileHeader = &pNtHeader->FileHeader;
    PIMAGE_OPTIONAL_HEADER pOptHeader = &pNtHeader->OptionalHeader;
    PIMAGE_DATA_DIRECTORY pDataDirectory = pOptHeader->DataDirectory;
    PIMAGE_DATA_DIRECTORY pImpEntry =  
        &pDataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT];
    PIMAGE_IMPORT_DESCRIPTOR pImpDescriptor =  
        (PIMAGE_IMPORT_DESCRIPTOR)(imageBase + pImpEntry->VirtualAddress);

    DWORD dwOldProtect = 0;
    for (; pImpDescriptor->Name; pImpDescriptor++) 
    {
        // find the dll IMPORT_DESCRIPTOR
        LPCSTR pDllName = (LPCSTR)(imageBase + pImpDescriptor->Name);
        if (!_stricmp(pDllName, targetDllName)) // ignore case
        {
            PIMAGE_THUNK_DATA pFirstThunk = (PIMAGE_THUNK_DATA)
                (imageBase + pImpDescriptor->FirstThunk);
            // find the iat function va
            for (; pFirstThunk->u1.Function; pFirstThunk++) 
            {
                if (pFirstThunk->u1.Function == (size_t)pfnOrg)
                {
                    VirtualProtect((LPVOID)&pFirstThunk->u1.Function,
                        4, PAGE_EXECUTE_READWRITE, &dwOldProtect);
                    pFirstThunk->u1.Function = (size_t)pfnNew;
                    VirtualProtect((LPVOID)&pFirstThunk->u1.Function,
                        4, dwOldProtect, &dwOldProtect);
                    return TRUE;
                }
            }
        }
    }
    return FALSE;
}

WINHOOKDEF WINHOOK_EXPORT 
BOOL winhook_iathook(LPCSTR targetDllName, PROC pfnOrg, PROC pfnNew)
{
    return winhook_iathookmodule(targetDllName, NULL, pfnOrg, pfnNew);
}

#ifndef WINHOOK_NOINLINEHOOK
#ifdef WINHOOK_USEDETOURS
#include "detours.h"
WINHOOKDEF WINHOOK_EXPORT 
int winhook_inlinehooks(PVOID pfnTargets[], 
    PVOID pfnNews[], PVOID pfnOlds[], size_t n)
{
    int i=0;
    DetourRestoreAfterWith();
    DetourTransactionBegin();
    DetourUpdateThread(GetCurrentThread());
    for(int i=0; i<n ;i++)
    {
        if(!pfnNews[i]) continue;
        pfnOlds[i] = pfnTargets[i];
        DetourAttach(&pfnOlds[i], pfnNews[i]);
    }
    DetourTransactionCommit();
    return i;
}

WINHOOKDEF WINHOOK_EXPORT
int winhook_inlineunhooks(PVOID pfnTargets[], 
    PVOID pfnNews[], PVOID pfnOlds[], size_t n)
{
    int i = 0;
    DetourTransactionBegin();
    DetourUpdateThread(GetCurrentThread());
    for(i=0; i<n ;i++)
    {
        if(!pfnNews[i]) continue;
        DetourDetach(&pfnOlds[i], pfnNews[i]);
    }
    DetourTransactionCommit();
    return i;
}
#else // use minhook
#define MINHOOK_IMPLEMENTATION
#include "minhook.h"
WINHOOKDEF WINHOOK_EXPORT 
int winhook_inlinehooks(PVOID pfnTargets[], 
    PVOID pfnNews[], PVOID pfnOlds[], size_t n)
{
    int i;
    if (MH_Initialize() != MH_OK)  return 0;
    for(i=0; i<n ;i++)
    {
        if(!pfnNews[i]) continue;
        MH_CreateHook(pfnTargets[i], pfnNews[i], &pfnOlds[i]);
        MH_EnableHook(pfnTargets[i]);
    }
    return i;
}

WINHOOKDEF WINHOOK_EXPORT
int winhook_inlineunhooks(PVOID pfnTargets[], 
    PVOID pfnNews[], PVOID pfnOlds[], size_t n)
{
    int i;
    for(i=0; i<n ;i++)
    {
        if(!pfnTargets[i]) continue;
        MH_DisableHook(pfnTargets[i]);
    }
    if(MH_Uninitialize() != MH_OK) return 0;
    return i;
}
#endif
#endif

#endif

/*
history:
v0.1 initial version
v0.2 add make this to single file
v0.2.2 add WINHOOK_STATIC, WINHOOK_SHARED macro
v0.2.3 change name to winhook.h and add guard for function name
v0.2.4 add winhook_searchmemory
v0.2.5 add minhook backend, compatible withh gcc, tcc
*/