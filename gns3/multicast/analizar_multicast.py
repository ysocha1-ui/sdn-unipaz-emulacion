"""Análisis del experimento multicast: resumen por celda, comparaciones por pares entre arquitecturas y gráficas.

Uso: python3 gns3/multicast/analizar_multicast.py          (TESIS=1 para las gráficas sin título interno;
     ARTICULO=1 para la versión en escala de grises y con tramas del artículo, a una columna)
Lee gns3/multicast/datos/corridas.jsonl y escribe:
  - gns3/multicast/datos/resumen_multicast.md y resumen_multicast.csv
  - docs/graficas/[tesis/]mc_*.png (300 ppp)

Por qué comparaciones POR PARES: en cada repetición se midieron todas las arquitecturas, en orden aleatorio, sobre la misma
topología y en un intervalo corto; por eso la unidad de comparación es la repetición y se usa la prueba t pareada (con la
prueba de Wilcoxon como comprobación sin supuesto de normalidad), no la t de Welch para muestras independientes.
"""
import csv
import json
import os
import statistics as st

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from scipy import stats

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
DATOS = os.environ.get('MC_DATOS', os.path.join(AQUI, 'datos'))
ARTICULO = os.environ.get('ARTICULO') == '1'
TESIS = os.environ.get('TESIS') == '1' or ARTICULO
SALIDA_GRAF = os.path.join(RAIZ, 'docs', 'graficas', 'tesis' if TESIS else '')
os.makedirs(SALIDA_GRAF, exist_ok=True)
EMISOR = 'Emisor-MC'

# Paleta: la de las gráficas del capítulo 4 (naranja y azul) más dos colores de la misma familia categórica.
ARQ = {
    ('tradicional', 'multicast'): dict(nombre='Tradicional (sin IGMP snooping)', corto='Tradicional', color='#eb6834', gris='#d9d9d9', trama='', marca='s'),
    ('snooping', 'multicast'): dict(nombre='Snooping nativo de OVS (sin consultor)', corto='Snooping OVS', color='#2f9e6e', gris='#a6a6a6', trama='///', marca='^'),
    ('sdn', 'multicast'): dict(nombre='SDN (Ryu, gestión multicast)', corto='SDN (Ryu)', color='#2a78d6', gris='#595959', trama='', marca='o'),
    ('tradicional', 'unicast'): dict(nombre='Unicast (una copia por receptor)', corto='Unicast', color='#52514e', gris='white', trama='xxx', marca='D'),
}
NAVY, TINTA, TINTA2, REJILLA = '#1F3864', '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': TINTA2, 'axes.labelcolor': TINTA,
    'xtick.color': TINTA2, 'ytick.color': TINTA2, 'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.color': REJILLA, 'grid.linewidth': 0.6, 'axes.axisbelow': True,
    'axes.titleweight': 'bold', 'axes.titlesize': 10, 'axes.titlecolor': TINTA, 'legend.frameon': False,
})
coma = FuncFormatter(lambda v, _: f'{v:g}'.replace('.', ','))
fmt = lambda v, d=2: 'n/d' if v is None else f'{v:.{d}f}'.replace('.', ',')


def cargar():
    filas = []
    with open(os.path.join(DATOS, 'corridas.jsonl')) as f:
        for linea in f:
            c = json.loads(linea)
            suscritos = set(c['suscritos'])
            recibidos = [d for d in c['receptores'].values()]
            validos = [d for d in recibidos if d['perdida_pct'] is not None]
            filas.append({
                'rep': c['rep'], 'arq': c['arquitectura'], 'tipo': c['tipo'], 'k': c['k'],
                'no_pedido_MB': sum(b for h, b in c['host_rx_bytes'].items() if h not in suscritos and h != EMISOR) / 1e6,
                'red_MB': sum(c['puertos_tx_bytes'].values()) / 1e6,
                'emisor_MB': c['emisor_tx_bytes'] / 1e6,
                'recibido_MB': st.mean(d['bytes'] for d in recibidos) / 1e6,
                'perdida_pct': st.mean(d['perdida_pct'] for d in validos) if validos else None,
                'jitter_ms': st.mean(d['jitter_ms'] for d in validos) if validos else None,
                'sin_resumen': len(recibidos) - len(validos),
            })
    return filas


