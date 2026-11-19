"""Fase 3 — construye los 10 bloques restantes del campus en el proyecto GNS3 y los conecta a Ryu.

Uso (con GNS3 abierto en el proyecto Fase1-Nucleo-Administrativa y Ryu corriendo):
    python3 gns3/fase3/construir_fase3.py

Usa la API local de GNS3 (localhost:3080) con el usuario/clave de ~/.config/GNS3/2.2/gns3_server.conf
y `docker exec` para configurar cada Open vSwitch. Cada paso queda registrado en gns3/fase3/registro_construccion.txt.
La topología sale de gns3/plan-nodos-enlaces.md (jerarquía del inventario del campus); no inventar nodos intermedios.
"""
import base64
import configparser
import json
import os
import subprocess
import time
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
REGISTRO = os.path.join(AQUI, 'registro_construccion.txt')
API = 'http://localhost:3080/v2'
PROYECTO = 'a895d4f8-2166-405c-9885-d8d8d387d508'
CONTROLADOR = 'tcp:192.168.122.1:6633'
IP_BR0 = "ip -4 -o addr show br0 | awk '{print $4}'"
IP_ETH0 = "ip -4 -o addr show eth0 | awk '{print $4}'"

# Bloques nuevos: nombre, x, y
SWITCHES = [
    ('Switch-NucleoProduccion-A', -330, 360),
    ('Switch-NucleoProduccion-B', -170, 360),
    ('Switch-Porteria', -10, 360),
    ('Switch-LBA', 220, 360),
    ('Switch-Biblioteca', 560, 330),
    ('Switch-EdificioAulas', 720, 280),
    ('Switch-Entrada', -10, 520),
    ('Switch-ParadaBuses', -10, 680),
    ('Switch-LAB2', 140, 520),
    ('Switch-LAB1', 320, 520),
]
# Hosts representativos: nombre, x, y, IP/prefijo
HOSTS = [
    ('NVR-LBA', 440, 430, '172.70.0.10/16'),      # NVR de Laboratorio 3 (recibe también las cámaras de Psicosocial)
    ('PC-LAB2', 60, 680, '172.30.0.21/16'),       # equipo de usuario en el bloque más profundo
    ('Camara-LAB2', 220, 680, '172.70.0.21/16'),  # cámara IP representativa (VLAN 70 IoT)
]
# Enlaces: (nodo A, puerto A, nodo B, puerto B). Router-Fibra es Ethernet switch de GNS3 (puerto N);
# los demás son docker (ethN = adaptador N).
ENLACES = [
    ('Router-Fibra', 2, 'Switch-NucleoProduccion-A', 0),
    ('Router-Fibra', 3, 'Switch-NucleoProduccion-B', 0),
    ('Router-Fibra', 4, 'Switch-Porteria', 0),
    ('Router-Fibra', 5, 'Switch-LBA', 0),
    ('Router-Fibra', 6, 'Switch-Biblioteca', 0),
    ('Router-Fibra', 7, 'Switch-EdificioAulas', 0),
    ('Switch-Porteria', 1, 'Switch-Entrada', 0),
    ('Switch-Entrada', 1, 'Switch-ParadaBuses', 0),
    ('Switch-LBA', 1, 'Switch-LAB2', 0),
    ('Switch-LBA', 2, 'Switch-LAB1', 0),
    ('Switch-LBA', 3, 'NVR-LBA', 0),
    ('Switch-LAB2', 1, 'PC-LAB2', 0),
    ('Switch-LAB2', 2, 'Camara-LAB2', 0),
]

cfg = configparser.ConfigParser()
cfg.read(os.path.expanduser('~/.config/GNS3/2.2/gns3_server.conf'))
AUTH = 'Basic ' + base64.b64encode(f"{cfg['Server']['user']}:{cfg['Server']['password']}".encode()).decode()


def log(texto):
    print(texto)
    with open(REGISTRO, 'a') as f:
        f.write(texto + '\n')


