#!/usr/bin/env python3
"""
Exercice 2 : Bloquer uniquement les paquets ICMP (ping)
Le reste du trafic passe normalement
"""
from bcc import BPF
import sys

bpf_text = """
#include <uapi/linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/icmp.h>
#include <linux/in.h>

// Compteurs: [0]=dropped, [1]=passed
BPF_ARRAY(stats, u64, 2);

int xdp_block_icmp(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    
    // À COMPLÉTER: Parser le header Ethernet
    // 1. Créer un pointeur vers struct ethhdr
    struct ethhdr *eth = data;
    // 2. Vérifier que le pointeur + taille ne dépasse pas data_end
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    
    // À COMPLÉTER: Vérifier si c'est IPv4
    // Indice: eth->h_proto doit être égal à htons(ETH_P_IP)
    // Pourquoi htons() ? (réfléchissez au byte order)
    if (eth->h_proto != htons(ETH_P_IP))
        return XDP_PASS;
    
    // À COMPLÉTER: Parser le header IP
    // 1. Calculer la position : data + taille du header Ethernet
    struct iphdr *ip = data + sizeof(struct ethhdr);
    
    // 2. Vérifier les limites
    if ((void *)(ip + 1) > data_end)
        return XDP_PASS;
    
    // À COMPLÉTER: Vérifier si c'est ICMP et bloquer
    // Indice: ip->protocol contient le numéro de protocole
    // IPPROTO_ICMP est la constante pour ICMP
    
    if (ip->protocol == IPPROTO_ICMP) {
        // Incrémenter compteur dropped (stats[0])
        u32 key = 0;
        u64 *count = stats.lookup(&key);
        if (count) {
            __sync_fetch_and_add(count, 1);
        }
        return XDP_DROP;
    }
    
    // À COMPLÉTER: Si ce n'est pas ICMP, laisser passer
    // Incrémenter compteur passed (stats[1])
    u32 key = 1;
    u64 *count = stats.lookup(&key);
    if (count) {
        __sync_fetch_and_add(count, 1);
    }
    return XDP_PASS;
}
"""

def main():
    if len(sys.argv) < 2:
        print("Usage: sudo python3 ex2_xdp_block_icmp.py <interface>")
        sys.exit(1)
    
    interface = sys.argv[1]
    b = BPF(text=bpf_text)
    fn = b.load_func("xdp_block_icmp", BPF.XDP)
    
    try:
        b.attach_xdp(interface, fn, 0)
        print(f"✓ Filtre ICMP actif sur {interface}")
        print("  Les pings seront bloqués")
        print("  Le reste du trafic passe normalement")
        print("\nTestez avec : ping 8.8.8.8 (devrait échouer)")
        print("           et : curl http://example.com (devrait marcher)\n")
        
        stats = b["stats"]
        
        import time
        while True:
            time.sleep(1)
            dropped = stats[0].value
            passed = stats[1].value
            total = dropped + passed
            
            if total > 0:
                drop_rate = (dropped / total) * 100
                print(f"Paquets : {total:8} | Bloqués : {dropped:6} ({drop_rate:.1f}%) | "
                      f"Passés : {passed:6}")
            else:
                print("En attente de paquets...")
                
    except KeyboardInterrupt:
        print("\n")
    finally:
        b.remove_xdp(interface, 0)
        print("✓ Filtre désactivé")

if __name__ == "__main__":
    main()
