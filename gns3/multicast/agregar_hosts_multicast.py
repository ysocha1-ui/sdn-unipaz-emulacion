"""Agrega al proyecto GNS3 los hosts del experimento multicast: un emisor en el núcleo y cinco receptores repartidos en
bloques directos y encadenados. Usa la imagen unipaz/ipterm-mc:1 (iperf2), que se construye con docker/Dockerfile.

Uso (con el servidor de GNS3 y el proyecto abiertos):  python3 gns3/multicast/agregar_hosts_multicast.py
Es idempotente: si el nodo o el enlace ya existen, no los vuelve a crear.
"""
from lib_gns3 import PROYECTO, api, nodos

PLANTILLA = 'ipterm-mc'
# nombre, conmutador, puerto del conmutador (ethN), IP
HOSTS = [
    ('Emisor-MC', 'Core-Switch-48p', 3, '172.30.0.100/16'),
    ('Rx-LAB2', 'Switch-LAB2', 3, '172.30.0.101/16'),
    ('Rx-Biblioteca', 'Switch-Biblioteca', 1, '172.30.0.103/16'),
    ('Rx-Entrada', 'Switch-Entrada', 2, '172.30.0.105/16'),
    ('Rx-Aprisco', 'Switch-Aprisco', 2, '172.30.0.102/16'),
    ('Rx-Aulas', 'Switch-EdificioAulas', 1, '172.30.0.104/16'),
]


def plantilla():
    for t in api('GET', '/templates'):
        if t['name'] == PLANTILLA:
            return t['template_id']
    base = next(t for t in api('GET', '/templates') if t['name'] == 'ipterm')
    nueva = {k: v for k, v in base.items() if k not in ('template_id', 'symbol', 'builtin')}
    nueva.update(name=PLANTILLA, image='unipaz/ipterm-mc:1', default_name_format='{name}-{0}')
    return api('POST', '/templates', nueva)['template_id']


def main():
    tid = plantilla()
    ns = nodos()
    enlaces = api('GET', f'/projects/{PROYECTO}/links')
    ocupados = {(nd['node_id'], nd['adapter_number']) for l in enlaces for nd in l['nodes']}
    for nombre, sw, puerto, ip in HOSTS:
        if nombre not in ns:
            s = ns[sw]
            n = api('POST', f'/projects/{PROYECTO}/templates/{tid}',
                    {'x': s['x'] + 90, 'y': s['y'] + 110, 'compute_id': 'local'})
            api('PUT', f'/projects/{PROYECTO}/nodes/{n["node_id"]}', {'name': nombre})
            print('creado', nombre)
            ns = nodos()
        h, s = ns[nombre], ns[sw]
        if (s['node_id'], puerto) in ocupados:
            print('enlace ya existe:', nombre, '<->', sw, f'eth{puerto}')
            continue
        api('POST', f'/projects/{PROYECTO}/links', {'nodes': [
            {'node_id': h['node_id'], 'adapter_number': 0, 'port_number': 0},
            {'node_id': s['node_id'], 'adapter_number': puerto, 'port_number': 0}]})
        print('enlazado', nombre, '<->', sw, f'eth{puerto}')


if __name__ == '__main__':
    main()
