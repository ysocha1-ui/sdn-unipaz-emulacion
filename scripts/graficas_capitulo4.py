"""Gráficas del capítulo 4: comparación tradicional vs SDN (GNS3) y línea base de la red real (Sophos).

Uso: python3 scripts/graficas_capitulo4.py
Lee gns3/mediciones/{trad,sdn}_{base,carga}.txt y escribe PNG (300 ppp) en docs/graficas/.
Los valores del Sophos salen de docs/INFORME_TRAFICO_SOPHOS.pdf (ventana de 2 h del 15/10/2026, unidades kbit/s).
"""
import os
import re
import statistics as st

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from scipy import stats

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MED = os.path.join(RAIZ, 'gns3', 'mediciones')
# TESIS=1: versión para el documento de grado, sin título ni nota internos (el rótulo y la "Nota." APA van en el Word)
TESIS = os.environ.get('TESIS') == '1'
OUT = os.path.join(RAIZ, 'docs', 'graficas', 'tesis' if TESIS else '')
os.makedirs(OUT, exist_ok=True)

# Paleta: slots 1 y 2 de la paleta categórica de referencia (validada para CVD); forma distinta como
# codificación secundaria, para impresión en escala de grises.
ESC = {
    'trad': dict(nombre='Tradicional', color='#eb6834', marca='s'),
    'sdn': dict(nombre='SDN (Ryu)', color='#2a78d6', marca='o'),
}
NAVY, TINTA, TINTA2, REJILLA = '#1F3864', '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': TINTA2, 'axes.labelcolor': TINTA,
    'xtick.color': TINTA2, 'ytick.color': TINTA2, 'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.color': REJILLA, 'grid.linewidth': 0.6, 'axes.axisbelow': True,
    'axes.titleweight': 'bold', 'axes.titlesize': 10, 'axes.titlecolor': TINTA, 'legend.frameon': False,
})
coma = FuncFormatter(lambda v, _: f'{v:g}'.replace('.', ','))
fmt = lambda v, d=2: f'{v:.{d}f}'.replace('.', ',')


def cargar(nombre):
    t = open(os.path.join(MED, nombre + '.txt')).read()
    return {
        'lat': [float(x) for x in re.findall(r'rtt min/avg/max/mdev = [\d.]+/([\d.]+)/', t)],
        'jit': [float(x) for x in re.findall(r'Mbits/sec\s+([\d.]+) ms', t)],
        'per': [float(x) for x in re.findall(r'\(([\d.e-]+)%\)\s+receiver', t)],
    }


D = {(e, c): cargar(f'{e}_{c}') for e in ESC for c in ('base', 'carga')}
METRICAS = {
    'lat': ('Latencia media (RTT)', 'ms', 'latencia'),
    'jit': ('Variación del retardo', 'ms', 'jitter'),
    'per': ('Pérdida de paquetes', '%', 'perdida'),
}
NIVELES = [('base', 'Sin carga'), ('carga', 'Con carga\n(40 Mbit/s ≈ 70 %)')]


def p_valor(m, c):
    a, b = D[('trad', c)][m], D[('sdn', c)][m]
    if st.pstdev(a) == 0 and st.pstdev(b) == 0:
        return None
    return stats.ttest_ind(a, b, equal_var=False).pvalue


def panel(ax, m):
    titulo, unidad, _ = METRICAS[m]
    for j, (c, etiqueta) in enumerate(NIVELES):
        for k, e in enumerate(ESC):
            lado = -1 if e == 'trad' else 1
            x0 = j + lado * 0.2
            v = D[(e, c)][m]
            dx = [x0 + (i - 4.5) * 0.011 for i in range(len(v))]  # desplazamiento fijo, sin azar
            ax.scatter(dx, v, s=14, marker=ESC[e]['marca'], color=ESC[e]['color'], alpha=0.35,
                       linewidths=0, zorder=2)
            media, de = st.mean(v), st.stdev(v)
            ax.errorbar(x0, media, yerr=de, fmt=ESC[e]['marca'], ms=7, color=ESC[e]['color'],
                        mec='white', mew=1.5, elinewidth=2, capsize=4, capthick=2, zorder=3,
                        label=ESC[e]['nombre'] if j == 0 else None)
            # etiqueta sobre el extremo superior de la barra de error, centrada en su propio marcador
            ax.annotate(fmt(media), (x0, media + de), xytext=(0, 4), textcoords='offset points',
                        va='bottom', ha='center', fontsize=6 if TESIS else 8, color=TINTA)
        p = p_valor(m, c)
        sep = '\n' if TESIS else ' '          # a 16 cm, en dos líneas para que no se monten entre grupos
        txt = (('sin\nvariación' if TESIS else 'sin variación\n(0 % en ambos)') if p is None
               else f'p = {fmt(p, 3)}' + (' *' if p < 0.05 else f'{sep}(n.s.)'))
        ax.text(j, 1.0, txt, transform=ax.get_xaxis_transform(), ha='center', va='bottom', fontsize=6 if TESIS else 8,
                color=TINTA if (p is not None and p < 0.05) else TINTA2,
                fontweight='bold' if (p is not None and p < 0.05) else 'normal')
    ax.set_xticks(range(len(NIVELES)), [n[1] for n in NIVELES])
    ax.set_xlim(-0.75, len(NIVELES) - 0.25)
    ax.set_ylabel(f'{titulo} ({unidad})')
    ax.yaxis.set_major_formatter(coma)
    ax.grid(axis='x', visible=False)
    ax.set_ylim(bottom=0, top=ax.get_ylim()[1] * 1.08)


