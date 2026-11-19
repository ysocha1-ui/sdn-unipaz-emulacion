"""Fase 3 — verificación: los 13 OVS del campus conectados a Ryu y pruebas de conectividad extremo a extremo.

Uso: python3 gns3/fase3/verificar_fase3.py
El resultado se guarda en gns3/fase3/verificacion_fase3.txt (evidencia para el documento).
"""
import os
import subprocess
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, 'verificacion_fase3.txt')
PROYECTO = 'a895d4f8-2166-405c-9885-d8d8d387d508'

OVS = [  # (switch, bloque)
    ('Core-Switch-48p', 'Administrativa (núcleo)'),
    ('Switch-SalonesAntiguos', 'Salones antiguos'),
    ('Switch-Aprisco', 'Aprisco'),
    ('Switch-NucleoProduccion-A', 'Núcleo de producción (troncal A)'),
    ('Switch-NucleoProduccion-B', 'Núcleo de producción (troncal B)'),
    ('Switch-Porteria', 'Portería'),
    ('Switch-Entrada', 'Entrada'),
    ('Switch-ParadaBuses', 'Parada de autobuses'),
    ('Switch-LBA', 'Laboratorio 3 (LBA) + Psicosocial vía NVR-LBA'),
    ('Switch-LAB2', 'Laboratorio 2'),
    ('Switch-LAB1', 'Laboratorio 1'),
    ('Switch-Biblioteca', 'Biblioteca'),
    ('Switch-EdificioAulas', 'Edificio de Aulas'),
]
PINGS = [  # (origen, destino IP, descripción)
    ('PC-LAB2', '172.30.0.12', 'PC-LAB2 → Servidor-Nucleo (bloque más profundo → núcleo)'),
    ('PC-LAB2', '172.30.0.11', 'PC-LAB2 → PC-Aprisco (entre dos ramas encadenadas distintas)'),
    ('Camara-LAB2', '172.70.0.10', 'Camara-LAB2 → NVR-LBA (tráfico de videovigilancia, subred IoT 172.70.0.0/16)'),
]

lineas = []


def out(t=''):
    print(t)
    lineas.append(t)


def sh(nodo, comando):
    r = subprocess.run(['docker', 'exec', f'GNS3.{nodo}.{PROYECTO}', 'sh', '-c', comando],
                       capture_output=True, text=True, timeout=90)
    return (r.stdout + r.stderr).strip()


out(f'===== Verificación Fase 3 — {time.strftime("%Y-%m-%d %H:%M:%S")} =====')
out('\n[1] Estado de los 13 Open vSwitch frente al controlador Ryu (tcp:192.168.122.1:6633)')
out(f'{"Switch":28} {"Bloque":48} {"IP br0":18} {"Modo":9} {"Conectado":10} Reglas')
conectados = 0
for sw, bloque in OVS:
    ip = sh(sw, "ip -4 -o addr show br0 | awk '{print $4}'") or 'SIN IP'
    modo = sh(sw, 'ovs-vsctl get-fail-mode br0')
    con = 'true' in sh(sw, 'ovs-vsctl --columns=is_connected list controller')
    reglas = sh(sw, 'ovs-ofctl -O OpenFlow13 dump-flows br0 | grep -c priority')
    conectados += con
    out(f'{sw:28} {bloque:48} {ip:18} {modo:9} {str(con).lower():10} {reglas}')
out(f'\nTotal conectados a Ryu: {conectados} de {len(OVS)}')

ryu = subprocess.run("ss -tn state established '( sport = :6633 )' | tail -n +2 | wc -l",
                     shell=True, capture_output=True, text=True).stdout.strip()
out(f'Conexiones OpenFlow abiertas en Ryu (puerto 6633): {ryu}')

out('\n[2] Pruebas de conectividad extremo a extremo (ping de 10 paquetes)')
for origen, destino, desc in PINGS:
    r = sh(origen, f'ping -c 10 -i 0.2 -q {destino}')
    res = [l for l in r.splitlines() if 'packet' in l or 'rtt' in l]
    out(f'- {desc}')
    for l in res:
        out(f'    {l}')

out('\n[3] Reglas instaladas por Ryu en el switch de Laboratorio 2 (ruta más profunda)')
out(sh('Switch-LAB2', 'ovs-ofctl -O OpenFlow13 dump-flows br0'))

with open(SALIDA, 'w') as f:
    f.write('\n'.join(lineas) + '\n')
print(f'\nGuardado en {SALIDA}')