METRICAS = [('no_pedido_MB', 'Recibido por equipos que no lo pidieron', 'MB'),
            ('red_MB', 'Carga total transmitida por los conmutadores', 'MB'),
            ('emisor_MB', 'Transmitido por el emisor', 'MB'),
            ('recibido_MB', 'Recibido por cada receptor suscrito', 'MB'),
            ('perdida_pct', 'Pérdida de paquetes (receptores suscritos)', '%'),
            ('jitter_ms', 'Jitter (receptores suscritos)', 'ms')]


def ic95(x):
    n = len(x)
    if n < 2:
        return (x[0], x[0]) if x else (None, None)
    m, e = st.mean(x), st.stdev(x) / n ** 0.5 * stats.t.ppf(0.975, n - 1)
    return m - e, m + e


def celda(filas, arq, tipo, k, metrica):
    return [f[metrica] for f in sorted(filas, key=lambda f: f['rep'])
            if f['arq'] == arq and f['tipo'] == tipo and f['k'] == k and f[metrica] is not None]


def pares(filas, a, b, k, metrica):
    """Diferencias a - b por repetición (solo repeticiones con ambas mediciones)."""
    da = {f['rep']: f[metrica] for f in filas if (f['arq'], f['tipo']) == a and f['k'] == k and f[metrica] is not None}
    db = {f['rep']: f[metrica] for f in filas if (f['arq'], f['tipo']) == b and f['k'] == k and f[metrica] is not None}
    comunes = sorted(set(da) & set(db))
    return [da[r] for r in comunes], [db[r] for r in comunes]


def comparar(x, y):
    """Prueba t pareada (x - y), IC 95 % de la diferencia media, g de Hedges pareada y Wilcoxon."""
    n = len(x)
    if n < 3:
        return None
    d = [a - b for a, b in zip(x, y)]
    sd = st.stdev(d)
    media = st.mean(d)
    ic = ic95(d)
    if sd == 0:
        t_p = 0.0 if media != 0 else 1.0
        g = None
    else:
        t_p = stats.ttest_rel(x, y).pvalue
        g = media / sd * (1 - 3 / (4 * (n - 1) - 1))
    try:
        w_p = stats.wilcoxon(x, y).pvalue if any(v != 0 for v in d) else 1.0
    except ValueError:
        w_p = None
    ref = st.mean(x)     # la referencia es la primera arquitectura (tradicional, snooping o unicast)
    return {'n': n, 'dif': media, 'ic': ic, 'p_t': t_p, 'p_w': w_p, 'g': g,
            'rel': (media / ref * 100) if ref else None}


def p_txt(p):
    if p is None:
        return 'n/d'
    return '< 0,001' if p < 0.001 else fmt(p, 3)


