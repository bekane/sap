#!/usr/bin/env python3
"""
Exercice 3 : Bloquer une adresse IP source spécifique
"""
from bcc import BPF
import sys
import socket
import struct

BLOCKED_IP = "1.1.1.1"

bpf_text = """
#include <uapi/linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>

#define BLOCKED_IP_INT BLOCKED_IP_PLACEHOLDER

BPF_ARRAY(stats, u64, 2);  // [0]=blocked, [1]=passed

int xdp_block_ip(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    
    // À COMPLÉTER: Parser Ethernet et IP (réutilisez la logique de l'ex2)
    // struct ethhdr *eth = ...
    // Vérifications...
    // struct iphdr *ip = ...
    
    // À COMPLÉTER: Vérifier si l'IP source correspond à l'IP bloquée
    // Indice: ip->saddr contient l'IP source (en network byte order)
    // Comparez avec BLOCKED_IP_INT
    // if (VOTRE CODE ICI) {
    //     // Bloquer et compter
    //     return XDP_DROP;
    // }
    
    // Sinon laisser passer
    u32 key = 1;
    u64 *count = stats.lookup(&key);
    if (count)
        __sync_fetch_and_add(count, 1);
    
    return XDP_PASS;
}
"""

def ip_to_int(ip_str):
    """
    Convertir une IP string vers format network byte order
    
    À COMPLÉTER:
    1. Utilisez socket.inet_aton() pour convertir l'IP en bytes
    2. Utilisez struct.unpack() pour convertir en int
    3. Format: "I" pour unsigned int
    
    Pourquoi cette conversion est nécessaire ?
    """
    # VOTRE CODE ICI
    pass

def int_to_ip(ip_int):
    """Convertir int vers IP string"""
    packed = struct.pack("I", ip_int)
    return socket.inet_ntoa(packed)

def main():
    if len(sys.argv) < 2:
        print("Usage: sudo python3 ex3_xdp_block_ip.py <interface> [ip_to_block]")
        print(f"Exemple: sudo python3 ex3_xdp_block_ip.py eth0 1.1.1.1")
        sys.exit(1)
    
    interface = sys.argv[1]
    blocked_ip = sys.argv[2] if len(sys.argv) > 2 else BLOCKED_IP
    
    # Convertir IP en entier
    blocked_ip_int = ip_to_int(blocked_ip)
    
    # Remplacer le placeholder dans le code C
    bpf_code = bpf_text.replace("BLOCKED_IP_PLACEHOLDER", str(blocked_ip_int))
    
    print(f"Blocage de l'IP : {blocked_ip}")
    print(f"  (format int : 0x{blocked_ip_int:08x})")
    
    b = BPF(text=bpf_code)
    fn = b.load_func("xdp_block_ip", BPF.XDP)
    
    try:
        b.attach_xdp(interface, fn, 0)
        print(f"\n Filtre IP actif sur {interface}")
        print(f"  Bloqué : {blocked_ip}")
        print(f"\nTestez avec : ping {blocked_ip}\n")
        
        stats = b["stats"]
        
        import time
        while True:
            time.sleep(1)
            blocked = stats[0].value
            passed = stats[1].value
            print(f"Bloqués : {blocked:6} | Passés : {passed:8}")
                
    except KeyboardInterrupt:
        print("\n")
    finally:
        b.remove_xdp(interface, 0)
        print(" Filtre désactivé")

if __name__ == "__main__":
    main()
