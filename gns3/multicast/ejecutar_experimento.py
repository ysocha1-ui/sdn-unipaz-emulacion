"""Experimento multicast: tradicional frente a SDN (y un control con el IGMP snooping nativo de OVS), con varios receptores.

Diseño:
  - Hay 12 mediciones por repetición: tradicional (multicast y unicast) x k = 1, 3, 5 receptores suscritos,
    snooping nativo x k, y SDN x k.
  - El ORDEN se aleatoriza dentro de cada repetición (semilla = número de repetición, reproducible): primero el orden
    de los tres bloques (tradicional, snooping, sdn) y dentro de cada bloque el orden de las mediciones. Así ninguna
    arquitectura se mide siempre antes que otra (el experimento anterior midió el tradicional entero y luego el SDN).
  - Cada medición: se leen los contadores, se suscriben los receptores (reportes IGMP), el emisor envía `tasa` durante
    `duracion` s, y se leen de nuevo los contadores y el resumen de iperf2 de cada receptor.
  - Los datos crudos quedan en gns3/multicast/datos/ (una línea JSON por medición). El script se puede interrumpir y
    reanudar: omite las mediciones que ya están registradas.

Uso (con GNS3 y el proyecto abiertos, hosts y conmutadores preparados con preparar_entorno.py):
    python3 gns3/multicast/ejecutar_experimento.py [--reps 10] [--duracion 15] [--tasa 5M] [--ks 1,3,5]
"""
import argparse
import json
import os
import random
import time

from lib_experimento import SWITCHES, corrida, modo_autonomo, modo_sdn, sh, EMISOR, ip_ip

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.environ.get('MC_DATOS', os.path.join(AQUI, 'datos'))
ARCHIVO = os.path.join(DATOS, 'corridas.jsonl')


def hechas():
    if not os.path.exists(ARCHIVO):
        return set()
    with open(ARCHIVO) as f:
        return {json.loads(linea)['id'] for linea in f if linea.strip()}


def plan(rep, ks):
    """Lista ordenada de (arquitectura, tipo, k) de una repetición, con el orden aleatorizado y reproducible."""
    azar = random.Random(rep)
    bloques = {'tradicional': [('multicast', k) for k in ks] + [('unicast', k) for k in ks],
               'snooping': [('multicast', k) for k in ks],
               'sdn': [('multicast', k) for k in ks]}
    orden = list(bloques)
    azar.shuffle(orden)
    salida = []
    for arq in orden:
        med = list(bloques[arq])
        azar.shuffle(med)
        salida += [(arq, tipo, k) for tipo, k in med]
    return salida


def preparar(arq, rep, k):
    if arq == 'tradicional':
        modo_autonomo(snooping=False)
    elif arq == 'snooping':
        modo_autonomo(snooping=True)
    else:
        modo_sdn(os.path.join(DATOS, 'ryu', f'rep{rep:02d}_k{k}.log'))
    for _ in range(5):          # comprobación de salud: debe haber conectividad unicast antes de medir
        if '1 received' in sh(EMISOR, f'ping -c 1 -W 2 {ip_ip("Rx-LAB2")}'):
            return
        time.sleep(2)
    raise RuntimeError(f'Sin conectividad tras preparar {arq}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reps', type=int, default=10)
    ap.add_argument('--duracion', type=int, default=15)
    ap.add_argument('--tasa', default='5M')
    ap.add_argument('--ks', default='1,3,5')
    a = ap.parse_args()
    ks = [int(x) for x in a.ks.split(',')]
    os.makedirs(os.path.join(DATOS, 'ryu'), exist_ok=True)
    ya = hechas()
    total = a.reps * len(plan(1, ks))
    t0 = time.time()
    actual = None
    for rep in range(1, a.reps + 1):
        for orden, (arq, tipo, k) in enumerate(plan(rep, ks), 1):
            ident = f'r{rep:02d}-{arq}-{tipo}-k{k}'
            if ident in ya:
                continue
            for intento in (1, 2):
                try:
                    # En SDN Ryu se reinicia en cada medición (estado de grupos limpio); en los otros modos solo
                    # se reconfigura cuando cambia la arquitectura.
                    if arq == 'sdn' or actual != arq:
                        preparar(arq, rep, k)
                        actual = arq
                    c = corrida(tipo, k, tasa=a.tasa, duracion=a.duracion, volcado_flujos=(rep == 1))
                    break
                except Exception as e:                      # un fallo transitorio se reintenta una vez
                    print(f'[{ident}] intento {intento} falló: {e}', flush=True)
                    actual = None
                    if intento == 2:
                        raise
            c.update(id=ident, rep=rep, arquitectura=arq, orden_en_repeticion=orden, hora=time.strftime('%H:%M:%S'))
            with open(ARCHIVO, 'a') as f:
                f.write(json.dumps(c, ensure_ascii=False) + '\n')
            hechas_n = len(hechas())
            print(f'[{time.strftime("%H:%M:%S")}] {ident} listo ({hechas_n}/{total}, '
                  f'{(time.time() - t0) / 60:.1f} min)', flush=True)
    modo_autonomo(snooping=False)
    print('Experimento terminado.', flush=True)


if __name__ == '__main__':
    main()
