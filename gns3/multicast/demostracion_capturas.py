"""Evidencia en paquetes: captura con tcpdump en un receptor suscrito (Rx-LAB2) y en un observador conectado al MISMO
conmutador (PC-LAB2), en la arquitectura tradicional y en la SDN, con un solo receptor suscrito.

Uso: python3 gns3/multicast/demostracion_capturas.py
Escribe gns3/multicast/datos/capturas/{tradicional,sdn}_{Rx-LAB2,PC-LAB2}.pcap (cabeceras de 96 bytes) y
capturas/resumen.txt con el conteo de paquetes del grupo y de mensajes IGMP en cada captura. Los .pcap se abren con Wireshark.
"""
import os
import subprocess
import time

from lib_experimento import GRUPO, corrida, modo_autonomo, modo_sdn, sh, sh_bg, contenedor

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, 'datos', 'capturas')
EQUIPOS = ['Rx-LAB2', 'PC-LAB2']


def main():
    os.makedirs(SALIDA, exist_ok=True)
    lineas = []
    for arq in ('tradicional', 'sdn'):
        if arq == 'sdn':
            modo_sdn(os.path.join(SALIDA, 'ryu_demostracion.log'))
        else:
            modo_autonomo(snooping=False)
        for h in EQUIPOS:
            sh(h, 'pkill tcpdump 2>/dev/null; rm -f /tmp/cap.pcap')
            sh_bg(h, 'tcpdump -i eth0 -s 96 -U -w /tmp/cap.pcap "igmp or (udp and dst host 239.10.10.10)"')
        time.sleep(2)
        c = corrida('multicast', 1, duracion=10)
        for h in EQUIPOS:
            sh(h, 'pkill -INT tcpdump')
        time.sleep(2)
        for h in EQUIPOS:
            destino = os.path.join(SALIDA, f'{arq}_{h}.pcap')
            subprocess.run(['docker', 'cp', f'{contenedor(h)}:/tmp/cap.pcap', destino], check=True)
            datos = sh(h, f'tcpdump -nr /tmp/cap.pcap "udp and dst host {GRUPO}" 2>/dev/null | wc -l')
            igmp = sh(h, 'tcpdump -nr /tmp/cap.pcap igmp 2>/dev/null | wc -l')
            rol = 'suscrito' if h == 'Rx-LAB2' else 'observador (no pidió el flujo)'
            lineas.append(f'{arq:12} {h:8} {rol:32} paquetes del grupo {GRUPO}: {datos:>6}   mensajes IGMP: {igmp}')
        lineas.append(f'{arq:12} bytes recibidos por cada equipo (contadores de la interfaz): '
                      + ', '.join(f'{h}={c["host_rx_bytes"][h] / 1e6:.2f} MB' for h in EQUIPOS))
    modo_autonomo(snooping=False)
    texto = '\n'.join(lineas)
    with open(os.path.join(SALIDA, 'resumen.txt'), 'w') as f:
        f.write('Capturas de demostración (1 receptor suscrito, 10 s a 5 Mbit/s). Rx-LAB2 y PC-LAB2 están en el mismo '
                'conmutador (Switch-LAB2).\n\n' + texto + '\n')
    print(texto)


if __name__ == '__main__':
    main()
