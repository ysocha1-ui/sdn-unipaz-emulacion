# Resultados del experimento multicast

Mediciones: 120 en 10 repeticiones; receptores sin resumen de iperf2 (excluidos de pérdida y jitter): 0.

## Resultados por arquitectura y número de receptores (media, desviación estándar e IC 95 %)

### Recibido por equipos que no lo pidieron (MB)

| Arquitectura | k = 1 | k = 3 | k = 5 |
|---|---|---|---|
| Tradicional (sin IGMP snooping) | 91,055 ± 0,002 (91,05 a 91,06; n = 10) | 70,821 ± 0,002 (70,82 a 70,82; n = 10) | 50,587 ± 0,002 (50,59 a 50,59; n = 10) |
| Snooping nativo de OVS (sin consultor) | 70,816 ± 0,005 (70,81 a 70,82; n = 10) | 50,583 ± 0,002 (50,58 a 50,58; n = 10) | 20,233 ± 0,001 (20,23 a 20,23; n = 10) |
| SDN (Ryu, gestión multicast) | 0,013 ± 0,019 (-0,00 a 0,03; n = 10) | 0,005 ± 0,001 (0,00 a 0,01; n = 10) | 0,004 ± 0,002 (0,00 a 0,01; n = 10) |
| Unicast (una copia por receptor) | 0,000 ± 0,000 (-0,00 a 0,00; n = 10) | 0,735 ± 2,322 (-0,93 a 2,40; n = 10) | 4,349 ± 7,003 (-0,66 a 9,36; n = 10) |

### Carga total transmitida por los conmutadores (MB)

| Arquitectura | k = 1 | k = 3 | k = 5 |
|---|---|---|---|
| Tradicional (sin IGMP snooping) | 172,06 ± 0,004 (172,06 a 172,07; n = 10) | 172,07 ± 0,005 (172,06 a 172,07; n = 10) | 172,07 ± 0,007 (172,06 a 172,07; n = 10) |
| Snooping nativo de OVS (sin consultor) | 151,82 ± 0,010 (151,81 a 151,83; n = 10) | 141,70 ± 0,006 (141,70 a 141,71; n = 10) | 131,59 ± 0,007 (131,58 a 131,59; n = 10) |
| SDN (Ryu, gestión multicast) | 30,56 ± 0,162 (30,44 a 30,67; n = 10) | 60,86 ± 0,016 (60,85 a 60,88; n = 10) | 91,22 ± 0,024 (91,21 a 91,24; n = 10) |
| Unicast (una copia por receptor) | 30,42 ± 0,004 (30,42 a 30,43; n = 10) | 82,50 ± 4,646 (79,18 a 85,82; n = 10) | 140,32 ± 13,999 (130,31 a 150,34; n = 10) |

### Transmitido por el emisor (MB)

| Arquitectura | k = 1 | k = 3 | k = 5 |
|---|---|---|---|
| Tradicional (sin IGMP snooping) | 10,12 ± 0,000 (10,12 a 10,12; n = 10) | 10,12 ± 0,000 (10,12 a 10,12; n = 10) | 10,12 ± 0,000 (10,12 a 10,12; n = 10) |
| Snooping nativo de OVS (sin consultor) | 10,12 ± 0,001 (10,12 a 10,12; n = 10) | 10,12 ± 0,000 (10,12 a 10,12; n = 10) | 10,12 ± 0,000 (10,12 a 10,12; n = 10) |
| SDN (Ryu, gestión multicast) | 10,12 ± 0,001 (10,12 a 10,12; n = 10) | 10,12 ± 0,001 (10,12 a 10,12; n = 10) | 10,12 ± 0,000 (10,12 a 10,12; n = 10) |
| Unicast (una copia por receptor) | 10,12 ± 0,001 (10,12 a 10,12; n = 10) | 30,36 ± 0,002 (30,36 a 30,36; n = 10) | 50,60 ± 0,004 (50,59 a 50,60; n = 10) |

### Recibido por cada receptor suscrito (MB)

| Arquitectura | k = 1 | k = 3 | k = 5 |
|---|---|---|---|
| Tradicional (sin IGMP snooping) | 9,84 ± 0,000 (9,84 a 9,84; n = 10) | 9,84 ± 0,000 (9,84 a 9,84; n = 10) | 9,84 ± 0,000 (9,84 a 9,84; n = 10) |
| Snooping nativo de OVS (sin consultor) | 9,84 ± 0,001 (9,84 a 9,84; n = 10) | 9,84 ± 0,000 (9,84 a 9,84; n = 10) | 9,84 ± 0,000 (9,84 a 9,84; n = 10) |
| SDN (Ryu, gestión multicast) | 9,84 ± 0,001 (9,84 a 9,84; n = 10) | 9,84 ± 0,001 (9,84 a 9,84; n = 10) | 9,84 ± 0,000 (9,84 a 9,84; n = 10) |
| Unicast (una copia por receptor) | 9,84 ± 0,000 (9,84 a 9,84; n = 10) | 9,84 ± 0,000 (9,84 a 9,84; n = 10) | 9,84 ± 0,000 (9,84 a 9,84; n = 10) |

