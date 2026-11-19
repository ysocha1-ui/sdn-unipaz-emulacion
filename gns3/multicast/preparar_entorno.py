"""Deja el entorno del experimento multicast listo desde cero (idempotente).

Pasos: construye la imagen de los hosts (iperf2) si falta, abre el proyecto GNS3 del repositorio (o, si no está, lo
importa desde paquete/ con su mismo identificador), agrega los hosts multicast, enciende todos los nodos, da IP de gestión a los 13 conmutadores y IP fija a los hosts.

Requisitos: servidor de GNS3 corriendo en modo local (`gns3server --local`), Docker y las imágenes gns3/ipterm y
gns3/openvswitch. Uso:  python3 gns3/multicast/preparar_entorno.py
"""
import os
import subprocess
import time

from agregar_hosts_multicast import main as agregar_hosts
from lib_experimento import preparar_conmutadores, preparar_hosts
from lib_gns3 import PROYECTO, RUTA_PROYECTO, api, importar_proyecto

AQUI = os.path.dirname(os.path.abspath(__file__))


def main():
    if subprocess.run(['docker', 'image', 'inspect', 'unipaz/ipterm-mc:1'], capture_output=True).returncode:
        print('Construyendo la imagen unipaz/ipterm-mc:1 (iperf2)...')
        subprocess.run(['docker', 'build', '-q', '-t', 'unipaz/ipterm-mc:1', os.path.join(AQUI, 'docker')], check=True)
    proyectos = {p['project_id']: p for p in api('GET', '/projects')}
    if PROYECTO not in proyectos and not os.path.exists(RUTA_PROYECTO):
        print('Importando el proyecto portable (paquete/Fase1-Nucleo-Administrativa.gns3project)...')
        importar_proyecto(os.path.join(AQUI, 'paquete', 'Fase1-Nucleo-Administrativa.gns3project'))
        proyectos = {p['project_id']: p for p in api('GET', '/projects')}
    if PROYECTO not in proyectos:
        print('Abriendo el proyecto GNS3...')
        api('POST', '/projects/load', {'path': RUTA_PROYECTO}, timeout=180)
    elif proyectos[PROYECTO]['status'] != 'opened':
        api('POST', f'/projects/{PROYECTO}/open', {}, timeout=180)
    agregar_hosts()
    print('Encendiendo los nodos...')
    api('POST', f'/projects/{PROYECTO}/nodes/start', {}, timeout=600)
    time.sleep(10)
    print('Conmutadores (IP de gestión):')
    for sw, ip in preparar_conmutadores().items():
        print(f'  {sw:30} {ip}')
    print('Hosts:')
    for h, ip in preparar_hosts().items():
        print(f'  {h:18} {ip}')


if __name__ == '__main__':
    main()
