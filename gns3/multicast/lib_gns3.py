"""Utilidades compartidas por los scripts del experimento multicast: API local de GNS3 y comandos dentro de los nodos.

Requiere el servidor de GNS3 en localhost:3080 con el usuario y la clave de ~/.config/GNS3/2.2/gns3_server.conf
(la clave no se escribe en ningún archivo del repositorio).
"""
import base64
import configparser
import json
import os
import subprocess
import urllib.request

API = 'http://localhost:3080/v2'
RUTA_PROYECTO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             'Fase1-Nucleo-Administrativa', 'Fase1-Nucleo-Administrativa.gns3')
PROYECTO = 'a895d4f8-2166-405c-9885-d8d8d387d508'

_cfg = configparser.ConfigParser()
_cfg.read(os.path.expanduser('~/.config/GNS3/2.2/gns3_server.conf'))
_AUTH = 'Basic ' + base64.b64encode(f"{_cfg['Server']['user']}:{_cfg['Server']['password']}".encode()).decode()


def api(metodo, ruta, datos=None, timeout=120):
    req = urllib.request.Request(API + ruta, method=metodo,
                                 data=json.dumps(datos).encode() if datos is not None else None,
                                 headers={'Authorization': _AUTH, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        cuerpo = r.read()
        return json.loads(cuerpo) if cuerpo else None


def importar_proyecto(ruta_zip, proyecto=PROYECTO, nombre='Fase1-Nucleo-Administrativa'):
    """Importa el proyecto portable (.gns3project) conservando su identificador, del que dependen los nombres de los
    contenedores (GNS3.<nodo>.<proyecto>). Se usa cuando el proyecto no está en la carpeta del repositorio."""
    with open(ruta_zip, 'rb') as f:
        req = urllib.request.Request(f'{API}/projects/{proyecto}/import?name={nombre}', method='POST', data=f.read(),
                                     headers={'Authorization': _AUTH})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


def nodos():
    """Diccionario nombre -> nodo del proyecto abierto."""
    return {n['name']: n for n in api('GET', f'/projects/{PROYECTO}/nodes')}


def contenedor(nombre):
    return f'GNS3.{nombre}.{PROYECTO}'


def sh(nodo, comando, timeout=60, check=False):
    """Ejecuta un comando dentro del contenedor del nodo y devuelve stdout+stderr."""
    r = subprocess.run(['docker', 'exec', contenedor(nodo), 'sh', '-c', comando],
                       capture_output=True, text=True, timeout=timeout)
    if check and r.returncode:
        raise RuntimeError(f'{nodo}: {comando!r} -> {r.stderr.strip()}')
    return (r.stdout + r.stderr).strip()


def sh_bg(nodo, comando):
    """Lanza un comando en segundo plano dentro del contenedor (no espera su salida)."""
    return subprocess.Popen(['docker', 'exec', contenedor(nodo), 'sh', '-c', comando],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
