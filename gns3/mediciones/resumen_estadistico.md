# Resumen estadístico — mediciones tradicional vs SDN (18/10/2026)

Camino: PC-Aprisco → Switch-Aprisco → Switch-SalonesAntiguos → Router-Fibra → Core-Switch-48p → Servidor-Nucleo (3 OVS).
10 corridas por escenario. Cada corrida: ping de 20 paquetes (latencia) + iperf3 UDP de 10 Mbit/s durante 20 s (jitter y pérdida).
Carga de fondo: UDP de 40 Mbit/s (~70 % de la capacidad medida del camino, ≈60 Mbit/s con TCP; 200 Mbit/s saturaba el emulador).
SDN: Ryu `simple_switch_13`, OpenFlow 1.3, OVS en modo secure. Tradicional: OVS en standalone (acción NORMAL).

| Escenario | Latencia media (ms) ± DE | Jitter medio (ms) ± DE | Pérdida media (%) ± DE |
|---|---|---|---|
| Tradicional sin carga | 25,372 ± 0,854 | 1,737 ± 0,151 | 0,000 ± 0,000 |
| SDN sin carga | 24,677 ± 1,274 | 1,699 ± 0,108 | 0,000 ± 0,000 |
| Tradicional con carga | 21,416 ± 1,930 | 1,779 ± 0,184 | 0,420 ± 0,537 |
| SDN con carga | 18,565 ± 3,107 | 1,683 ± 0,107 | 0,154 ± 0,144 |

Prueba t de Welch (tradicional vs SDN, α = 0,05):

| Nivel | Métrica | t | p | ¿Significativa? |
|---|---|---|---|---|
| Sin carga | Latencia | 1,433 | 0,171 | No |
| Sin carga | Jitter | 0,649 | 0,525 | No |
| Sin carga | Pérdida | — | — | No aplica (0 % en ambos) |
| Con carga | Latencia | 2,466 | 0,026 | **Sí** |
| Con carga | Jitter | 1,436 | 0,172 | No |
| Con carga | Pérdida | 1,514 | 0,160 | No |

Observaciones para interpretar (limitaciones):
- En ambos escenarios la latencia con carga salió MENOR que sin carga: artefacto del emulador (con la CPU ocupada los switches virtuales se atienden más rápido). Los valores sirven para comparar escenarios entre sí, no como cifras de la red real.
- sdn_carga, corrida 5: pico máximo de 108,5 ms (mdev 19,7), aunque la media de esa corrida es normal (24,0 ms).
- Los escenarios se midieron en secuencia (primero el tradicional, después el SDN), no intercalados.
- Flujo UDP unicast; no es multicast nativo.
