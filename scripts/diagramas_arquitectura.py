"""Diagramas formales de la arquitectura SDN propuesta (apartado 4.2 del documento de grado).

Uso: python3 scripts/diagramas_arquitectura.py
Salida: docs/graficas/tesis/arquitectura_planos.png y docs/graficas/tesis/segmentacion_vlan.png
Sin título interno: el rótulo y la nota APA van en el documento.
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(RAIZ, 'docs', 'graficas', 'tesis')
os.makedirs(OUT, exist_ok=True)
NAVY, AZUL, CLARO, GRIS, GRIS_C, TINTA = '#1F3864', '#2a78d6', '#dfe7f4', '#8c8c8c', '#efefef', '#0b0b0b'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8.5})


def caja(ax, x, y, w, h, texto, fondo='white', borde=NAVY, discontinua=False, negrita=False, tam=8.5, color=TINTA):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.08', fc=fondo, ec=borde,
                                lw=1.2, ls=(0, (4, 3)) if discontinua else '-', zorder=2))
    ax.text(x + w / 2, y + h / 2, texto, ha='center', va='center', fontsize=tam, color=color,
            fontweight='bold' if negrita else 'normal', zorder=3, linespacing=1.3)


def flecha(ax, x1, y1, x2, y2, color=NAVY, discontinua=False, doble=False, lw=1.3):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='<|-|>' if doble else '-|>', mutation_scale=10,
                                 color=color, lw=lw, ls=(0, (4, 3)) if discontinua else '-', zorder=1))


# ------------------------------------------------------------------ 1. arquitectura por planos
fig, ax = plt.subplots(figsize=(7.2, 7.6), dpi=300)
ax.set_xlim(-0.75, 10); ax.set_ylim(0, 10.6); ax.axis('off')

# franjas de los planos
for y, h, nombre in ((8.15, 2.15, 'PLANO DE\nAPLICACIÓN'), (5.55, 1.75, 'PLANO DE\nCONTROL'), (0.2, 4.55, 'PLANO DE\nDATOS')):
    ax.add_patch(FancyBboxPatch((-0.65, y), 10.6, h, boxstyle='round,pad=0,rounding_size=0.1', fc=CLARO, ec='none', zorder=0))
    ax.text(-0.38, y + h / 2, nombre.replace('\n', ' '), ha='center', va='center', rotation=90, fontsize=8,
            fontweight='bold', color=NAVY)

# aplicaciones
caja(ax, 1.7, 8.45, 1.95, 1.0, 'Conmutación\nde capa 2\n(simple_switch_13)', negrita=False)
caja(ax, 3.85, 8.45, 1.85, 1.0, 'Monitoreo de\ntopología y\nestadísticas', discontinua=True)
caja(ax, 5.9, 8.45, 1.85, 1.0, 'Gestión\nmulticast\n(consultor IGMP)')
caja(ax, 7.95, 8.45, 1.85, 1.0, 'Priorización\nde tráfico (QoS)\npor VLAN', discontinua=True)
ax.text(1.3, 7.72, 'Interfaz norte\n(API REST de Ryu)', ha='center', va='center', fontsize=7.5, color=NAVY, style='italic')
for x in (2.67, 4.77, 6.82, 8.87):
    flecha(ax, x, 8.4, x, 7.05, doble=True, discontinua=x in (4.77, 8.87))

# controlador
caja(ax, 2.6, 5.85, 5.2, 1.15, 'Controlador Ryu\nOpenFlow 1.3  ·  tcp/6633  ·  red de gestión VLAN 50', fondo='white', negrita=True, tam=8.3)
ax.text(1.3, 5.12, 'Interfaz sur\n(OpenFlow 1.3)', ha='center', va='center', fontsize=7.5, color=NAVY, style='italic')

# plano de datos: fuera de alcance, núcleo, fibra, bloques
caja(ax, 0.35, 3.75, 2.05, 0.75, 'Firewall Sophos y\nrouter de borde', fondo=GRIS_C, borde=GRIS, color='#444444', tam=7.5)
ax.text(1.37, 3.55, 'fuera del alcance\nde la propuesta', ha='center', va='top', fontsize=6.5, color='#555555', style='italic')
caja(ax, 3.0, 3.75, 2.2, 0.75, 'Conmutador de núcleo\n(Open vSwitch)', negrita=True, tam=7.8)
caja(ax, 5.8, 3.75, 2.2, 0.75, 'Enrutador de fibra\n(distribución)')
flecha(ax, 2.42, 4.12, 2.98, 4.12, color=GRIS, doble=True)
flecha(ax, 5.22, 4.12, 5.78, 4.12, doble=True)
# OpenFlow hacia núcleo y bloques
flecha(ax, 4.1, 5.83, 4.1, 4.52, color=AZUL)
flecha(ax, 7.6, 5.83, 9.0, 4.65, color=AZUL)
ax.text(9.0, 4.5, 'a los conmutadores\nde los 13 bloques', ha='center', va='top', fontsize=6.8, color=AZUL)

directos = ['Salones\nantiguos', 'Núcleo de\nproducción\n(A y B)', 'Portería', 'Laboratorio 3\n(LBA)', 'Biblioteca', 'Edificio\nde Aulas']
xs = [0.45 + i * 1.58 for i in range(6)]
for x, n in zip(xs, directos):
    caja(ax, x, 1.95, 1.4, 0.95, n, tam=7.3)
    flecha(ax, 6.9, 3.73, x + 0.7, 2.92, lw=0.8)
encadenados = [(0, 'Aprisco'), (2, 'Entrada →\nParada de buses'), (3, 'Lab. 1, Lab. 2\ny Psicosocial')]
for i, n in encadenados:
    caja(ax, xs[i], 0.45, 1.4, 0.95, n, tam=7.0, discontinua=False, fondo='#f7f9fc')
    flecha(ax, xs[i] + 0.7, 1.93, xs[i] + 0.7, 1.42, lw=0.8)
ax.text(9.9, 1.0, 'Bloques\nencadenados', ha='right', va='center', fontsize=7, color=NAVY, style='italic')

# leyenda
ax.plot([-0.2, 0.3], [-0.05, -0.05], color=NAVY, lw=1.2); ax.text(0.4, -0.05, 'implementado en la emulación', va='center', fontsize=7)
ax.plot([3.6, 4.1], [-0.05, -0.05], color=NAVY, lw=1.2, ls=(0, (4, 3))); ax.text(4.2, -0.05, 'propuesto (trabajo futuro)', va='center', fontsize=7)
ax.plot([6.6, 7.1], [-0.05, -0.05], color=AZUL, lw=1.3); ax.text(7.2, -0.05, 'sesión OpenFlow', va='center', fontsize=7)
ax.set_ylim(-0.3, 10.45)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'arquitectura_planos.png'))
plt.close(fig)

# ------------------------------------------------------------------ 2. segmentación por VLAN y salida a internet
fig, ax = plt.subplots(figsize=(7.2, 5.0), dpi=300)
ax.set_xlim(0, 10); ax.set_ylim(0, 7); ax.axis('off')
VLAN = [  # (y, número, segmento, subred, salida)
    (6.0, 10, 'Administración', '172.10.0.0/16', 'MC'),
    (4.85, 30, 'Estudiantes', '172.30.0.0/16', 'MC'),
    (3.7, 20, 'Docentes', '172.20.0.0/16', 'UF'),
    (2.55, 70, 'IoT: cámaras, NVR/DVR\ny sensores', '172.70.0.0/16', 'UF'),
    (1.4, 50, 'Gestión y monitoreo', '172.50.0.0/16', 'CT'),
]
for y, n, seg, red, _ in VLAN:
    caja(ax, 0.1, y - 0.42, 3.0, 0.84, f'VLAN {n} · {seg}\n{red}', tam=7.6, negrita=False)
caja(ax, 4.1, 2.6, 1.9, 3.3, 'Red del campus\ngobernada por\nRyu\n\nnúcleo, enrutador\nde fibra y\n13 bloques', fondo=CLARO, negrita=False, tam=7.6)
caja(ax, 4.1, 0.95, 1.9, 0.9, 'Controlador Ryu', fondo='white', negrita=True, tam=7.8)
caja(ax, 6.65, 4.95, 1.25, 1.05, 'Firewall y\nrouter de\nborde', fondo=GRIS_C, borde=GRIS, color='#444444', tam=7)
ax.text(7.27, 4.85, 'fuera del alcance', ha='center', va='top', fontsize=6.3, color='#555555', style='italic')
caja(ax, 8.45, 5.55, 1.5, 0.95, 'Media Commerce\n1 Gbps\n(principal)', negrita=True, tam=7.3)
caja(ax, 8.45, 3.6, 1.5, 0.95, 'Ufinet\n500 Mbps', negrita=True, tam=7.3)
for y, n, *_ in VLAN[:4]:
    flecha(ax, 3.12, y, 4.08, min(max(y, 2.75), 5.75), lw=0.9)
flecha(ax, 3.12, 1.4, 4.08, 1.4, lw=0.9)
flecha(ax, 6.02, 4.25, 6.63, 5.3, lw=1.1)
# salidas por proveedor
flecha(ax, 7.92, 5.75, 8.43, 6.0, lw=1.6)
ax.text(7.75, 6.2, 'VLAN 10 y 30', ha='center', fontsize=6.8, color=NAVY)
flecha(ax, 7.92, 5.15, 8.43, 4.1, lw=1.6)
ax.text(7.7, 4.15, 'VLAN 20 y 70\n(sin respaldo)', ha='center', fontsize=6.8, color=NAVY)
flecha(ax, 9.2, 5.53, 9.2, 4.57, color=AZUL, discontinua=True)
ax.text(9.32, 5.05, 'respaldo de\nVLAN 10 y 30', ha='left', va='center', fontsize=6.5, color=AZUL)
ax.text(5.05, 0.45, 'La VLAN 50 no sale a internet: conecta el controlador con los conmutadores.', ha='center', fontsize=6.8,
        color='#444444', style='italic')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'segmentacion_vlan.png'))
plt.close(fig)
print('ok')
