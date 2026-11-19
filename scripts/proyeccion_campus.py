"""Proyección teórica de la demanda a escala del campus (capítulo 4). NO son mediciones: es un cálculo con supuestos explícitos.

Uso: python3 scripts/proyeccion_campus.py
Entradas (todas documentadas):
  - Población: Oficina de Planeación, oct. 2026 (cap. 3): 2780 estudiantes, 150 docentes, 70 administrativos.
  - Uso de Meet (encuesta, cap. 4): 56,1 % de los estudiantes y 83,2 % de los docentes.
  - Tráfico real: informe del firewall Sophos, 15/10/2026 15:10–17:10, zona WAN total: promedio 357,1 y pico 579,7 Mbit/s.
  - Capacidad contratada actual: Media Commerce 1000 + Ufinet 500 = 1500 Mbit/s (Ufinet tenía 300 hasta oct. 2026).
  - Consumo de Meet por participante (Google, support.google.com/a/answer/1279090): 1,3 Mbit/s de bajada
    (organizaciones grandes) y hasta 3,6 Mbit/s en 1080p.
Salida: tabla por consola y docs/graficas/cap4_proyeccion_campus.png
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fmt = lambda v, d=0: f'{v:,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

N_EST, N_DOC, N_ADM = 2780, 150, 70
N = N_EST + N_DOC + N_ADM
USO_MEET_EST, USO_MEET_DOC = 0.561, 0.832
WAN_PROM, WAN_PICO = 357.1, 579.7          # Mbit/s, Sophos
CAP_WAN = 1000 + 500                       # Mbit/s: Ufinet ampliado de 300 a 500 en oct. 2026
CAP_TRONCAL = 1000                         # Mbit/s, enlace Core 48p → Router de fibra (puertos de 1 Gbps del T1600G-52TS)
MEET_BAJO, MEET_ALTO = 1.3, 3.6            # Mbit/s por participante

print('== 1. Demanda por usuario en hora pico (según % de usuarios conectados a la vez)')
for f in (0.10, 0.20, 0.30):
    print(f'  {int(f * 100)} % conectados ({fmt(N * f)} usuarios): {fmt(WAN_PICO / (N * f), 2)} Mbit/s por usuario')

libre = CAP_WAN - WAN_PICO
usuarios_meet = N_EST * USO_MEET_EST + N_DOC * USO_MEET_DOC
print(f'\n== 2. Margen en los enlaces a internet en hora pico: {fmt(libre, 1)} Mbit/s de {CAP_WAN}')
print(f'  Usuarios que declararon usar Meet: {fmt(usuarios_meet)}')
for b in (MEET_BAJO, MEET_ALTO):
    cabe = libre / b
    print(f'  A {fmt(b, 1)} Mbit/s por participante caben {fmt(cabe)} sesiones simultáneas más '
          f'(= {fmt(cabe / usuarios_meet * 100, 1)} % de los usuarios de Meet)')

libre_tr = CAP_TRONCAL - WAN_PICO
print(f'\n== 3. Transmisión institucional desde un servidor interno (escenario teórico)')
print(f'  Margen en la troncal Core → Router de fibra en hora pico: {fmt(libre_tr, 1)} Mbit/s')
for b in (MEET_BAJO, MEET_ALTO):
    print(f'  {fmt(b, 1)} Mbit/s: unicast satura la troncal con {fmt(libre_tr / b)} espectadores; '
          f'multicast usa {fmt(b, 1)} Mbit/s en la troncal sin importar cuántos espectadores haya')

# Gráfica: carga en la troncal según número de espectadores
V = list(range(0, 1001, 10))
fig, ax = plt.subplots(figsize=(6.3, 3.4), dpi=300)
NAVY, TINTA2, REJ = '#1F3864', '#52514e', '#e4e3df'
ax.plot(V, [v * MEET_BAJO for v in V], color='#eb6834', lw=2, label=f'Unicast: una copia por espectador ({fmt(MEET_BAJO, 1)} Mbit/s c/u)')
ax.plot(V, [MEET_BAJO if v else 0 for v in V], color='#2a78d6', lw=2, label='Multicast: una sola copia en la troncal')
ax.axhline(libre_tr, color=TINTA2, lw=1.2, ls='--')
ax.text(995, libre_tr + 30, f'Capacidad libre de la troncal en hora pico ≈ {fmt(libre_tr)} Mbit/s', fontsize=7.5, color=TINTA2,
        ha='right', va='bottom')                     # por encima de la línea, sin tocarla
ax.text(995, MEET_BAJO + 30, f'Multicast: ≈ {fmt(MEET_BAJO, 1)} Mbit/s con cualquier número de espectadores', fontsize=7.5,
        color='#2a78d6', ha='right', va='bottom')
x_sat = libre_tr / MEET_BAJO
ax.plot([x_sat], [libre_tr], marker='o', ms=7, color='#eb6834', mec='white', mew=1.5, zorder=4)
ax.annotate(f'se satura con ≈ {fmt(x_sat)} espectadores', (x_sat, libre_tr), xytext=(10, -22),
            textcoords='offset points', fontsize=7.5, color='#0b0b0b')
ax.set_xlabel('Espectadores simultáneos de una transmisión institucional')
ax.set_ylabel('Carga en la troncal (Mbit/s)')
ax.set_xlim(0, 1000)
ax.set_ylim(0, 1400)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt(v)))
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt(v)))
for s in ('top', 'right'):
    ax.spines[s].set_visible(False)
ax.grid(color=REJ, lw=0.6)
ax.set_axisbelow(True)
TESIS = os.environ.get('TESIS') == '1'  # versión para el documento de grado: sin título ni nota internos
if not TESIS:
  ax.set_title('Proyección teórica: transmisión interna unicast vs multicast', loc='left', fontsize=10, fontweight='bold')
ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=1, fontsize=7.5, frameon=False)
if not TESIS:
  fig.text(0.01, 0.005, 'Estimación con supuestos (no medida): troncal de 1 Gbps; tráfico de fondo = pico real del firewall\n'
         f'({fmt(WAN_PICO)} Mbit/s, 15/10/2026); {fmt(MEET_BAJO, 1)} Mbit/s por espectador (Google).',
         fontsize=6, color=TINTA2, va='bottom')
fig.tight_layout(rect=(0, 0 if TESIS else 0.06, 1, 1))
os.makedirs(os.path.join(RAIZ, 'docs', 'graficas', 'tesis'), exist_ok=True)
salida = os.path.join(RAIZ, 'docs', 'graficas', 'tesis' if TESIS else '', 'cap4_proyeccion_campus.png')
fig.savefig(salida)
print('\nGráfica:', salida)
