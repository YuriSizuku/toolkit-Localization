"""
modify windows pe with dll injected for hooking
    v0.3.1, developed by devseed
"""

from ast import Store, arg
from pickle import FALSE
import sys
import os
import argparse
import lief
from keystone import Ks, KS_ARCH_X86, KS_MODE_32, KS_MODE_64

# This might be regared as virus by windows defender
# can not be ASLR
def injectdll_iat(exepath, dllpath, outpath="out.exe"): 
    binary_exe = lief.parse(exepath)
    binary_dll = lief.parse(dllpath)
    
    dllpath = os.path.basename(dllpath)
    dll_imp = binary_exe.add_library(dllpath)
    print("the import dll in " + exepath)
    for imp in binary_exe.imports:
        print(imp.name)

    for exp_func in binary_dll.exported_functions:
        dll_imp.add_entry(exp_func.name)
        print(dllpath + ", func "+ exp_func.name + " added!")

    # disable ASLR
    exe_oph =  binary_exe.optional_header
    exe_oph.remove(lief.PE.DLL_CHARACTERISTICS.DYNAMIC_BASE)

    builder = lief.PE.Builder(binary_exe)
    builder.build_imports(True).patch_imports(True)
    builder.build()
    builder.write(outpath)

# change the oep and use codecave for LoadLibraryA dll
# only support for x86 and x64 architecture, no arm support
def injectdll_codecave(exepath, dllpath, outpath="out.exe"):
    # parsing pe
    pe = lief.parse(exepath)
    pe_oph = pe.optional_header
    imgbase = pe_oph.imagebase
    oeprva = pe_oph.addressof_entrypoint
    section_code = pe.section_from_rva(oeprva)
    impentry_LoadLibraryA = pe.get_import("KERNEL32.dll")\
            .get_entry("LoadLibraryA")

    # find position to code cave
    dllpath_bytes = dllpath.encode() + b'\x00'
    if pe_oph.magic == lief.PE.PE_TYPE.PE32_PLUS:
        print(f"{exepath}: oep={imgbase+oeprva:016X}, "
        f"code_section={imgbase+section_code.virtual_size:016X}, "
        f"LoadLibraryA={imgbase+impentry_LoadLibraryA.iat_address:016X}")
        max_len = len(dllpath_bytes) + 0x60
    elif pe_oph.magic == lief.PE.PE_TYPE.PE32:
        print(f"{exepath}: oep={imgbase+oeprva:08X}, "
        f"code_section={imgbase+section_code.virtual_size:08X}, "
        f"LoadLibraryA={imgbase+impentry_LoadLibraryA.iat_address:08X}")
        max_len = len(dllpath_bytes) + 0x20
    if section_code.sizeof_raw_data - section_code.virtual_size < max_len:
        print("error! can not find space for codecave")
        return 
    else:
        payload_rva = section_code.virtual_address + section_code.virtual_size

    # make code cave code
    if pe_oph.magic == lief.PE.PE_TYPE.PE32_PLUS:
        infostr = f"inject asm at {imgbase+payload_rva:016X}:"
        ks = Ks(KS_ARCH_X86, KS_MODE_64)
        code_str = f"""
            push rcx;
            lea rcx, [dllpath+1];
            mov rax, 0x{imgbase:016X};
            add rcx, rax;
            mov rax, 0x{imgbase+impentry_LoadLibraryA.iat_address:016X};
            call qword ptr ds:[rax];
            pop rcx;
            mov rax, 0x{imgbase+oeprva:016X};
            jmp rax; 
            dllpath:
            nop"""
        print(infostr, code_str)
        payload, _ = ks.asm(code_str, addr=payload_rva) # > 32bit error

    elif pe_oph.magic == lief.PE.PE_TYPE.PE32:
        infostr = f"try to inject asm at {imgbase+payload_rva:08X}:"
        ks = Ks(KS_ARCH_X86, KS_MODE_32)
        code_str = f"""
            pushad;
            mov eax, dllpath+1;
            push eax;
            call dword ptr ds:[0x{imgbase+impentry_LoadLibraryA.iat_address:08X}];
            popad;
            jmp 0x{imgbase+oeprva:08X};
            dllpath:
            nop"""
        print(infostr, code_str)
        payload, _ = ks.asm(code_str, addr=imgbase+payload_rva)
        
    else:
        print("error invalid pe magic!", pe_oph.magic)
        return

    payload = payload + list(dllpath_bytes)
    print("payload: ", [hex(x) for x in payload])

    # inject code
    section_code.virtual_size += len(payload)
    section_code.content += payload
    pe_oph.addressof_entrypoint = payload_rva
    pe_oph.remove(lief.PE.DLL_CHARACTERISTICS.DYNAMIC_BASE)
    builder = lief.PE.Builder(pe)
    builder.build()
    builder.write(outpath)

