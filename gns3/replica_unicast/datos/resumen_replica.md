# Réplica del experimento 1 (unicast, orden aleatorio)

Mediciones: 300 en 30 repeticiones. Cargas de fondo: 0 Mbit/s, 20 Mbit/s, 40 Mbit/s, 60 Mbit/s, 200 Mbit/s.

## Medias por arquitectura y carga (IC 95 %)

| Carga (Mbit/s) | Arquitectura | Latencia media (ms) | Variación del retardo (ms) | Pérdida del flujo de video (%) | Pérdida de ecos ICMP (%) | iperf3 completado |
|---|---|---|---|---|---|---|
| 0 | Tradicional | 13,06 (12,52 a 13,60) | 1,43 (1,38 a 1,49) | 0,00 (0,00 a 0,00) | 0,00 (0,00 a 0,00) | 30 de 30 |
| 0 | SDN (Ryu) | 13,16 (12,55 a 13,77) | 1,47 (1,40 a 1,53) | 0,00 (0,00 a 0,00) | 0,00 (0,00 a 0,00) | 30 de 30 |
| 20 | Tradicional | 10,06 (9,23 a 10,89) | 1,53 (1,46 a 1,61) | 0,02 (-0,01 a 0,05) | 0,00 (0,00 a 0,00) | 30 de 30 |
| 20 | SDN (Ryu) | 10,06 (9,16 a 10,96) | 1,51 (1,47 a 1,56) | 0,00 (0,00 a 0,00) | 0,00 (0,00 a 0,00) | 30 de 30 |
| 40 | Tradicional | 10,37 (9,76 a 10,98) | 1,45 (1,40 a 1,50) | 0,02 (-0,01 a 0,05) | 0,00 (0,00 a 0,00) | 30 de 30 |
| 40 | SDN (Ryu) | 10,42 (9,86 a 10,98) | 1,50 (1,42 a 1,58) | 0,14 (0,04 a 0,24) | 0,00 (0,00 a 0,00) | 30 de 30 |
| 60 | Tradicional | 10,53 (10,02 a 11,03) | 1,42 (1,37 a 1,47) | 0,20 (0,02 a 0,39) | 0,17 (-0,17 a 0,51) | 30 de 30 |
| 60 | SDN (Ryu) | 10,41 (9,97 a 10,85) | 1,47 (1,37 a 1,57) | 0,36 (0,25 a 0,47) | 0,17 (-0,17 a 0,51) | 30 de 30 |
| 200 | Tradicional | 22,53 (20,51 a 24,55) | 1,27 (0,86 a 1,67) | 17,38 (-37,93 a 72,68) | 60,83 (56,18 a 65,49) | 4 de 30 |
| 200 | SDN (Ryu) | 21,98 (20,30 a 23,66) | 1,89 (0,84 a 2,94) | 33,32 (-390,07 a 456,71) | 60,17 (55,13 a 65,20) | 2 de 30 |

## Comparación por pares (tradicional − SDN; positivo: menor en SDN)

| Carga (Mbit/s) | Métrica | n | Diferencia media | IC 95 % | p (t pareada) | p (Wilcoxon) | g |
|---|---|---|---|---|---|---|---|
| 0 | Latencia media (ms) | 30 | -0,10 | -0,78 a 0,58 | 0,768 | 0,478 | -0,05 |
| 0 | Variación del retardo (ms) | 30 | -0,03 | -0,09 a 0,03 | 0,313 | 0,556 | -0,18 |
| 0 | Pérdida del flujo de video (%) | 30 | 0,00 | 0,00 a 0,00 | n/d | n/d | n/d |
| 0 | Pérdida de ecos ICMP (%) | 30 | 0,00 | 0,00 a 0,00 | n/d | n/d | n/d |
| 20 | Latencia media (ms) | 30 | -0,00 | -0,82 a 0,81 | 0,999 | 0,465 | -0,00 |
| 20 | Variación del retardo (ms) | 30 | 0,02 | -0,05 a 0,09 | 0,600 | 0,556 | 0,09 |
| 20 | Pérdida del flujo de video (%) | 30 | 0,02 | -0,01 a 0,05 | 0,201 | 0,180 | 0,23 |
| 20 | Pérdida de ecos ICMP (%) | 30 | 0,00 | 0,00 a 0,00 | n/d | n/d | n/d |
| 40 | Latencia media (ms) | 30 | -0,05 | -0,69 a 0,59 | 0,876 | 0,440 | -0,03 |
| 40 | Variación del retardo (ms) | 30 | -0,05 | -0,13 a 0,04 | 0,283 | 0,360 | -0,19 |
| 40 | Pérdida del flujo de video (%) | 30 | -0,12 | -0,22 a -0,01 | 0,030 | 0,050 | -0,41 |
| 40 | Pérdida de ecos ICMP (%) | 30 | 0,00 | 0,00 a 0,00 | n/d | n/d | n/d |
| 60 | Latencia media (ms) | 30 | 0,12 | -0,60 a 0,83 | 0,741 | 0,871 | 0,06 |
| 60 | Variación del retardo (ms) | 30 | -0,05 | -0,17 a 0,06 | 0,360 | 0,685 | -0,17 |
| 60 | Pérdida del flujo de video (%) | 30 | -0,16 | -0,38 a 0,05 | 0,138 | < 0,001 | -0,27 |
| 60 | Pérdida de ecos ICMP (%) | 30 | 0,00 | -0,49 a 0,49 | 1,000 | 1,000 | 0,00 |
| 200 | Latencia media (ms) | 30 | 0,55 | -1,14 a 2,24 | 0,509 | 0,262 | 0,12 |
| 200 | Variación del retardo (ms) | — | n/d | — | — | — | — |
| 200 | Pérdida del flujo de video (%) | — | n/d | — | — | — | — |
| 200 | Pérdida de ecos ICMP (%) | 30 | 0,67 | -6,89 a 8,23 | 0,858 | 0,837 | 0,03 |

Carga del equipo anfitrión durante las mediciones (promedio de 1 minuto): entre 1.88 y 9.42.