NOTA = ('Puntos claros: las 10 corridas de cada escenario. Marcador con barra: media ± 1 desviación estándar.\n'
        'p: prueba t de Welch tradicional vs SDN (α = 0,05); * diferencia significativa; n.s. no significativa.')

# Una figura por métrica (para insertarlas por separado en el capítulo 4)
for m, (titulo, unidad, archivo) in METRICAS.items():
    fig, ax = plt.subplots(figsize=(6.3, 3.8), dpi=300)
    panel(ax, m)
    if not TESIS:
        ax.set_title(f'{titulo}: escenario tradicional vs SDN', pad=26, loc='left')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=2)
    if not TESIS:
        fig.text(0.01, 0.005, NOTA, fontsize=6.5, color=TINTA2, va='bottom')
    fig.tight_layout(rect=(0, 0 if TESIS else 0.07, 1, 1))
    fig.savefig(os.path.join(OUT, f'cap4_{archivo}.png'))
    plt.close(fig)

# Figura combinada (tres paneles, cada uno con su propio eje). En el documento va a 16 cm de ancho: se dibuja a ese
# tamaño para que el texto se imprima a su tamaño real y no reducido.
if TESIS:
    plt.rcParams.update({'font.size': 7, 'axes.titlesize': 8})
fig, axs = plt.subplots(1, 3, figsize=(6.3, 3.4) if TESIS else (10, 3.9), dpi=300)
for ax, m in zip(axs, METRICAS):
    panel(ax, m)
    ax.set_title(METRICAS[m][0], pad=26, loc='left')
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, loc='lower center', ncol=2, bbox_to_anchor=(0.5, 0.0 if TESIS else 0.06))
if not TESIS:
    fig.text(0.01, 0.005, NOTA, fontsize=6.5, color=TINTA2, va='bottom')
fig.tight_layout(rect=(0, 0.1 if TESIS else 0.14, 1, 1))
fig.savefig(os.path.join(OUT, 'cap4_resumen_qos.png'))
plt.close(fig)
plt.rcParams.update({'font.size': 9, 'axes.titlesize': 10})   # el resto de figuras, con el tamaño general

# Línea base de la red real (Sophos, ventana de 2 h del 15/10/2026) frente a la carga del experimento
ENLACES = [  # nombre, capacidad (Mbit/s), promedio y pico (kbit/s)
    ('Media Commerce (principal, 1 Gbps)', 1000, 283174.57, 533488.89),
    ('Ufinet (respaldo, 300 Mbps al 15/10)', 300, 58738.94, 227397.46),
]
fig, ax = plt.subplots(figsize=(6.3, 3.0), dpi=300)
alto = 0.34
caja = dict(boxstyle='square,pad=0.15', fc='white', ec='none')
for i, (nom, cap, prom, pico) in enumerate(ENLACES):
    up, ui = prom / 1000 / cap * 100, pico / 1000 / cap * 100
    ax.barh(i - alto / 2 - 0.02, up, height=alto, color='#9fb4d6', label='Promedio' if i == 0 else None)
    ax.barh(i + alto / 2 + 0.02, ui, height=alto, color=NAVY, label='Pico' if i == 0 else None)
    ax.text(up + 1, i - alto / 2 - 0.02, f'{fmt(up, 0)} %  ({fmt(prom / 1000, 0)} Mbit/s)', va='center', fontsize=8, color=TINTA, bbox=caja, zorder=4)
    ax.text(ui + 1, i + alto / 2 + 0.02, f'{fmt(ui, 0)} %  ({fmt(pico / 1000, 0)} Mbit/s)', va='center', fontsize=8, color=TINTA, bbox=caja, zorder=4)
ax.axvline(70, color=TINTA2, lw=1.2, ls='--', zorder=3)
ax.text(70, -0.62, 'Carga del experimento en GNS3 (≈ 70 %)', ha='center', va='bottom', fontsize=7.5, color=TINTA2)
ax.set_yticks(range(len(ENLACES)), [e[0] for e in ENLACES])
ax.set_xlim(0, 100)
ax.set_ylim(1.5, -0.62)
ax.set_xlabel('Utilización del enlace (%)')
ax.grid(axis='y', visible=False)
if not TESIS:
    ax.set_title('Utilización real de los enlaces a internet', loc='left', pad=18)
ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.28), ncol=2, fontsize=8)
if not TESIS:
  fig.text(0.01, 0.005, 'Fuente: informe de tráfico del firewall institucional (Sophos XGS 3300), jueves 15/10/2026, 15:10–17:10. Valores del informe en kbit/s.',
         fontsize=6.5, color=TINTA2, va='bottom')
fig.tight_layout(rect=(0, 0 if TESIS else 0.05, 1, 1))
fig.savefig(os.path.join(OUT, 'cap4_utilizacion_sophos.png'))
plt.close(fig)

print('Generadas en', OUT)
for f in sorted(os.listdir(OUT)):
    if f.startswith('cap4_'):
        print(' ', f)
