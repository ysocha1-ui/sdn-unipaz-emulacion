"""Demostración en vivo para la sustentación (unos 3 minutos): el mismo flujo multicast con la red tradicional y con SDN.

Un receptor suscrito (Rx-LAB2) y un observador que NO pidió el flujo (PC-LAB2), conectados al mismo conmutador. Con la
red tradicional, el observador recibe el flujo (inundación); con SDN, no recibe nada (poda). Al final muestra la regla
que instaló el controlador en el conmutador de Laboratorio 2.

Uso (con el entorno preparado: gns3server --local y python3 gns3/multicast/preparar_entorno.py):
    python3 gns3/multicast/demo_sustentacion.py
No escribe en los datos publicados del proyecto: el registro del controlador queda en /tmp/demo_ryu.log.
"""
import time

from lib_experimento import GRUPO, corrida, modo_autonomo, modo_sdn, sh, sh_bg

EQUIPOS = [('Rx-LAB2', 'receptor suscrito'), ('PC-LAB2', 'observador (no pidió el flujo)')]


def titulo(t):
    print('\n' + '=' * 72 + f'\n  {t}\n' + '=' * 72, flush=True)


def medir(arquitectura):
    for h, _ in EQUIPOS:
        sh(h, 'pkill tcpdump 2>/dev/null; rm -f /tmp/demo.pcap')
        sh_bg(h, f'tcpdump -i eth0 -s 96 -U -w /tmp/demo.pcap "udp and dst host {GRUPO}"')
    time.sleep(2)
    print(f'  El emisor envía 5 Mbit/s al grupo {GRUPO} durante 10 segundos...', flush=True)
    corrida('multicast', 1, duracion=10)
    for h, _ in EQUIPOS:
        sh(h, 'pkill -INT tcpdump')
    time.sleep(2)
    res = {}
    for h, _ in EQUIPOS:
        res[h] = int(sh(h, 'tcpdump -nr /tmp/demo.pcap 2>/dev/null | wc -l').strip() or 0)
    return res


def main():
    print('Preparando la red (calentamiento de 5 segundos)...', flush=True)
    modo_autonomo(snooping=False)
    corrida('multicast', 1, duracion=5)            # la primera corrida tras encender la emulación sale incompleta

    titulo('1. Red tradicional: los conmutadores deciden solos (el multicast se inunda)')
    trad = medir('tradicional')

    titulo('2. Red SDN: el controlador Ryu gestiona los grupos multicast')
    print('  Conectando los 13 conmutadores al controlador...', flush=True)
    modo_sdn('/tmp/demo_ryu.log')
    sdn = medir('sdn')
    reglas = sh('Switch-LAB2', f'ovs-ofctl -O OpenFlow13 dump-flows br0 | grep {GRUPO}')

    titulo('Resultado: paquetes del grupo multicast que llegaron a cada equipo')
    print(f'  {"Equipo":10} {"Papel":32} {"Tradicional":>12} {"SDN":>8}')
    for h, papel in EQUIPOS:
        print(f'  {h:10} {papel:32} {trad[h]:>12} {sdn[h]:>8}')
    print('\n  Regla que instaló el controlador en Switch-LAB2 (el flujo sale solo por el puerto del receptor):')
    for linea in reglas.splitlines():
        partes = [p for p in linea.split(', ') if p.split('=')[0].strip() in ('n_packets', 'priority') or 'nw_dst' in p
                  or 'actions' in p]
        print('   ', ', '.join(partes) if partes else linea.strip())

    modo_autonomo(snooping=False)                 # deja la red como estaba
    print('\n  Listo. La red quedó otra vez en modo tradicional.')


if __name__ == '__main__':
    main()
