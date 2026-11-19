"""Análisis de la réplica del experimento 1 (calidad de servicio con tráfico unicast, orden aleatorio, estrés progresivo).

Uso: python3 gns3/replica_unicast/analizar_replica.py   (TESIS=1: tamaño para el documento; DIAPO=1: una fila, para
     la presentación, en docs/graficas/replica_unicast_diapositiva.png)
Lee gns3/replica_unicast/datos/corridas.jsonl y escribe:
  - gns3/replica_unicast/datos/resumen_replica.md y resumen_replica.csv
  - docs/graficas/[tesis/]replica_unicast.png

Para cada nivel de carga compara SDN con la red tradicional por pares (la repetición es la unidad: en cada una se
midieron ambas arquitecturas en orden aleatorio): diferencia media tradicional - SDN, IC 95 %, t pareada, Wilcoxon y
g de Hedges pareada. Las métricas del flujo de iperf3 solo existen cuando la prueba se completó (en sobrecarga puede no
completarse); se informa cuántas se completaron.
"""
import csv
import json
import math
import os
import statistics as st

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from scipy import stats

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
DATOS = os.environ.get('RU_DATOS', os.path.join(AQUI, 'datos'))
TESIS = os.environ.get('TESIS') == '1'
DIAPO = os.environ.get('DIAPO') == '1'   # versión de una fila para la presentación
SALIDA_GRAF = os.path.join(RAIZ, 'docs', 'graficas', 'tesis' if TESIS else '')
ARQ = {'tradicional': ('Tradicional', '#eb6834', 's'), 'sdn': ('SDN (Ryu)', '#2a78d6', 'o')}
METRICAS = [('latencia_ms', 'Latencia media (ms)'), ('jitter_ms', 'Variación del retardo (ms)'),
            ('perdida_pct', 'Pérdida del flujo de video (%)'), ('ping_perdida_pct', 'Pérdida de ecos ICMP (%)')]
fmt = lambda v, d=2: 'n/d' if v is None or (isinstance(v, float) and math.isnan(v)) else f'{v:.{d}f}'.replace('.', ',')
coma = FuncFormatter(lambda v, _: f'{v:g}'.replace('.', ','))


def cargar():
    with open(os.path.join(DATOS, 'corridas.jsonl')) as f:
        return [json.loads(l) for l in f if l.strip()]


def ic95(x):
    if len(x) < 2:
        return None, None
    m, e = st.mean(x), st.stdev(x) / math.sqrt(len(x)) * stats.t.ppf(0.975, len(x) - 1)
    return m - e, m + e


def pares(filas, carga, metrica):
    v = {(f['rep'], f['arquitectura']): f.get(metrica) for f in filas if f['carga_mbps'] == carga}
    reps = sorted({r for r, _ in v})
    return [(v[(r, 'tradicional')], v[(r, 'sdn')]) for r in reps
            if v.get((r, 'tradicional')) is not None and v.get((r, 'sdn')) is not None]


def comparar(p):
    if len(p) < 3:
        return None
    d = [a - b for a, b in p]
    md = st.mean(d)
    lo, hi = ic95(d)
    sd = st.stdev(d)
    if sd == 0:
        return dict(n=len(d), dif=md, lo=lo, hi=hi, p_t=None, p_w=None, g=None)
    t = stats.ttest_rel([a for a, _ in p], [b for _, b in p])
    try:
        w = stats.wilcoxon(d).pvalue
    except ValueError:
        w = None
    g = md / sd * (1 - 3 / (4 * (len(d) - 1) - 1))
    return dict(n=len(d), dif=md, lo=lo, hi=hi, p_t=t.pvalue, p_w=w, g=g)


