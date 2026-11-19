"""Figura 4 del documento de grado: topología del campus emulada en GNS3, dibujada a partir del archivo del proyecto.

Uso: python3 scripts/diagrama_topologia_gns3.py
Salida: docs/graficas/tesis/topologia_gns3.png (16 cm de ancho, texto a tamaño de impresión)

Los nodos y los enlaces se leen de gns3/Fase1-Nucleo-Administrativa/Fase1-Nucleo-Administrativa.gns3, de modo que el
diagrama no puede mostrar un nodo o un enlace que el proyecto no tenga (el script falla si falta alguno). Solo la
disposición es propia, por niveles de la jerarquía física, para que los nombres se lean; la captura del lienzo de GNS3
se conserva en el Apéndice D.
"""
import json
import os
import zipfile

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Patch

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROYECTO = os.path.join(RAIZ, 'gns3', 'Fase1-Nucleo-Administrativa', 'Fase1-Nucleo-Administrativa.gns3')
PORTABLE = os.path.join(RAIZ, 'gns3', 'multicast', 'paquete', 'Fase1-Nucleo-Administrativa.gns3project')
SALIDA = os.path.join(RAIZ, 'docs', 'graficas', 'tesis', 'topologia_gns3.png')
NAVY, GRIS, TINTA, AZUL_C, GRIS_C = '#1F3864', '#7f7f7f', '#0b0b0b', '#dbe6f6', '#efefef'

# Disposición por niveles: (x, y) en unidades del dibujo; y crece hacia abajo
POS = {
    'ISP-Mediacomerce(NAT)': (3.2, 0.0), 'ISP-Ufinet(NAT)': (7.6, 0.0),
    'Raisecom-Mediocomer': (3.2, 1.3), 'Raisecom-Unifet': (7.6, 1.3),
    'Router-Borde': (5.4, 2.6),
    'Servidor-Nucleo': (2.6, 3.9), 'Core-Switch-48p': (5.4, 3.9), 'Emisor-MC': (8.2, 3.9),
    'Router-Fibra': (5.4, 5.2),
    'Switch-NucleoProduccion-A': (0.8, 6.6), 'Switch-NucleoProduccion-B': (2.6, 6.6),
    'Switch-Porteria': (4.3, 6.6), 'Switch-LBA': (7.6, 6.6), 'Switch-SalonesAntiguos': (10.9, 6.6),
    'Switch-Biblioteca': (12.9, 6.6), 'Switch-EdificioAulas': (14.75, 6.6),
    'Switch-Entrada': (4.3, 8.0), 'Switch-LAB1': (5.95, 8.0), 'Switch-LAB2': (7.6, 8.0), 'NVR-LBA': (9.25, 8.0),
    'Switch-Aprisco': (10.9, 8.0), 'Rx-Biblioteca': (12.9, 8.0), 'Rx-Aulas': (14.75, 8.0),
    'Switch-ParadaBuses': (3.4, 9.4), 'Rx-Entrada': (5.1, 9.4),
    'PC-Aprisco': (10.1, 9.4), 'Rx-Aprisco': (11.75, 9.4),
    'PC-LAB2': (5.95, 10.8), 'Camara-LAB2': (7.6, 10.8), 'Rx-LAB2': (9.25, 10.8),
}
MULTICAST = {'Emisor-MC', 'Rx-LAB2', 'Rx-Biblioteca', 'Rx-Entrada', 'Rx-Aprisco', 'Rx-Aulas'}


def rotulo(nombre):
    """Rótulo de la caja: los conmutadores de bloque sin el prefijo «Switch-» (la nota de la figura lo indica) y los
    nombres largos en dos líneas; el resto del nombre es el del nodo en GNS3."""
    if nombre.startswith('Switch-'):
        nombre = nombre[len('Switch-'):]
    for largo, corte in (('NucleoProduccion-', 6), ('SalonesAntiguos', 7), ('EdificioAulas', 8), ('ParadaBuses', 6),
                         ('Raisecom-', 9), ('ISP-', 4), ('Core-Switch-48p', 12), ('Router-', 7), ('Servidor-', 9)):
        if nombre.startswith(largo):
            return nombre[:corte] + '\n' + nombre[corte:]
    return nombre