def api(metodo, ruta, datos=None):
    req = urllib.request.Request(API + ruta, method=metodo,
                                 data=json.dumps(datos).encode() if datos is not None else None,
                                 headers={'Authorization': AUTH, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        cuerpo = r.read()
        return json.loads(cuerpo) if cuerpo else None


def sh(nodo, comando):
    r = subprocess.run(['docker', 'exec', f'GNS3.{nodo}.{PROYECTO}', 'sh', '-c', comando],
                       capture_output=True, text=True, timeout=60)
    return (r.stdout + r.stderr).strip()


def plantilla(nombre):
    return next(t['template_id'] for t in api('GET', '/templates') if t['name'] == nombre)


def nodos():
    return {n['name']: n for n in api('GET', f'/projects/{PROYECTO}/nodes')}


def crear(nombre, x, y, tid, existentes):
    if nombre in existentes:
        log(f'  ya existe: {nombre}')
        return
    n = api('POST', f'/projects/{PROYECTO}/templates/{tid}', {'x': x, 'y': y, 'compute_id': 'local'})
    api('PUT', f'/projects/{PROYECTO}/nodes/{n["node_id"]}', {'name': nombre})
    log(f'  creado: {nombre}')


def puerto(nodo, num):
    if nodo['node_type'] == 'ethernet_switch':
        return {'node_id': nodo['node_id'], 'adapter_number': 0, 'port_number': num}
    return {'node_id': nodo['node_id'], 'adapter_number': num, 'port_number': 0}


def main():
    log(f'===== Construcción Fase 3 — {time.strftime("%Y-%m-%d %H:%M:%S")} =====')

    log('\n[1] Crear nodos')
    existentes = nodos()
    t_ovs, t_ipterm = plantilla('Open vSwitch'), plantilla('ipterm')
    for nombre, x, y in SWITCHES:
        crear(nombre, x, y, t_ovs, existentes)
    for nombre, x, y, _ in HOSTS:
        crear(nombre, x, y, t_ipterm, existentes)

    log('\n[2] Cablear')
    ns = nodos()
    ocupados = {(e['node_id'], e['adapter_number'], e['port_number'])
                for l in api('GET', f'/projects/{PROYECTO}/links') for e in l['nodes']}
    for a, pa, b, pb in ENLACES:
        ea, eb = puerto(ns[a], pa), puerto(ns[b], pb)
        if tuple(ea.values()) in ocupados or tuple(eb.values()) in ocupados:
            log(f'  ya cableado: {a}:{pa} <-> {b}:{pb}')
            continue
        api('POST', f'/projects/{PROYECTO}/links', {'nodes': [ea, eb]})
        log(f'  enlace: {a} (puerto {pa}) <-> {b} (eth{pb})')

    log('\n[3] Encender nodos nuevos')
    for nombre in [s[0] for s in SWITCHES] + [h[0] for h in HOSTS]:
        if ns[nombre]['status'] != 'started':
            api('POST', f'/projects/{PROYECTO}/nodes/{ns[nombre]["node_id"]}/start', {})
        log(f'  encendido: {nombre}')
    time.sleep(8)

    log('\n[4] IP de gestión (DHCP) y OpenFlow 1.3 en cada OVS nuevo')
    for nombre, _, _ in SWITCHES:  # en orden de arriba hacia abajo: el padre primero
        sh(nombre, 'udhcpc -i br0 -n -q -t 5 >/dev/null 2>&1; ovs-vsctl set bridge br0 protocols=OpenFlow13')
        log(f'  {nombre}: br0 = {sh(nombre, IP_BR0) or "SIN IP"}')

    log('\n[5] Modo SDN: fail-mode secure + controlador Ryu')
    for nombre, _, _ in SWITCHES:
        sh(nombre, f'ovs-vsctl set-fail-mode br0 secure; ovs-vsctl set-controller br0 {CONTROLADOR}')
    time.sleep(5)

    log('\n[6] IP fija de los hosts representativos (persistente en /etc/network/interfaces)')
    for nombre, _, _, ip in HOSTS:
        direccion, pref = ip.split('/')
        mascara = '255.255.0.0' if pref == '16' else '255.255.255.0'
        sh(nombre, f'printf "auto eth0\\niface eth0 inet static\\n\\taddress {direccion}\\n\\tnetmask {mascara}\\n" '
                   f'> /etc/network/interfaces; ip addr flush dev eth0; ip addr add {ip} dev eth0; ip link set eth0 up')
        log(f'  {nombre}: {sh(nombre, IP_ETH0)}')

    log('\nListo. Verificar con: python3 gns3/fase3/verificar_fase3.py')


if __name__ == '__main__':
    main()