def tablas(filas, ks):
    md = []
    csv_filas = [['arquitectura', 'tipo', 'k', 'metrica', 'n', 'media', 'sd', 'ic95_inf', 'ic95_sup', 'min', 'max']]
    md.append('## Resultados por arquitectura y número de receptores (media, desviación estándar e IC 95 %)\n')
    for metrica, titulo, unidad in METRICAS:
        md.append(f'### {titulo} ({unidad})\n')
        md.append('| Arquitectura | ' + ' | '.join(f'k = {k}' for k in ks) + ' |')
        md.append('|---|' + '---|' * len(ks))
        for (arq, tipo), meta in ARQ.items():
            if metrica == 'no_pedido_MB' and tipo == 'unicast':
                pass
            celdas = []
            for k in ks:
                x = celda(filas, arq, tipo, k, metrica)
                if not x:
                    celdas.append('—')
                    continue
                lo, hi = ic95(x)
                sd = st.stdev(x) if len(x) > 1 else 0.0
                celdas.append(f'{fmt(st.mean(x), 3 if unidad == "ms" or metrica == "no_pedido_MB" else 2)} ± {fmt(sd, 3)} '
                              f'({fmt(lo, 2)} a {fmt(hi, 2)}; n = {len(x)})')
                csv_filas.append([arq, tipo, k, metrica, len(x), st.mean(x), sd, lo, hi, min(x), max(x)])
            md.append(f'| {meta["nombre"]} | ' + ' | '.join(celdas) + ' |')
        md.append('')
    md.append('## Comparaciones por pares (misma repetición, orden aleatorio)\n')
    md.append('Diferencia = primera arquitectura (referencia) menos SDN. «Reducción» = diferencia media sobre la media de '
              'la referencia: cuánto menos usa SDN. p_t: prueba t pareada; p_W: prueba de Wilcoxon de rangos con signo '
              '(con n = 10 su mínimo posible es 0,002); g: g de Hedges pareada, solo para el jitter: en las métricas de bytes '
              'la variabilidad entre repeticiones es casi nula y el tamaño del efecto no tiene interpretación.\n')
    comparaciones = [
        (('tradicional', 'multicast'), ('sdn', 'multicast'), ['no_pedido_MB', 'red_MB', 'perdida_pct', 'jitter_ms'],
         'Tradicional (sin snooping) − SDN'),
        (('snooping', 'multicast'), ('sdn', 'multicast'), ['no_pedido_MB', 'red_MB', 'perdida_pct', 'jitter_ms'],
         'Snooping nativo de OVS − SDN'),
        (('tradicional', 'unicast'), ('sdn', 'multicast'), ['emisor_MB', 'red_MB'], 'Unicast − multicast gestionado por SDN'),
    ]
    for a, b, mets, titulo in comparaciones:
        md.append(f'### {titulo}\n')
        md.append('| k | Métrica | n | Diferencia media | IC 95 % | Reducción (%) | p_t | p_W | g |')
        md.append('|---|---|---|---|---|---|---|---|---|')
        for k in ks:
            for m in mets:
                u = next(u for mm, _, u in METRICAS if mm == m)
                x, y = pares(filas, a, b, k, m)
                r = comparar(x, y)
                if r is None:
                    continue
                md.append(f'| {k} | {next(t for mm, t, _ in METRICAS if mm == m)} ({u}) | {r["n"]} | {fmt(r["dif"], 3)} | '
                          f'{fmt(r["ic"][0], 3)} a {fmt(r["ic"][1], 3)} | {fmt(r["rel"], 1)} | {p_txt(r["p_t"])} | '
                          f'{p_txt(r["p_w"])} | {fmt(r["g"], 2) if m == "jitter_ms" else "—"} |')
        md.append('')
    return '\n'.join(md), csv_filas


def barras(ax, filas, ks, metrica, claves, ylabel):
    ancho = 0.8 / len(claves)
    for i, clave in enumerate(claves):
        meta = ARQ[clave]
        xs, ys, err = [], [], []
        for j, k in enumerate(ks):
            x = celda(filas, clave[0], clave[1], k, metrica)
            if not x:
                continue
            lo, hi = ic95(x)
            xs.append(j + (i - (len(claves) - 1) / 2) * ancho)
            ys.append(st.mean(x))
            err.append((hi - lo) / 2 if lo is not None else 0)
        estilo = (dict(color=meta['gris'], hatch=meta['trama'], edgecolor='black', linewidth=0.5) if ARTICULO
                  else dict(color=meta['color']))
        ax.bar(xs, ys, ancho * 0.92, yerr=err, capsize=2, error_kw=dict(lw=0.8, ecolor=TINTA2), label=meta['corto'],
               **estilo)
    ax.set_xticks(range(len(ks)))
    ax.set_xticklabels([f'{k}' for k in ks])
    ax.set_xlabel('Receptores suscritos (k)')
    ax.set_ylabel(ylabel)
    ax.yaxis.set_major_formatter(coma)