# change the oep and use codecave by using PEB
# only support for x86 and x64 architecture, no arm support
def injectdll_codecave2(exepath, dllpath, outpath="out.exe", aslr=FALSE):
        # parsing pe
    pe = lief.parse(exepath)
    pe_oph = pe.optional_header
    imgbase = pe_oph.imagebase
    oeprva = pe_oph.addressof_entrypoint

    # find position to code cave
    dllpath_bytes = dllpath.encode() + b'\x00'
    if pe_oph.magic == lief.PE.PE_TYPE.PE32_PLUS:
        findLoadLibraryA_code = [0x41, 0x57, 0x41, 0x56, 0x56, 0x57, 0x55, 0x53, 0x48, 0x83, 0xEC, 0x10, 0x48, 0x89, 0xE1, 0x48, 0xC7, 0x01, 0x00, 0x00, 0x00, 0x00, 0x65, 0x48, 0x8B, 0x04, 0x25, 0x60, 0x00, 0x00, 0x00, 0x48, 0x8B, 0x40, 0x18, 0x48, 0x8B, 0x40, 0x20, 0x48, 0x8B, 0x00, 0x48, 0x8B, 0x00, 0x48, 0x8B, 0x40, 0x20, 0x48, 0x89, 0x04, 0x24, 0x4C, 0x8B, 0x39, 0x48, 0xB8, 0x69, 0x62, 0x72, 0x61, 0x72, 0x79, 0x41, 0x00, 0x48, 0x89, 0x41, 0x05, 0x48, 0xB8, 0x4C, 0x6F, 0x61, 0x64, 0x4C, 0x69, 0x62, 0x72, 0x48, 0x89, 0x01, 0x49, 0x63, 0x47, 0x3C, 0x41, 0x8B, 0x84, 0x07, 0x88, 0x00, 0x00, 0x00, 0x45, 0x8B, 0x4C, 0x07, 0x24, 0x4D, 0x01, 0xF9, 0x45, 0x8B, 0x44, 0x07, 0x1C, 0x4D, 0x01, 0xF8, 0x48, 0x81, 0xF9, 0x00, 0x00, 0x01, 0x00, 0x73, 0x29, 0x41, 0x8B, 0x44, 0x07, 0x10, 0xFF, 0xC8, 0x48, 0x89, 0xE1, 0xBA, 0xFF, 0xFF, 0x00, 0x00, 0x21, 0xD1, 0x21, 0xD0, 0x29, 0xC1, 0x48, 0x63, 0xC1, 0x41, 0x0F, 0xB7, 0x04, 0x41, 0x41, 0x8B, 0x04, 0x80, 0x4C, 0x01, 0xF8, 0xE9, 0x88, 0x00, 0x00, 0x00, 0x45, 0x8B, 0x54, 0x07, 0x18, 0x4D, 0x85, 0xD2, 0x74, 0x69, 0x45, 0x8B, 0x74, 0x07, 0x20, 0x4D, 0x01, 0xFE, 0x4D, 0x8D, 0x5F, 0x01, 0x31, 0xC0, 0x31, 0xF6, 0x41, 0x8B, 0x1C, 0xB6, 0x41, 0x8A, 0x0C, 0x1F, 0x84, 0xC9, 0x74, 0x33, 0x4C, 0x01, 0xDB, 0x31, 0xFF, 0x0F, 0xBE, 0xD1, 0x0F, 0xBE, 0x2C, 0x3C, 0x85, 0xED, 0x74, 0x27, 0x40, 0x38, 0xE9, 0x74, 0x10, 0x8D, 0x4A, 0x20, 0x39, 0xE9, 0x74, 0x09, 0x89, 0xE9, 0x83, 0xC1, 0x20, 0x39, 0xD1, 0x75, 0x16, 0x8A, 0x0C, 0x3B, 0x48, 0xFF, 0xC7, 0x84, 0xC9, 0x75, 0xD6, 0x89, 0xFF, 0xEB, 0x02, 0x31, 0xFF, 0x31, 0xD2, 0x40, 0x8A, 0x2C, 0x3C, 0x40, 0x0F, 0xBE, 0xCD, 0x39, 0xCA, 0x74, 0x0E, 0x48, 0xFF, 0xC6, 0x4C, 0x39, 0xD6, 0x75, 0xA9, 0xEB, 0x15, 0x31, 0xC0, 0xEB, 0x11, 0x89, 0xF0, 0x41, 0x0F, 0xB7, 0x04, 0x41, 0x41, 0x8B, 0x04, 0x80, 0x49, 0x01, 0xC7, 0x4C, 0x89, 0xF8, 0x48, 0x83, 0xC4, 0x10, 0x5B, 0x5D, 0x5F, 0x5E, 0x41, 0x5E, 0x41, 0x5F, 0xC3]
        ks = Ks(KS_ARCH_X86, KS_MODE_64)
        infostr = f"try to compile asm:"
        code_str = f"""
            call getip; 
            lea rbx, [rax-5];
            push rcx;
            push rdx;
            push r8;
            push r9;
            sub rsp, 0x28; // this is for memory 0x10 align

            // get the imagebase
            mov rax, 0x60; // to avoid relative addressing
            mov rdi, qword ptr gs:[rax]; //peb
            mov rdi, [rdi + 18h]; //ldr
            mov rdi, [rdi + 20h]; //InMemoryOrderLoadList, this
            mov rdi, [rdi -10h + 30h]; //this.DllBase
            
            // load dll
            lea rax, [rbx + dllpath];
            add rax, {len(dllpath_bytes)};
            call rax; // findLoadlibraryA
            lea rcx, [rbx+dllpath];
            call rax; // LoadLibraryA
            
            // jmp to origin oep
            add rsp, 0x28;
            pop r9;
            pop r8;
            pop rdx;
            pop rcx;
            mov rax, 0x{oeprva:04X};
            add rax, rdi;
            jmp rax;
            
            getip:
            mov rax, [rsp]
            ret

            dllpath:
            """
        print(infostr, code_str)
        payload, _ = ks.asm(code_str) # > 32bit error
    elif pe_oph.magic == lief.PE.PE_TYPE.PE32:
        findLoadLibraryA_code = [0x55, 0x53, 0x57, 0x56, 0x83, 0xEC, 0x24, 0x8D, 0x4C, 0x24, 0x14, 0xC7, 0x01, 0x00, 0x00, 0x00, 0x00, 0x64, 0xA1, 0x30, 0x00, 0x00, 0x00, 0x8B, 0x40, 0x0C, 0x8B, 0x40, 0x14, 0x8B, 0x00, 0x8B, 0x00, 0x8B, 0x40, 0x10, 0x89, 0x44, 0x24, 0x14, 0x8B, 0x01, 0xC6, 0x41, 0x0C, 0x00, 0xC7, 0x41, 0x08, 0x61, 0x72, 0x79, 0x41, 0xC7, 0x41, 0x04, 0x4C, 0x69, 0x62, 0x72, 0xC7, 0x01, 0x4C, 0x6F, 0x61, 0x64, 0x8B, 0x50, 0x3C, 0x8B, 0x54, 0x10, 0x78, 0x8B, 0x5C, 0x10, 0x24, 0x01, 0xC3, 0x8B, 0x7C, 0x10, 0x1C, 0x01, 0xC7, 0x81, 0xF9, 0x00, 0x00, 0x01, 0x00, 0x73, 0x1C, 0x8B, 0x54, 0x10, 0x10, 0x4A, 0xBE, 0xFF, 0xFF, 0x00, 0x00, 0x21, 0xF1, 0x21, 0xF2, 0x29, 0xD1, 0x0F, 0xB7, 0x0C, 0x4B, 0x03, 0x04, 0x8F, 0xE9, 0x92, 0x00, 0x00, 0x00, 0x8B, 0x4C, 0x10, 0x18, 0x89, 0x4C, 0x24, 0x10, 0x85, 0xC9, 0x74, 0x74, 0x89, 0x1C, 0x24, 0x89, 0x7C, 0x24, 0x04, 0x8B, 0x4C, 0x10, 0x20, 0x01, 0xC1, 0x89, 0x4C, 0x24, 0x0C, 0x8D, 0x48, 0x01, 0x89, 0x4C, 0x24, 0x08, 0x31, 0xED, 0x8B, 0x4C, 0x24, 0x0C, 0x8B, 0x34, 0xA9, 0x8A, 0x14, 0x30, 0xB9, 0x00, 0x00, 0x00, 0x00, 0xBB, 0x00, 0x00, 0x00, 0x00, 0x84, 0xD2, 0x74, 0x30, 0x03, 0x74, 0x24, 0x08, 0x31, 0xC9, 0x0F, 0xBE, 0xDA, 0x0F, 0xBE, 0x54, 0x0C, 0x14, 0x85, 0xD2, 0x74, 0x1E, 0x38, 0xD3, 0x74, 0x10, 0x8D, 0x7B, 0x20, 0x39, 0xD7, 0x74, 0x09, 0x89, 0xD7, 0x83, 0xC7, 0x20, 0x39, 0xDF, 0x75, 0x0E, 0x8A, 0x14, 0x0E, 0x41, 0x84, 0xD2, 0x75, 0xD8, 0x31, 0xDB, 0x8A, 0x54, 0x0C, 0x14, 0x0F, 0xBE, 0xCA, 0x39, 0xCB, 0x74, 0x0B, 0x45, 0x3B, 0x6C, 0x24, 0x10, 0x75, 0xA6, 0x31, 0xC0, 0xEB, 0x0E, 0x8B, 0x0C, 0x24, 0x0F, 0xB7, 0x0C, 0x69, 0x8B, 0x54, 0x24, 0x04, 0x03, 0x04, 0x8A, 0x83, 0xC4, 0x24, 0x5E, 0x5F, 0x5B, 0x5D, 0xC3]
        infostr = f"try to compile asm: "
        ks = Ks(KS_ARCH_X86, KS_MODE_32)
        code_str = f"""
            call getip; 
            lea ebx, [eax-5];
            
            // get the imagebase
            mov eax, 0x30; // to avoid relative addressing
            mov edi, dword ptr fs:[eax]; //peb
            mov edi, [edi + 0ch]; //ldr
            mov edi, [edi + 14h]; //InMemoryOrderLoadList, this
            mov edi, [edi -8h + 18h]; //this.DllBase

            // load dll
            lea eax, [ebx + dllpath];
            push eax;
            add eax, {len(dllpath_bytes)};
            call eax; // findLoadLibraryA
            call eax; // LoadLibraryA
            
            // jmp to origin oep
            mov eax, 0x{oeprva:04X};
            add eax, edi;
            jmp eax;
            
            getip:
            mov eax, [esp]
            ret

            dllpath:
            """
        print(infostr, code_str)
        payload, _ = ks.asm(code_str)
    else:
        raise ValueError(f"error invalid pe magic!, {pe_oph.magic}")

    payload = payload + list(dllpath_bytes) + findLoadLibraryA_code
    # print("payload: ", [hex(x) for x in payload])

    # inject code
    section_loader = lief.PE.Section(payload, ".loader", 
        lief.PE.SECTION_CHARACTERISTICS.MEM_EXECUTE)
    section_loader = pe.add_section(section_loader, 
        lief.PE.SECTION_TYPES.TEXT)
    pe_oph.addressof_entrypoint = section_loader.virtual_address
    if not aslr:
        pe_oph.remove(lief.PE.DLL_CHARACTERISTICS.DYNAMIC_BASE)
    builder = lief.PE.Builder(pe)
    builder.build()
    builder.write(outpath)

