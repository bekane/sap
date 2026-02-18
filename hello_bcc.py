#!/usr/bin/env python3
from bcc import BPF

bpf_text = r"""
#include <uapi/linux/ptrace.h>

int hello(struct pt_regs *ctx) {
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;

    char comm[16];
    bpf_get_current_comm(&comm, sizeof(comm));

    bpf_trace_printk("Hello BCC pid=%d comm=%s\\n", pid, comm);
    return 0;
}
"""

b = BPF(text=bpf_text)
b.attach_kprobe(event="__x64_sys_execve", fn_name="hello")

print("Tracing execve... Ctrl-C to stop.")
b.trace_print()