def estilo(nodo):
    if nodo['node_type'] == 'nat':
        return dict(fc='white', ec=GRIS, ls=(0, (3, 2)), color=TINTA, peso='normal')
    if nodo['node_type'] == 'ethernet_switch':
        return dict(fc=GRIS_C, ec=GRIS, ls='-', color=TINTA, peso='normal')
    if 'openvswitch' in nodo['properties'].get('image', ''):
        return dict(fc=NAVY, ec=NAVY, ls='-', color='white', peso='bold')
    if nodo['name'] in MULTICAST:
        return dict(fc=AZUL_C, ec=NAVY, ls='-', color=TINTA, peso='normal')
    return dict(fc='white', ec=NAVY, ls='-', color=TINTA, peso='normal')


def main():
    if os.path.exists(PROYECTO):
        topo = json.load(open(PROYECTO))['topology']
    else:                                     # sin la carpeta del proyecto: se lee del proyecto portable exportado
        with zipfile.ZipFile(PORTABLE) as z:
            topo = json.loads(z.read('project.gns3'))['topology']
    nodos = {n['node_id']: n for n in topo['nodes']}
    nombres = {n['name'] for n in nodos.values()}
    assert nombres == set(POS), f'nodos sin posición: {nombres - set(POS)}; posiciones sin nodo: {set(POS) - nombres}'

    fig, ax = plt.subplots(figsize=(6.3, 4.9), dpi=300)
    ax.set_xlim(-0.1, 15.6); ax.set_ylim(11.4, -0.5); ax.axis('off')
    bus = []                                   # enlaces del enrutador de fibra a los bloques: bus horizontal
    for l in topo['links']:
        a, b = (nodos[e['node_id']]['name'] for e in l['nodes'])
        if 'Router-Fibra' in (a, b):
            otro = b if a == 'Router-Fibra' else a
            if POS[otro][1] > POS['Router-Fibra'][1]:
                bus.append(POS[otro][0])
                ax.plot([POS[otro][0]] * 2, [5.95, POS[otro][1]], color=GRIS, lw=0.8, zorder=1)
                continue
        (x1, y1), (x2, y2) = POS[a], POS[b]
        ax.plot([x1, x2], [y1, y2], color=GRIS, lw=0.8, zorder=1)
    if bus:
        xf, yf = POS['Router-Fibra']
        ax.plot([xf, xf], [yf, 5.95], color=GRIS, lw=0.8, zorder=1)
        ax.plot([min(bus + [xf]), max(bus + [xf])], [5.95, 5.95], color=GRIS, lw=0.8, zorder=1)
    for n in nodos.values():
        x, y = POS[n['name']]
        e = estilo(n)
        w, h = (1.72 if 'NucleoProduccion' in n['name'] else 1.5), 0.78
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle='round,pad=0.02,rounding_size=0.12',
                                    fc=e['fc'], ec=e['ec'], lw=0.8, ls=e['ls'], zorder=2))
        ax.text(x, y, rotulo(n['name']), ha='center', va='center', fontsize=6.3, color=e['color'],
                fontweight=e['peso'], linespacing=1.1, zorder=3)
    ax.legend(handles=[Patch(fc=NAVY, ec=NAVY, label='Open vSwitch (gobernado por Ryu en SDN)'),
                       Patch(fc=GRIS_C, ec=GRIS, label='Conmutador Ethernet de GNS3'),
                       Patch(fc='white', ec=GRIS, ls='--', label='Salida a internet (NAT)'),
                       Patch(fc='white', ec=NAVY, label='Equipo de prueba'),
                       Patch(fc=AZUL_C, ec=NAVY, label='Emisor y receptores multicast')],
              loc='upper right', bbox_to_anchor=(1.0, 1.0), fontsize=6, frameon=False, ncol=1,
              handlelength=1.6, borderaxespad=0)
    fig.tight_layout(pad=0.2)
    fig.savefig(SALIDA)
    print(SALIDA, len(nodos), 'nodos,', len(topo['links']), 'enlaces')


if __name__ == '__main__':
    main()
