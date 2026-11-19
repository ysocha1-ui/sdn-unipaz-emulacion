"""Biblioteca del experimento multicast: preparación de la topología, cambio entre arquitecturas y medición.

Arquitecturas que se comparan (todas sobre los MISMOS 13 conmutadores Open vSwitch; solo cambia quién decide el reenvío):
  tradicional  : OVS autónomo (standalone, acción NORMAL) sin IGMP snooping: el multicast se inunda por toda la red.
  snooping     : OVS autónomo con su IGMP snooping nativo habilitado (control: un conmutador tradicional «gestionado»).
  sdn          : OVS en modo secure gobernado por Ryu con la aplicación ryu-apps/gestion_multicast_igmp.py.
"""
import os
import re
import subprocess
import time

from lib_gns3 import api, contenedor, nodos, sh, sh_bg

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APP_RYU = os.path.join(RAIZ, 'ryu-apps', 'gestion_multicast_igmp.py')
CONTROLADOR = 'tcp:192.168.122.1:6633'
GRUPO = '239.10.10.10'

# Los 13 conmutadores, el padre antes que sus hijos (el DHCP de gestión de cada uno pasa por los de arriba).
CORE = 'Core-Switch-48p'
SWITCHES = [CORE, 'Switch-NucleoProduccion-A', 'Switch-NucleoProduccion-B', 'Switch-Porteria', 'Switch-LBA',
            'Switch-Biblioteca', 'Switch-EdificioAulas', 'Switch-SalonesAntiguos', 'Switch-Aprisco', 'Switch-Entrada',
            'Switch-ParadaBuses', 'Switch-LAB2', 'Switch-LAB1']
EMISOR = 'Emisor-MC'
# Receptores en el orden en que se suscriben al aumentar k (el primero es el del bloque más profundo).
RECEPTORES = ['Rx-LAB2', 'Rx-Biblioteca', 'Rx-Entrada', 'Rx-Aprisco', 'Rx-Aulas']
IP = {EMISOR: '172.30.0.100/16', 'Rx-LAB2': '172.30.0.101/16', 'Rx-Aprisco': '172.30.0.102/16',
      'Rx-Biblioteca': '172.30.0.103/16', 'Rx-Aulas': '172.30.0.104/16', 'Rx-Entrada': '172.30.0.105/16'}
# Equipos que nunca se suscriben (observadores): reciben tráfico solo si la red lo inunda.
OBSERVADORES = ['Servidor-Nucleo', 'PC-Aprisco', 'PC-LAB2', 'Camara-LAB2', 'NVR-LBA']
HOSTS = [EMISOR] + RECEPTORES + OBSERVADORES


def ip_ip(valor):
    return IP[valor].split('/')[0]


# ----------------------------------------------------------------------------------------------------------------
# Preparación (una vez por sesión de GNS3)
# ----------------------------------------------------------------------------------------------------------------
def preparar_conmutadores():
    """Deja los 13 OVS en modo autónomo, con IP de gestión (DHCP) y OpenFlow 1.3; el núcleo con dpid = 1 (consultor)."""
    for sw in SWITCHES:
        sh(sw, 'ovs-vsctl --if-exists del-controller br0; ovs-vsctl set-fail-mode br0 standalone; '
               'ovs-vsctl set bridge br0 protocols=OpenFlow13 mcast_snooping_enable=false')
    sh(CORE, 'ovs-vsctl set bridge br0 other-config:datapath-id=0000000000000001')
    time.sleep(2)
    for sw in SWITCHES:
        sh(sw, 'udhcpc -i br0 -n -q -t 5 >/dev/null 2>&1')
    return {sw: sh(sw, "ip -4 -o addr show br0 | awk '{print $4}'") or 'SIN IP' for sw in SWITCHES}


def preparar_hosts():
    """IP fija y ruta multicast en los hosts nuevos (los observadores ya traen su IP persistente)."""
    for h, ip in IP.items():
        d, p = ip.split('/')
        sh(h, f'ip addr flush dev eth0; ip addr add {ip} dev eth0; ip link set eth0 up multicast on')
        sh(h, 'ip route replace 224.0.0.0/4 dev eth0')   # sin esta ruta iperf2 no puede unirse al grupo
    return {h: sh(h, "ip -4 -o addr show eth0 | awk '{print $4}'") for h in HOSTS}


# ----------------------------------------------------------------------------------------------------------------
# Arquitecturas
# ----------------------------------------------------------------------------------------------------------------
def detener_ryu():
    subprocess.run(['pkill', '-f', 'gestion_multicast_igmp'], capture_output=True)
    time.sleep(1)


