#!/usr/bin/env python3
"""
Exercice 4 : Bloquer un port TCP/UDP spécifique
"""
from bcc import BPF
import sys

BLOCKED_PORT = 80

bpf_text = """
#include <uapi/linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>

#define BLOCKED_PORT_VALUE BLOCKED_PORT_PLACEHOLDER

BPF_ARRAY(stats, u64, 2);

int xdp_block_port(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    
    // Parser Ethernet et IP (comme avant)
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;
    
    if (eth->h_proto != htons(ETH_P_IP))
        return XDP_PASS;
    
    struct iphdr *ip = data + sizeof(struct ethhdr);
    if ((void *)(ip + 1) > data_end)
        return XDP_PASS;
    
    u16 dport = 0;
    
    // À COMPLÉTER: Parser TCP
    // Attention: Le header IP peut être de taille variable (options)
    // Utilisez ip->ihl (IP Header Length) pour calculer la position
    // ihl est en nombre de mots de 32 bits
    if (ip->protocol == IPPROTO_TCP) {
        // Position du header TCP = après le header IP
        // struct tcphdr *tcp = (void *)ip + (ip->ihl * 4);
        
        // À COMPLÉTER:
        // 1. Vérifier les limites
        // 2. Extraire le port destination
        // 3. Convertir avec ntohs() (pourquoi ?)
        // VOTRE CODE ICI
        
    } else if (ip->protocol == IPPROTO_UDP) {
        // À COMPLÉTER: Parser UDP (similaire à TCP)
        // struct udphdr *udp = ...
        // VOTRE CODE ICI
    }
    
    // À COMPLÉTER: Bloquer si le port correspond
    // if (dport == BLOCKED_PORT_VALUE) {
    //     // Compter et bloquer
    //     VOTRE CODE ICI
    // }
    
    // Laisser passer
    u32 key = 1;
    u64 *count = stats.lookup(&key);
    if (count)
        __sync_fetch_and_add(count, 1);
    
    return XDP_PASS;
}
"""

def main():
    if len(sys.argv) < 2:
        print("Usage: sudo python3 ex4_xdp_block_port.py <interface> [port]")
        print("Exemple: sudo python3 ex4_xdp_block_port.py eth0 80")
        sys.exit(1)
    
    interface = sys.argv[1]
    blocked_port = int(sys.argv[2]) if len(sys.argv) > 2 else BLOCKED_PORT
    
    bpf_code = bpf_text.replace("BLOCKED_PORT_PLACEHOLDER", str(blocked_port))
    
    print(f"Blocage du port : {blocked_port}")
    
    b = BPF(text=bpf_code)
    fn = b.load_func("xdp_block_port", BPF.XDP)
    
    try:
        b.attach_xdp(interface, fn, 0)
        print(f" Filtre PORT actif sur {interface}")
        print(f"  Port bloqué : {blocked_port}")
        
        if blocked_port == 80:
            print("\nTestez avec :")
            print("  curl http://example.com     # Devrait échouer (port 80)")
            print("  curl https://example.com    # Devrait marcher (port 443)")
        
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