### Pérdida de paquetes (receptores suscritos) (%)

| Arquitectura | k = 1 | k = 3 | k = 5 |
|---|---|---|---|
| Tradicional (sin IGMP snooping) | 0,00 ± 0,000 (0,00 a 0,00; n = 10) | 0,00 ± 0,000 (0,00 a 0,00; n = 10) | 0,00 ± 0,000 (0,00 a 0,00; n = 10) |
| Snooping nativo de OVS (sin consultor) | 0,00 ± 0,000 (0,00 a 0,00; n = 10) | 0,00 ± 0,000 (0,00 a 0,00; n = 10) | 0,00 ± 0,000 (0,00 a 0,00; n = 10) |
| SDN (Ryu, gestión multicast) | 0,00 ± 0,000 (0,00 a 0,00; n = 10) | 0,00 ± 0,000 (0,00 a 0,00; n = 10) | 0,00 ± 0,000 (0,00 a 0,00; n = 10) |
| Unicast (una copia por receptor) | 0,00 ± 0,000 (0,00 a 0,00; n = 10) | 0,00 ± 0,000 (0,00 a 0,00; n = 10) | 0,00 ± 0,000 (0,00 a 0,00; n = 10) |

### Jitter (receptores suscritos) (ms)

| Arquitectura | k = 1 | k = 3 | k = 5 |
|---|---|---|---|
| Tradicional (sin IGMP snooping) | 3,303 ± 0,211 (3,15 a 3,45; n = 10) | 3,309 ± 0,150 (3,20 a 3,42; n = 10) | 3,344 ± 0,120 (3,26 a 3,43; n = 10) |
| Snooping nativo de OVS (sin consultor) | 3,046 ± 0,548 (2,65 a 3,44; n = 10) | 2,888 ± 0,181 (2,76 a 3,02; n = 10) | 2,882 ± 0,118 (2,80 a 2,97; n = 10) |
| SDN (Ryu, gestión multicast) | 1,711 ± 0,199 (1,57 a 1,85; n = 10) | 1,759 ± 0,302 (1,54 a 1,97; n = 10) | 1,901 ± 0,313 (1,68 a 2,13; n = 10) |
| Unicast (una copia por receptor) | 0,190 ± 0,077 (0,13 a 0,24; n = 10) | 0,718 ± 0,154 (0,61 a 0,83; n = 10) | 1,630 ± 0,222 (1,47 a 1,79; n = 10) |

## Comparaciones por pares (misma repetición, orden aleatorio)

Diferencia = primera arquitectura (referencia) menos SDN. «Reducción» = diferencia media sobre la media de la referencia: cuánto menos usa SDN. p_t: prueba t pareada; p_W: prueba de Wilcoxon de rangos con signo (con n = 10 su mínimo posible es 0,002); g: g de Hedges pareada, solo para el jitter: en las métricas de bytes la variabilidad entre repeticiones es casi nula y el tamaño del efecto no tiene interpretación.

### Tradicional (sin snooping) − SDN

| k | Métrica | n | Diferencia media | IC 95 % | Reducción (%) | p_t | p_W | g |
|---|---|---|---|---|---|---|---|---|
| 1 | Recibido por equipos que no lo pidieron (MB) | 10 | 91,042 | 91,027 a 91,056 | 100,0 | < 0,001 | 0,002 | — |
| 1 | Carga total transmitida por los conmutadores (MB) | 10 | 141,505 | 141,387 a 141,622 | 82,2 | < 0,001 | 0,002 | — |
| 1 | Pérdida de paquetes (receptores suscritos) (%) | 10 | 0,000 | 0,000 a 0,000 | n/d | 1,000 | 1,000 | — |
| 1 | Jitter (receptores suscritos) (ms) | 10 | 1,593 | 1,433 a 1,753 | 48,2 | < 0,001 | 0,002 | 6,51 |
| 3 | Recibido por equipos que no lo pidieron (MB) | 10 | 70,816 | 70,814 a 70,817 | 100,0 | < 0,001 | 0,002 | — |
| 3 | Carga total transmitida por los conmutadores (MB) | 10 | 111,200 | 111,187 a 111,213 | 64,6 | < 0,001 | 0,002 | — |
| 3 | Pérdida de paquetes (receptores suscritos) (%) | 10 | 0,000 | 0,000 a 0,000 | n/d | 1,000 | 1,000 | — |
| 3 | Jitter (receptores suscritos) (ms) | 10 | 1,551 | 1,273 a 1,829 | 46,9 | < 0,001 | 0,002 | 3,65 |
| 5 | Recibido por equipos que no lo pidieron (MB) | 10 | 50,583 | 50,581 a 50,585 | 100,0 | < 0,001 | 0,002 | — |
| 5 | Carga total transmitida por los conmutadores (MB) | 10 | 80,843 | 80,825 a 80,862 | 47,0 | < 0,001 | 0,002 | — |
| 5 | Pérdida de paquetes (receptores suscritos) (%) | 10 | 0,000 | 0,000 a 0,000 | n/d | 1,000 | 1,000 | — |
| 5 | Jitter (receptores suscritos) (ms) | 10 | 1,443 | 1,222 a 1,663 | 43,1 | < 0,001 | 0,002 | 4,28 |