def modo_autonomo(snooping):
    """Arquitectura tradicional: OVS standalone; con snooping=True se habilita el IGMP snooping nativo de OVS con su
    configuración por defecto (flood de grupos no registrados) y SIN consultor IGMP: OVS no trae uno."""
    detener_ryu()
    flag = 'true' if snooping else 'false'
    for sw in SWITCHES:
        sh(sw, 'ovs-vsctl --if-exists del-controller br0; ovs-vsctl set-fail-mode br0 standalone; '
               f'ovs-vsctl set bridge br0 mcast_snooping_enable={flag} other_config:mcast-snooping-flood-reports={flag} '
               'other_config:mcast-snooping-disable-flood-unregistered=false; '
               'ovs-ofctl -O OpenFlow13 del-flows br0; ovs-ofctl -O OpenFlow13 add-flow br0 priority=0,actions=NORMAL; '
               'ovs-appctl mdb/flush br0 >/dev/null 2>&1')
    time.sleep(1)


def _esperar_conexion(nombres, limite=90):
    for _ in range(limite):
        if all(sh(sw, 'ovs-vsctl get controller br0 is_connected') == 'true' for sw in nombres):
            return
        time.sleep(1)
    raise RuntimeError('Conmutadores sin conectar a Ryu: ' + ', '.join(
        sw for sw in nombres if sh(sw, 'ovs-vsctl get controller br0 is_connected') != 'true'))


def modo_sdn(archivo_log):
    """Arquitectura SDN: Ryu con la aplicación de gestión multicast.

    Orden: primero se conectan los 12 conmutadores de bloque, después el núcleo (consultor) y se espera a que su consulta
    haya alcanzado a todos (cada conmutador registra su «puerto de subida»). Ryu se reinicia en cada llamada para que el
    estado de grupos de la corrida anterior no contamine la siguiente."""
    detener_ryu()
    entorno = dict(os.environ, MC_CONSULTOR_DPID='1')
    log = open(archivo_log, 'w')
    ryu = os.environ.get('RYU_MANAGER', os.path.expanduser('~/ryu-controller/venv/bin/ryu-manager'))
    for sw in SWITCHES:
        sh(sw, 'ovs-vsctl --if-exists del-controller br0; ovs-vsctl set-fail-mode br0 secure; '
               'ovs-vsctl set bridge br0 mcast_snooping_enable=false; ovs-ofctl -O OpenFlow13 del-flows br0')
    subprocess.Popen([ryu, '--ofp-tcp-listen-port', '6633', APP_RYU], stdout=log, stderr=subprocess.STDOUT, env=entorno)
    time.sleep(3)
    bloques = [s for s in SWITCHES if s != CORE]
    for sw in bloques:
        # max_backoff = 1 s: si Ryu todavía no responde, el conmutador reintenta pronto en vez de esperar hasta 8 s
        sh(sw, f'ovs-vsctl set-controller br0 {CONTROLADOR}; ovs-vsctl set controller br0 max_backoff=1000 '
               'inactivity_probe=10000')
    _esperar_conexion(bloques)
    sh(CORE, f'ovs-vsctl set-controller br0 {CONTROLADOR}; ovs-vsctl set controller br0 max_backoff=1000 '
             'inactivity_probe=10000')
    _esperar_conexion([CORE])
    for _ in range(60):                       # la consulta sale 2 s después de conectarse el núcleo
        with open(archivo_log) as f:
            if f.read().count('puerto de subida') >= len(bloques):
                break
        time.sleep(1)
    else:
        raise RuntimeError('No todos los conmutadores aprendieron su puerto de subida (ver ' + archivo_log + ')')
    time.sleep(1)


# ----------------------------------------------------------------------------------------------------------------
# Medición
# ----------------------------------------------------------------------------------------------------------------
def rx_bytes(nombre):
    return int(sh(nombre, 'cat /sys/class/net/eth0/statistics/rx_bytes') or 0)


def tx_bytes(nombre):
    return int(sh(nombre, 'cat /sys/class/net/eth0/statistics/tx_bytes') or 0)


def bytes_en_puertos():
    """Bytes transmitidos por todos los puertos de cada conmutador (excluido el puerto LOCAL)."""
    total = {}
    for sw in SWITCHES:
        salida = sh(sw, 'ovs-ofctl -O OpenFlow13 dump-ports br0')
        # «port  1: rx pkts=..., bytes=..., ... \n tx pkts=..., bytes=...»
        pares = re.findall(r'port\s+(\S+):\s+rx pkts=\d+, bytes=(\d+).*?\n\s+tx pkts=\d+, bytes=(\d+)', salida)
        total[sw] = sum(int(tx) for puerto, rx, tx in pares if puerto != 'LOCAL')
    return total


LINEA_CSV = re.compile(r'^\d+,[\d.]+,\d+,[\d.]+,\d+,\d+,([\d.]+)-([\d.]+),(\d+),(\d+),([\d.]+),(\d+),(\d+),([\d.]+),(\d+)')


