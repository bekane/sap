#!/usr/bin/env python3
"""
Exercice 5 : Firewall XDP piloté par fichier de configuration
Les règles sont lues depuis firewall.conf au démarrage

Usage: sudo python3 ex5_xdp_firewall_config.py <interface> [fichier.conf]
"""
from bcc import BPF
import sys
import os
import socket
import struct
import time

bpf_text = """
#include <uapi/linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>

// À COMPLÉTER: Déclarer deux maps BPF
// 1. blocked_ips   : clé=u32 (IP),   valeur=u8, taille=1024
// 2. blocked_ports : clé=u16 (port), valeur=u8, taille=256
// BPF_HASH(blocked_ips,   ...VOTRE CODE ICI...);
// BPF_HASH(blocked_ports, ...VOTRE CODE ICI...);

// Statistiques : [0]=dropped_ip, [1]=dropped_port, [2]=passed
BPF_ARRAY(stats, u64, 3);

int xdp_firewall(struct xdp_md *ctx) {
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    // Parser Ethernet
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;
    if (eth->h_proto != htons(ETH_P_IP))
        return XDP_PASS;

    // Parser IP
    struct iphdr *ip = data + sizeof(struct ethhdr);
    if ((void *)(ip + 1) > data_end)
        return XDP_PASS;

    // À COMPLÉTER: Vérifier si l'IP source est dans blocked_ips
    // Indice: blocked_ips.lookup(&ip->saddr) retourne NULL si absent
    // Si trouvé et valeur == 1 → incrémenter stats[0] et XDP_DROP
    // VOTRE CODE ICI

    // Parser TCP/UDP pour extraire le port destination
    u16 dport = 0;
    if (ip->protocol == IPPROTO_TCP) {
        struct tcphdr *tcp = (void *)ip + (ip->ihl * 4);
        if ((void *)(tcp + 1) > data_end)
            return XDP_PASS;
        dport = ntohs(tcp->source);
    } else if (ip->protocol == IPPROTO_UDP) {
        struct udphdr *udp = (void *)ip + (ip->ihl * 4);
        if ((void *)(udp + 1) > data_end)
            return XDP_PASS;
        dport = ntohs(udp->source);
    }

    // À COMPLÉTER: Vérifier si le port est dans blocked_ports
    // Même logique que pour les IPs, mais avec dport
    // Attention: ne vérifier que si dport > 0
    // Si trouvé et valeur == 1 → incrémenter stats[1] et XDP_DROP
    // VOTRE CODE ICI

    // Laisser passer
    u32 key = 2;
    u64 *count = stats.lookup(&key);
    if (count) __sync_fetch_and_add(count, 1);
    return XDP_PASS;
}
"""

def ip_to_int(ip_str):
    """
    Convertir une IP string vers int (network byte order)
    À COMPLÉTER: réutilisez votre code de l'exercice 3
    """
    # VOTRE CODE ICI
    pass

def load_config(config_file):
    """
    Parser le fichier de configuration

    À COMPLÉTER:
    - Ouvrir le fichier ligne par ligne
    - Ignorer les lignes vides et les commentaires (#)
    - Extraire la liste après 'IP_LIST='
    - Extraire la liste après 'PORT_LIST='
    - Retourner un dict {'ips': [...], 'ports': [...]}

    Indice: line.startswith('IP_LIST=') puis line.split('=', 1)[1].split(',')
    """
    config = {'ips': [], 'ports': []}

    if not os.path.exists(config_file):
        print(f"  Fichier introuvable : {config_file}")
        print(f"   Créez-le avec le format suivant :")
        print(f"   IP_LIST=1.1.1.1,8.8.8.8")
        print(f"   PORT_LIST=80,443")
        return config

    # À COMPLÉTER
    # with open(config_file) as f:
    #     for line in f:
    #         ...
    # VOTRE CODE ICI

    return config

def load_rules(b, config):
    """
    Injecter les règles dans les Maps BPF

    À COMPLÉTER pour les IPs:
    - Pour chaque IP dans config['ips'] :
        1. Convertir en int avec ip_to_int()
        2. b["blocked_ips"][b["blocked_ips"].Key(ip_int)] = b["blocked_ips"].Leaf(1)

    À COMPLÉTER pour les ports:
    - Pour chaque port dans config['ports'] :
        1. Convertir en int
        2. Même logique avec b["blocked_ports"]
    """
    print("\n IPs bloquées :")
    for ip in config['ips']:
        try:
            # VOTRE CODE ICI
            print(f"    {ip}")
        except Exception as e:
            print(f"    {ip} — {e}")

    print("\n Ports bloqués :")
    for port_str in config['ports']:
        try:
            port = int(port_str)
            # VOTRE CODE ICI
            print(f"    {port}")
        except Exception as e:
            print(f"    {port_str} — {e}")
    print()

def show_stats(b):
    """Afficher les statistiques en une ligne"""
    dropped_ip   = b["stats"][0].value
    dropped_port = b["stats"][1].value
    passed       = b["stats"][2].value
    total        = dropped_ip + dropped_port + passed
    rate = ((dropped_ip + dropped_port) / total * 100) if total else 0
    print(f"\\r Total: {total:8} | "
          f"Bloqués IP: {dropped_ip:6} | "
          f"Bloqués Port: {dropped_port:6} | "
          f"Passés: {passed:6} | "
          f"Drop: {rate:5.1f}%", end="", flush=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: sudo python3 ex5_xdp_firewall_config.py <interface> [fichier.conf]")
        print("Exemple: sudo python3 ex5_xdp_firewall_config.py eth0 firewall.conf")
        sys.exit(1)

    interface   = sys.argv[1]
    config_file = sys.argv[2] if len(sys.argv) > 2 else "firewall.conf"

    print("  XDP Firewall — chargement par fichier de configuration")
    print(f"   Interface : {interface}")
    print(f"   Config    : {config_file}\\n")

    # Charger et parser la config
    config = load_config(config_file)

    if not config['ips'] and not config['ports']:
        print("  Aucune règle trouvée dans le fichier de config.")
        sys.exit(1)

    # Compiler et charger le programme eBPF
    b  = BPF(text=bpf_text)
    fn = b.load_func("xdp_firewall", BPF.XDP)

    # Injecter les règles dans les Maps BPF
    load_rules(b, config)

    try:
        b.attach_xdp(interface, fn, 0)
        print(f" Firewall attaché à {interface}")
        print("  Ctrl+C pour arrêter\\n")

        while True:
            show_stats(b)
            time.sleep(1)

    except KeyboardInterrupt:
        print("\\n")
    finally:
        b.remove_xdp(interface, 0)
        print(" Firewall détaché")
        # Afficher résumé final
        print(f"\\n Résumé :")
        print(f"   IPs bloquées  : {config['ips']}")
        print(f"   Ports bloqués : {config['ports']}")
        show_stats(b)
        print()

if __name__ == "__main__":
    main()