### Snooping nativo de OVS − SDN

| k | Métrica | n | Diferencia media | IC 95 % | Reducción (%) | p_t | p_W | g |
|---|---|---|---|---|---|---|---|---|
| 1 | Recibido por equipos que no lo pidieron (MB) | 10 | 70,803 | 70,786 a 70,819 | 100,0 | < 0,001 | 0,002 | — |
| 1 | Carga total transmitida por los conmutadores (MB) | 10 | 121,260 | 121,139 a 121,381 | 79,9 | < 0,001 | 0,002 | — |
| 1 | Pérdida de paquetes (receptores suscritos) (%) | 10 | 0,000 | 0,000 a 0,000 | n/d | 1,000 | 1,000 | — |
| 1 | Jitter (receptores suscritos) (ms) | 10 | 1,335 | 0,985 a 1,685 | 43,8 | < 0,001 | 0,002 | 2,50 |
| 3 | Recibido por equipos que no lo pidieron (MB) | 10 | 50,578 | 50,576 a 50,580 | 100,0 | < 0,001 | 0,002 | — |
| 3 | Carga total transmitida por los conmutadores (MB) | 10 | 80,839 | 80,824 a 80,853 | 57,0 | < 0,001 | 0,002 | — |
| 3 | Pérdida de paquetes (receptores suscritos) (%) | 10 | 0,000 | 0,000 a 0,000 | n/d | 1,000 | 1,000 | — |
| 3 | Jitter (receptores suscritos) (ms) | 10 | 1,129 | 0,856 a 1,403 | 39,1 | < 0,001 | 0,002 | 2,70 |
| 5 | Recibido por equipos que no lo pidieron (MB) | 10 | 20,229 | 20,227 a 20,231 | 100,0 | < 0,001 | 0,002 | — |
| 5 | Carga total transmitida por los conmutadores (MB) | 10 | 40,364 | 40,348 a 40,380 | 30,7 | < 0,001 | 0,002 | — |
| 5 | Pérdida de paquetes (receptores suscritos) (%) | 10 | 0,000 | 0,000 a 0,000 | n/d | 1,000 | 1,000 | — |
| 5 | Jitter (receptores suscritos) (ms) | 10 | 0,981 | 0,785 a 1,177 | 34,0 | < 0,001 | 0,002 | 3,28 |

### Unicast − multicast gestionado por SDN

| k | Métrica | n | Diferencia media | IC 95 % | Reducción (%) | p_t | p_W | g |
|---|---|---|---|---|---|---|---|---|
| 1 | Transmitido por el emisor (MB) | 10 | 0,002 | 0,001 a 0,004 | 0,0 | < 0,001 | 0,002 | — |
| 1 | Carga total transmitida por los conmutadores (MB) | 10 | -0,135 | -0,251 a -0,018 | -0,4 | 0,028 | 0,002 | — |
| 3 | Transmitido por el emisor (MB) | 10 | 20,242 | 20,240 a 20,244 | 66,7 | < 0,001 | 0,002 | — |
| 3 | Carga total transmitida por los conmutadores (MB) | 10 | 21,633 | 18,309 a 24,958 | 26,2 | < 0,001 | 0,002 | — |
| 5 | Transmitido por el emisor (MB) | 10 | 40,479 | 40,475 a 40,482 | 80,0 | < 0,001 | 0,002 | — |
| 5 | Carga total transmitida por los conmutadores (MB) | 10 | 49,099 | 39,079 a 59,119 | 35,0 | < 0,001 | 0,002 | — |

