#!/usr/bin/env python3
"""
Exercice 1 : Bloquer tous les paquets avec XDP
ATTENTION : Ceci coupera votre connexion réseau !

CONSIGNES:
- Complétez les sections marquées "À COMPLÉTER"
- Testez votre code progressivement
- Utilisez Ctrl+C pour arrêter proprement
"""
from bcc import BPF
import time
import sys

# Programme eBPF
bpf_text = """
#include <uapi/linux/bpf.h>
#include <linux/if_ether.h>

// Compteur de paquets bloqués
BPF_ARRAY(drop_count, u64, 1);

int xdp_drop_all(struct xdp_md *ctx) {
    u32 key = 0;
    u64 *count = drop_count.lookup(&key);
    
    if (count) {
        // À COMPLÉTER: Incrémenter le compteur de manière atomique
        // Indice: utilisez __sync_fetch_and_add()
        __sync_fetch_and_add(count, 1);
    }
    
    // À COMPLÉTER: Retourner l'action XDP appropriée pour BLOQUER le paquet
    // Indice: Quelle constante XDP permet de jeter un paquet ?
    return XDP_DROP;
}
"""

def main():
    if len(sys.argv) < 2:
        print("Usage: sudo python3 ex1_xdp_drop_all.py <interface>")
        print("Exemple: sudo python3 ex1_xdp_drop_all.py eth0")
        print("\n  ATTENTION : Ceci bloquera TOUT le trafic réseau !")
        sys.exit(1)
    
    interface = sys.argv[1]
    
    print(f"  ATTENTION : Je vais bloquer TOUT le trafic sur {interface}")
    print("   Vous perdrez la connexion réseau !")
    print("   Appuyez sur Ctrl+C pour restaurer.")
    # input("   Appuyez sur Entrée pour continuer...")
    
    # Charger le programme
    b = BPF(text=bpf_text)
    
    # À COMPLÉTER: Charger la fonction XDP
    # Indice: utilisez b.load_func() avec le bon type
    fn = b.load_func("xdp_drop_all", BPF.XDP)
    
    try:
        # À COMPLÉTER: Attacher le programme XDP à l'interface
        # Indice: utilisez b.attach_xdp()
        b.attach_xdp(interface, fn, 0)
        
        print(f"\n✓ XDP DROP actif sur {interface}")
        print("  Testez depuis un autre terminal : ping 8.8.8.8")
        print("\nAppuyez sur Ctrl+C pour arrêter.\n")
        
        drop_count = b["drop_count"]
        
        while True:
            time.sleep(1)
            count = drop_count[0].value
            print(f"Paquets bloqués : {count}")
            
    except:
        print("\n\nRestoration du réseau...")
    finally:
        # À COMPLÉTER: Détacher XDP proprement
        # Indice: utilisez b.remove_xdp()
        b.remove_xdp(interface, 0)
        print("✓ XDP détaché - réseau restauré")

if __name__ == "__main__":
    main()
