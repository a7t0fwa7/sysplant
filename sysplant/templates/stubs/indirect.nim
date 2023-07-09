##__PROC_DEFINITION__##
    asm """
        mov [rsp +8], rcx
        mov [rsp+16], rdx
        mov [rsp+24], r8
        mov [rsp+32], r9
        sub rsp, 0x28
        mov ecx, ##__FUNCTION_HASH__##
        call `SPT_GetSyscallNumber`
        mov r15, rax
        mov ecx, ##__FUNCTION_HASH__##
        call `##__FUNCTION_RESOLVE__##`
        xor r15, rax
        xor rax, r15
        xor r15, rax
        add rsp, 0x28
        mov rcx, [rsp +8]
        mov rdx, [rsp+16]
        mov r8, [rsp+24]
        mov r9, [rsp+32]
        mov r10, rcx
        jmp r15
    """