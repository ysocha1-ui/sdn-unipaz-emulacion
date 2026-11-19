"""Réplica del experimento 1 (calidad de servicio con tráfico unicast) con orden aleatorio, más repeticiones y estrés
progresivo, en respuesta a las observaciones de los calificadores (Revisión 1): «repetir con orden intercalado o
aleatorio, mayor número de repeticiones, condiciones del equipo controladas y publicar los datos brutos».

Mismo camino que el experimento original (PC-Aprisco -> Switch-Aprisco -> Switch-SalonesAntiguos -> Router-Fibra ->
Core-Switch-48p -> Servidor-Nucleo) y mismas mediciones (20 ecos ICMP; flujo UDP de 10 Mbit/s durante 20 s con iperf3),
ahora sobre la topología completa de los trece bloques:
  tradicional : los 13 OVS en modo autónomo (standalone, acción NORMAL)
  sdn         : los 13 OVS gobernados por Ryu con ryu.app.simple_switch_13, la aplicación del experimento original
Cargas de fondo (UDP, del mismo origen al mismo destino, puerto 5202): 0, 20, 40, 60 y 200 Mbit/s. El camino emulado
soporta unos 60 Mbit/s con TCP; 200 Mbit/s es un nivel de sobrecarga.

Diseño: en cada repetición se miden las 10 condiciones (2 arquitecturas x 5 cargas) en orden aleatorio (semilla = número
de repetición). Tras cada cambio de arquitectura se hace un calentamiento de 3 ecos, igual en ambas, para que el primer
paquete que pasa por el controlador no entre en la medición. Se registra la carga del equipo anfitrión (/proc/loadavg).

Uso:  python3 gns3/replica_unicast/ejecutar_replica_unicast.py [--reps 20] [--cargas 0,20,40,60,200]
Requisitos: entorno preparado con gns3/multicast/preparar_entorno.py. Se puede interrumpir y reanudar.
Datos: gns3/replica_unicast/datos/corridas.jsonl (otra carpeta con la variable RU_DATOS).
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), 'multicast'))
from lib_experimento import CONTROLADOR, CORE, SWITCHES, _esperar_conexion, modo_autonomo  # noqa: E402
from lib_gns3 import sh, sh_bg  # noqa: E402

DATOS = os.environ.get('RU_DATOS', os.path.join(AQUI, 'datos'))
ORIGEN, DESTINO, IP_DESTINO = 'PC-Aprisco', 'Servidor-Nucleo', '172.30.0.12'
RYU = os.environ.get('RYU_MANAGER', os.path.expanduser('~/ryu-controller/venv/bin/ryu-manager'))


def detener_ryu():
    subprocess.run(['pkill', '-f', 'ryu-manager'], capture_output=True)
    time.sleep(1)


def modo_tradicional():
    detener_ryu()
    modo_autonomo(snooping=False)


def modo_sdn(log):
    """Los 13 OVS en modo secure con Ryu (simple_switch_13); primero los bloques y al final el núcleo."""
    detener_ryu()
    for sw in SWITCHES:
        sh(sw, 'ovs-vsctl --if-exists del-controller br0; ovs-vsctl set-fail-mode br0 secure; '
               'ovs-vsctl set bridge br0 mcast_snooping_enable=false; ovs-ofctl -O OpenFlow13 del-flows br0')
    subprocess.Popen([RYU, '--ofp-tcp-listen-port', '6633', 'ryu.app.simple_switch_13'], stdout=open(log, 'a'),
                     stderr=subprocess.STDOUT)
    time.sleep(3)
    bloques = [s for s in SWITCHES if s != CORE]
    for sw in bloques + [CORE]:
        sh(sw, f'ovs-vsctl set-controller br0 {CONTROLADOR}; ovs-vsctl set controller br0 max_backoff=1000 '
               'inactivity_probe=10000')
    _esperar_conexion(SWITCHES)
    time.sleep(2)


def reiniciar_servidores():
    sh(DESTINO, 'pkill iperf3; sleep 0.5; iperf3 -s -D; iperf3 -s -p 5202 -D')
    sh(ORIGEN, 'pkill iperf3')
    time.sleep(1)


def calentar():
    return sh(ORIGEN, f'ping -c 3 -W 2 {IP_DESTINO} >/dev/null 2>&1 && echo ok || echo falla', timeout=30)


def medir(carga):
    """Una medición: carga de fondo (si la hay), 20 ecos ICMP y un flujo UDP de 10 Mbit/s durante 20 s."""
    reiniciar_servidores()
    if carga:
        sh_bg(ORIGEN, f'iperf3 -c {IP_DESTINO} -p 5202 -u -b {carga}M -t 45 >/dev/null 2>&1')
        time.sleep(3)
    ping = sh(ORIGEN, f'ping -c 20 -i 0.2 -W 2 -q {IP_DESTINO}', timeout=60)
    salida = sh(ORIGEN, f'iperf3 -c {IP_DESTINO} -u -b 10M -t 20 -J', timeout=90)
    sh(ORIGEN, 'pkill iperf3')
    r = {'ping_bruto': ping.splitlines()[-2:], 'iperf_error': None}
    m = re.search(r'([\d.]+)% packet loss', ping)
    r['ping_perdida_pct'] = float(m.group(1)) if m else None
    m = re.search(r'= [\d.]+/([\d.]+)/([\d.]+)/([\d.]+) ms', ping)
    r['latencia_ms'], r['latencia_max_ms'], r['latencia_desv_ms'] = (float(x) for x in m.groups()) if m else (None,) * 3
    try:
        j = json.loads(salida[salida.index('{'):])
        if 'error' in j:
            r['iperf_error'] = j['error']
        s = j.get('end', {}).get('sum', {})
        r['jitter_ms'], r['perdida_pct'] = s.get('jitter_ms'), s.get('lost_percent')
        r['paquetes'], r['paquetes_perdidos'] = s.get('packets'), s.get('lost_packets')
    except (ValueError, json.JSONDecodeError):
        r['iperf_error'] = salida[-200:]
        r['jitter_ms'] = r['perdida_pct'] = r['paquetes'] = r['paquetes_perdidos'] = None
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reps', type=int, default=20)
    ap.add_argument('--cargas', default='0,20,40,60,200')
    a = ap.parse_args()
    cargas = [int(x) for x in a.cargas.split(',')]
    os.makedirs(os.path.join(DATOS, 'ryu'), exist_ok=True)
    archivo = os.path.join(DATOS, 'corridas.jsonl')
    hechas = set()
    if os.path.exists(archivo):
        with open(archivo) as f:
            hechas = {json.loads(l)['id'] for l in f if l.strip()}
    actual = None
    for rep in range(1, a.reps + 1):
        plan = [(arq, c) for arq in ('tradicional', 'sdn') for c in cargas]
        random.Random(rep).shuffle(plan)
        for orden, (arq, carga) in enumerate(plan, 1):
            ident = f'r{rep:02d}_{arq}_{carga}'
            if ident in hechas:
                continue
            if arq != actual:
                if arq == 'sdn':
                    modo_sdn(os.path.join(DATOS, 'ryu', f'rep{rep:02d}.log'))
                else:
                    modo_tradicional()
                actual = arq
                calentamiento = calentar()
            else:
                calentamiento = 'sin cambio de arquitectura'
            inicio = time.time()
            r = medir(carga)
            r.update(id=ident, rep=rep, orden_en_repeticion=orden, arquitectura=arq, carga_mbps=carga,
                     calentamiento=calentamiento, carga_equipo=open('/proc/loadavg').read().split()[:3],
                     inicio=inicio, hora=time.strftime('%H:%M:%S'))
            with open(archivo, 'a') as f:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
            print(f"{ident:24} lat={r['latencia_ms']} jit={r['jitter_ms']} perd={r['perdida_pct']} "
                  f"ping_perd={r['ping_perdida_pct']} err={r['iperf_error']}", flush=True)
    modo_tradicional()


if __name__ == '__main__':
    main()