def debug():
    pass

def main():
    if len(sys.argv) < 3:
        print("injectdll exepath dllpath [-m|method iat|codecave(default)|codecave2] [-o outpath]")
        return

    parser = argparse.ArgumentParser()
    parser.add_argument('exepath', type=str)
    parser.add_argument('dllpath', type=str)
    parser.add_argument('--method', '-m', default='codecave')
    parser.add_argument('--outpath', '-o', default='out.exe')
    parser.add_argument('--aslr', action="store_true")
    args = parser.parse_args()
    if args.method.lower() == 'codecave':
        injectdll_codecave(args.exepath, args.dllpath, args.outpath)
    elif args.method.lower() == 'codecave2':
        injectdll_codecave2(args.exepath, args.dllpath, args.outpath)
    elif args.method.lower() == 'iat':
        injectdll_iat(args.exepath, args.dllpath, args.outpath, args.aslr)
    else:
        raise NotImplementedError()    
    
if __name__ == "__main__":
    # debug()
    main()
    pass

"""
history:
v0.1 injectdll by adding iat entry
v0.2 add codecave method using dynamiclly LoadLibraryA from iat,
        to avoid windows defender assuming this as virus
v0.3 add codecave2 method using PEB to get LoadLibraryA
v0.3.1 support aslr for codecave2 method
"""