def graficas(filas, ks):
    multi = [('tradicional', 'multicast'), ('snooping', 'multicast'), ('sdn', 'multicast')]
    todo = multi + [('tradicional', 'unicast')]
    # Para el documento (TESIS=1) los paneles van apilados: con 16 cm de ancho, tres paneles en fila serían ilegibles.
    # El artículo (ARTICULO=1) va a una columna de 8 cm, en blanco y negro como pide su plantilla.
    if ARTICULO:
        plt.rcParams.update({'font.size': 7, 'hatch.linewidth': 0.5})
        fig, ejes = plt.subplots(3, 1, figsize=(3.4, 5.8))
    else:
        fig, ejes = plt.subplots(3, 1, figsize=(6.3, 7.0)) if TESIS else plt.subplots(1, 3, figsize=(11, 3.6))
    barras(ejes[0], filas, ks, 'no_pedido_MB', multi, 'MB recibidos sin haberlos pedido')
    barras(ejes[1], filas, ks, 'red_MB', todo, 'MB transmitidos por los conmutadores')
    barras(ejes[2], filas, ks, 'emisor_MB', [('sdn', 'multicast'), ('tradicional', 'unicast')], 'MB transmitidos por el emisor')
    if not TESIS:
        ejes[0].set_title('Tráfico en equipos que no lo pidieron')
        ejes[1].set_title('Carga total en la red')
        ejes[2].set_title('Carga en el enlace del emisor')
    for j, k in enumerate(ks):                 # las barras de SDN miden casi cero: se rotulan para que se vean
        x = celda(filas, 'sdn', 'multicast', k, 'no_pedido_MB')
        if x:
            ejes[0].annotate(fmt(st.mean(x), 2), (j + 0.8 / 3, st.mean(x)), xytext=(0, 3), textcoords='offset points',
                             ha='center', fontsize=6 if ARTICULO else 7,
                             color='black' if ARTICULO else ARQ[('sdn', 'multicast')]['color'])
    tam = 6 if ARTICULO else 8
    if ARTICULO:
        for ax, etiqueta in zip(ejes, ('MB recibidos\nsin pedirlos', 'MB transmitidos por\nlos conmutadores',
                                       'MB transmitidos\npor el emisor')):
            ax.set_ylabel(etiqueta)
        ejes[0].set_ylim(0, ejes[0].get_ylim()[1] * 1.15)
    ejes[0].legend(loc='upper right', fontsize=tam)
    ejes[1].set_ylim(0, ejes[1].get_ylim()[1] * 1.35)    # espacio para la leyenda sobre las barras
    ejes[1].legend(loc='upper center', fontsize=tam if ARTICULO else 7.5, ncol=2)
    ejes[2].legend(loc='upper left', fontsize=tam)
    fig.tight_layout()
    fig.savefig(os.path.join(SALIDA_GRAF, 'mc_trafico_articulo.png' if ARTICULO else 'mc_trafico.png'), dpi=300)
    plt.close(fig)
    if ARTICULO:
        return

    # La pérdida fue 0 % en todas las mediciones (se informa en el texto); solo se grafica el jitter.
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    barras(ax, filas, ks, 'jitter_ms', todo, 'Jitter (ms)')
    if not TESIS:
        ax.set_title('Jitter en los receptores suscritos')
    ax.set_ylim(0, ax.get_ylim()[1] * 1.3)
    ax.legend(loc='upper center', fontsize=7.5, ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(SALIDA_GRAF, 'mc_qos.png'), dpi=300)
    plt.close(fig)


def main():
    filas = cargar()
    ks = sorted({f['k'] for f in filas})
    reps = len({f['rep'] for f in filas})
    md, csv_filas = tablas(filas, ks)
    sin_resumen = sum(f['sin_resumen'] for f in filas)
    cab = (f'# Resultados del experimento multicast\n\nMediciones: {len(filas)} en {reps} repeticiones; receptores sin resumen '
           f'de iperf2 (excluidos de pérdida y jitter): {sin_resumen}.\n\n')
    with open(os.path.join(DATOS, 'resumen_multicast.md'), 'w') as f:
        f.write(cab + md + '\n')
    with open(os.path.join(DATOS, 'resumen_multicast.csv'), 'w', newline='') as f:
        csv.writer(f).writerows(csv_filas)
    graficas(filas, ks)
    print(cab + md)


if __name__ == '__main__':
    main()
