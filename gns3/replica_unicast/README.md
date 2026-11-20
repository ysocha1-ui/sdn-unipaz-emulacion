# Réplica del experimento 1: calidad de servicio con tráfico unicast

Documento: apartados **4.4 y 4.5** (Tablas 7 y 8, Figura 6). La primera serie se resume en 4.5.

La primera serie del experimento 1 ([`../fase2/`](../fase2/), datos en [`../mediciones/`](../mediciones/)) se midió en
secuencia: primero la red tradicional y después la SDN, con diez repeticiones. Los calificadores pidieron repetirla con
orden aleatorio, más repeticiones y condiciones del equipo controladas, y publicar los datos crudos. Esta carpeta
contiene esa réplica.

## Diseño

| Elemento | Valor |
|---|---|
| Camino | `PC-Aprisco` (172.30.0.11) → Switch-Aprisco → Switch-SalonesAntiguos → Router-Fibra → Core-Switch-48p → `Servidor-Nucleo` (172.30.0.12), sobre la topología completa de los trece bloques |
| Tradicional | los 13 Open vSwitch en modo autónomo (`standalone`, acción NORMAL), sin IGMP snooping |
| SDN | los 13 Open vSwitch en modo `secure`, gobernados por Ryu con `ryu.app.simple_switch_13` (la aplicación de la primera serie) |
| Cargas de fondo | 0, 20, 40, 60 y 200 Mbit/s (UDP, mismo origen y destino, puerto 5202). El camino soporta unos 60 Mbit/s con TCP: 200 Mbit/s es sobrecarga |
| Medición | 20 ecos ICMP (`ping -i 0.2`) para la latencia y un flujo UDP de 10 Mbit/s durante 20 s (`iperf3 -u -b 10M -t 20 -J`) para la variación del retardo y la pérdida |
| Repeticiones | 30; en cada una, las 10 combinaciones (2 arquitecturas × 5 cargas) en **orden aleatorio** (semilla = número de repetición). Total: 300 mediciones |
| Control | tras cada cambio de arquitectura, 3 ecos de calentamiento (igual en las dos) para que la instalación de las primeras reglas no entre en la medición; en cada medición se registra la carga del equipo anfitrión (`/proc/loadavg`) |
| Análisis | por pares, con la repetición como unidad: diferencia tradicional − SDN, IC 95 %, t para muestras relacionadas, Wilcoxon y g de Hedges |

## Resultado

| Carga (Mbit/s) | Latencia trad. (ms) | Latencia SDN (ms) | Diferencia (IC 95 %) | p (t pareada) |
|---|---|---|---|---|
| 0 | 13,06 | 13,16 | −0,10 (−0,78 a 0,58) | 0,768 |
| 20 | 10,06 | 10,06 | 0,00 (−0,82 a 0,81) | 0,999 |
| 40 | 10,37 | 10,42 | −0,05 (−0,69 a 0,59) | 0,876 |
| 60 | 10,53 | 10,41 | 0,12 (−0,60 a 0,83) | 0,741 |
| 200 | 22,53 | 21,98 | 0,55 (−1,14 a 2,24) | 0,509 |

- La latencia y la variación del retardo **no difirieron** entre las arquitecturas en ninguna carga. La diferencia de
  2,85 ms de la primera serie (40 Mbit/s) no se confirmó.
- La pérdida del flujo de video fue menor de 0,4 % hasta 60 Mbit/s; con 40 y 60 Mbit/s fue algo mayor con SDN
  (0,14 % frente a 0,02 % y 0,36 % frente a 0,20 %), diferencias de décimas de punto porcentual.
- Con 200 Mbit/s las dos redes se saturan por igual (≈ 60 % de ecos perdidos) e iperf3 casi nunca termina (4 y 2 de 30),
  por eso en ese nivel no se informan la variación del retardo ni la pérdida del flujo.

Tablas completas, con los intervalos de cada media y las pruebas de Wilcoxon: [`datos/resumen_replica.md`](datos/resumen_replica.md).

## Archivos

| Archivo | Contenido |
|---|---|
| `ejecutar_replica_unicast.py` | Ejecuta las 300 mediciones (unas 3 horas). Se puede interrumpir y reanudar |
| `analizar_replica.py` | Recalcula las tablas y la figura desde los datos crudos |
| `datos/corridas.jsonl` | Una línea por medición: arquitectura, carga, orden dentro de la repetición, salida resumida de ping, métricas de iperf3, errores y carga del equipo |
| `datos/ryu/repNN.log` | Registro del controlador en cada repetición |
| `datos/resumen_replica.md`, `.csv` | Resultado del análisis |

## Cómo repetirlo

Con el entorno preparado como indica el [manual](../../MANUAL.md) (paso 4.3, `preparar_entorno.py`):

```bash
# solo el análisis, desde los datos publicados (no requiere GNS3)
python3 gns3/replica_unicast/analizar_replica.py            # TESIS=1 para la figura del documento

# la réplica completa, en otra carpeta para no sobrescribir los datos publicados
RU_DATOS=/tmp/replica python3 gns3/replica_unicast/ejecutar_replica_unicast.py --reps 30 --cargas 0,20,40,60,200

# prueba rápida (1 repetición, unos 6 minutos)
RU_DATOS=/tmp/humo python3 gns3/replica_unicast/ejecutar_replica_unicast.py --reps 1
```

Si Ryu no está en `~/ryu-controller/venv/bin/ryu-manager`, indique la ruta con la variable `RYU_MANAGER`. Al terminar,
el script deja los conmutadores en modo tradicional.