def main():
    filas = cargar()
    cargas = sorted({f['carga_mbps'] for f in filas})
    reps = len({f['rep'] for f in filas})
    md = [f'# Réplica del experimento 1 (unicast, orden aleatorio)\n',
          f'Mediciones: {len(filas)} en {reps} repeticiones. Cargas de fondo: '
          + ', '.join(f'{c} Mbit/s' for c in cargas) + '.\n',
          '## Medias por arquitectura y carga (IC 95 %)\n',
          '| Carga (Mbit/s) | Arquitectura | ' + ' | '.join(n for _, n in METRICAS) + ' | iperf3 completado |',
          '|---|---|' + '---|' * len(METRICAS) + '---|']
    csv_filas = [['carga_mbps', 'arquitectura', 'metrica', 'n', 'media', 'de', 'ic_inf', 'ic_sup']]
    for c in cargas:
        for a in ARQ:
            sub = [f for f in filas if f['carga_mbps'] == c and f['arquitectura'] == a]
            celdas = []
            for m, _ in METRICAS:
                x = [f[m] for f in sub if f.get(m) is not None]
                if x:
                    lo, hi = ic95(x)
                    celdas.append(f'{fmt(st.mean(x))} ({fmt(lo)} a {fmt(hi)})' if lo is not None else fmt(st.mean(x)))
                    csv_filas.append([c, a, m, len(x), st.mean(x), st.stdev(x) if len(x) > 1 else '', lo, hi])
                else:
                    celdas.append('n/d')
            ok = sum(1 for f in sub if f.get('jitter_ms') is not None)
            md.append(f'| {c} | {ARQ[a][0]} | ' + ' | '.join(celdas) + f' | {ok} de {len(sub)} |')
    md += ['', '## Comparación por pares (tradicional − SDN; positivo: menor en SDN)\n',
           '| Carga (Mbit/s) | Métrica | n | Diferencia media | IC 95 % | p (t pareada) | p (Wilcoxon) | g |',
           '|---|---|---|---|---|---|---|---|']
    for c in cargas:
        for m, n in METRICAS:
            r = comparar(pares(filas, c, m))
            if r is None:
                md.append(f'| {c} | {n} | — | n/d | — | — | — | — |')
                continue
            p_t = 'n/d' if r['p_t'] is None else ('< 0,001' if r['p_t'] < 0.001 else fmt(r['p_t'], 3))
            p_w = 'n/d' if r['p_w'] is None else ('< 0,001' if r['p_w'] < 0.001 else fmt(r['p_w'], 3))
            md.append(f"| {c} | {n} | {r['n']} | {fmt(r['dif'])} | {fmt(r['lo'])} a {fmt(r['hi'])} | {p_t} | {p_w} | "
                      f"{fmt(r['g'])} |")
    cargas_eq = sorted({f['carga_equipo'][0] for f in filas})
    md += ['', f"Carga del equipo anfitrión durante las mediciones (promedio de 1 minuto): entre {cargas_eq[0]} y "
               f"{cargas_eq[-1]}."]
    texto = '\n'.join(md) + '\n'
    with open(os.path.join(DATOS, 'resumen_replica.md'), 'w') as f:
        f.write(texto)
    with open(os.path.join(DATOS, 'resumen_replica.csv'), 'w', newline='') as f:
        csv.writer(f).writerows(csv_filas)

    # Gráfica: cada métrica frente a la carga, media e IC 95 % por arquitectura
    os.makedirs(SALIDA_GRAF, exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7.5 if TESIS else 9, 'axes.spines.top': False,
                         'axes.spines.right': False, 'axes.grid': True, 'grid.color': '#e4e3df', 'axes.axisbelow': True})
    if DIAPO:
        plt.rcParams['font.size'] = 11
        fig, ejes = plt.subplots(1, 4, figsize=(15, 4.2))
    else:
        fig, ejes = plt.subplots(2, 2, figsize=(6.3, 5.4) if TESIS else (10, 7))
    pos = {c: i for i, c in enumerate(cargas)}
    for ax, (m, n) in zip(ejes.flat, METRICAS):
        for k, (a, (nom, color, marca)) in enumerate(ARQ.items()):
            xs, ys, err = [], [], []
            for c in cargas:
                x = [f[m] for f in filas if f['carga_mbps'] == c and f['arquitectura'] == a and f.get(m) is not None]
                if len(x) < 10:  # en sobrecarga iperf3 casi nunca termina: pocos datos no dan un IC útil
                    continue
                lo, hi = ic95(x)
                xs.append(pos[c] + (k - 0.5) * 0.12)
                ys.append(st.mean(x))
                err.append((hi - lo) / 2 if lo is not None else 0)
            ax.errorbar(xs, ys, yerr=err, color=color, marker=marca, ms=4, lw=1.2, capsize=2, label=nom)
        if m in ('jitter_ms', 'perdida_pct'):
            for c in cargas:
                if sum(1 for f in filas if f['carga_mbps'] == c and f.get(m) is not None) < 20:
                    ax.annotate('sobrecarga:\niperf3 no se\ncompleta', (pos[c], 0.5), xycoords=('data', 'axes fraction'),
                                ha='center', va='center', fontsize=7 if TESIS else 8, color='#6b6a66')
        ax.set_xticks(range(len(cargas)), [str(c) for c in cargas])
        ax.set_xlim(-0.5, len(cargas) - 0.5)
        ax.set_xlabel('Carga de fondo (Mbit/s)')
        ax.set_ylabel(n)
        ax.yaxis.set_major_formatter(coma)
        ax.set_ylim(bottom=0)
    h, l = ejes.flat[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=2, frameon=False)
    fig.tight_layout(rect=(0, 0.09 if DIAPO else 0.05, 1, 1))
    nombre = 'replica_unicast_diapositiva.png' if DIAPO else 'replica_unicast.png'
    fig.savefig(os.path.join(SALIDA_GRAF, nombre), dpi=200 if DIAPO else 300)
    print(texto)


if __name__ == '__main__':
    main()