def parsear_receptor(texto):
    """Resumen final del servidor iperf2 (salida -y C): bytes, jitter (ms), paquetes perdidos/totales."""
    mejor = None
    for linea in texto.splitlines():
        m = LINEA_CSV.match(linea.strip())
        if m and float(m.group(1)) == 0.0 and (mejor is None or float(m.group(2)) > float(mejor.group(2))):
            mejor = m
    if mejor is None:
        return {'bytes': 0, 'jitter_ms': None, 'perdidos': None, 'total': 0, 'perdida_pct': None}
    return {'bytes': int(mejor.group(3)), 'jitter_ms': float(mejor.group(5)), 'perdidos': int(mejor.group(6)),
            'total': int(mejor.group(7)), 'perdida_pct': float(mejor.group(8))}


# ----------------------------------------------------------------------------------------------------------------
# Una corrida
# ----------------------------------------------------------------------------------------------------------------
def corrida(tipo, k, tasa='5M', duracion=15, volcado_flujos=False):
    """Una medición: `tipo` = 'multicast' (un flujo al grupo) o 'unicast' (un flujo por receptor); k receptores suscritos.

    Devuelve contadores (bytes) de cada host, bytes transmitidos por los puertos de los conmutadores, el resumen de
    iperf2 de cada receptor suscrito y, si se pide, las reglas de flujo de algunos conmutadores (evidencia).
    """
    suscritos = RECEPTORES[:k]
    for sw in SWITCHES:
        sh(sw, 'ovs-appctl mdb/flush br0 >/dev/null 2>&1')      # cada corrida parte sin grupos aprendidos
    for h in HOSTS:
        sh(h, 'pkill iperf 2>/dev/null; rm -f /tmp/rx.csv /tmp/tx.txt')
    antes_h = {h: rx_bytes(h) for h in HOSTS}
    antes_tx_emisor = tx_bytes(EMISOR)
    antes_p = bytes_en_puertos()
    for r in suscritos:   # los receptores arrancan primero: al unirse al grupo envían su reporte IGMP
        servidor = f'-B {GRUPO} ' if tipo == 'multicast' else ''
        sh_bg(r, f'iperf -s -u {servidor}-y C -i 1 -t {duracion + 12} > /tmp/rx.csv 2>&1')
    time.sleep(4)
    t0 = time.time()
    if tipo == 'multicast':
        sh(EMISOR, f'iperf -c {GRUPO} -u -b {tasa} -t {duracion} -T 8 > /tmp/tx.txt 2>&1', timeout=duracion + 30)
    else:
        clientes = [sh_bg(EMISOR, f'iperf -c {ip_ip(r)} -u -b {tasa} -t {duracion} > /tmp/tx_{r}.txt 2>&1')
                    for r in suscritos]
        for c in clientes:
            c.wait(timeout=duracion + 30)
    time.sleep(3)
    flujos = {}
    if volcado_flujos:
        for sw in (CORE, 'Switch-LBA', 'Switch-LAB2', 'Switch-Biblioteca'):
            flujos[sw] = sh(sw, 'ovs-ofctl -O OpenFlow13 dump-flows br0')
    despues_h = {h: rx_bytes(h) for h in HOSTS}
    despues_p = bytes_en_puertos()
    receptores = {r: parsear_receptor(sh(r, 'cat /tmp/rx.csv')) for r in suscritos}
    emisor_tx = tx_bytes(EMISOR) - antes_tx_emisor
    for h in HOSTS:
        sh(h, 'pkill iperf 2>/dev/null')
    return {
        'tipo': tipo, 'k': k, 'tasa': tasa, 'duracion_s': duracion, 'inicio': t0,
        'host_rx_bytes': {h: despues_h[h] - antes_h[h] for h in HOSTS},
        'puertos_tx_bytes': {sw: despues_p[sw] - antes_p[sw] for sw in SWITCHES},
        'emisor_tx_bytes': emisor_tx,
        'receptores': receptores, 'suscritos': suscritos, 'flujos': flujos,
    }


def resumen(c):
    """Texto corto de una corrida, para el piloto."""
    obs = [h for h in HOSTS if h not in c['suscritos'] and h != EMISOR]
    sin_pedir = sum(c['host_rx_bytes'][h] for h in obs)
    lineas = [f"{c['tipo']} k={c['k']}: emisor transmitió {c['emisor_tx_bytes'] / 1e6:.2f} MB; "
              f"total en puertos de conmutadores {sum(c['puertos_tx_bytes'].values()) / 1e6:.2f} MB; "
              f"recibido por equipos que NO lo pidieron {sin_pedir / 1e6:.3f} MB"]
    for r, d in c['receptores'].items():
        lineas.append(f"   {r:14} recibió {d['bytes'] / 1e6:.2f} MB, pérdida {d['perdida_pct']} %, jitter {d['jitter_ms']} ms")
    return '\n'.join(lineas)
