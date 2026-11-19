# Experimento multicast — guía de reproducción

Compara cómo se comporta el tráfico **IP multicast** en la topología emulada del campus UNIPAZ (13 conmutadores Open vSwitch)
bajo tres arquitecturas, con uno o varios receptores:

| Arquitectura | Qué es | Cómo se configura |
|---|---|---|
| **Tradicional** | Conmutadores autónomos (`standalone`, acción `NORMAL`), sin IGMP snooping: el multicast se inunda | `modo_autonomo(snooping=False)` |
| **Snooping nativo de OVS** (control) | Conmutadores autónomos con el IGMP snooping propio de Open vSwitch, configuración por defecto y **sin consultor IGMP** (OVS no trae uno) | `modo_autonomo(snooping=True)` |
| **SDN** | Conmutadores en modo `secure` gobernados por Ryu con la aplicación `ryu-apps/gestion_multicast_igmp.py` (consultor IGMP + snooping + poda del multicast sin receptores) | `modo_sdn(...)` |

Además se mide el **unicast** (un flujo por receptor, equivalente a lo que hace hoy un servicio como Meet) como referencia
de lo que cuesta no usar multicast.

## Topología y equipos

Es la topología de los trece bloques de la Fase 3 (`gns3/fase3/`) con **seis hosts nuevos** (imagen `unipaz/ipterm-mc:1`,
que agrega iperf2 a `gns3/ipterm`):

| Host | Conmutador | Posición en la jerarquía física | IP |
|---|---|---|---|
| `Emisor-MC` | Core-Switch-48p | núcleo | 172.30.0.100 |
| `Rx-LAB2` | Switch-LAB2 | el más profundo: núcleo → enrutador de fibra → LBA → LAB2 | 172.30.0.101 |
| `Rx-Biblioteca` | Switch-Biblioteca | enlace directo al enrutador de fibra | 172.30.0.103 |
| `Rx-Entrada` | Switch-Entrada | encadenado: Portería → Entrada | 172.30.0.105 |
| `Rx-Aprisco` | Switch-Aprisco | encadenado: Salones antiguos → Aprisco | 172.30.0.102 |
| `Rx-Aulas` | Switch-EdificioAulas | enlace directo al enrutador de fibra | 172.30.0.104 |

Los equipos ya existentes (`Servidor-Nucleo`, `PC-Aprisco`, `PC-LAB2`, `Camara-LAB2`, `NVR-LBA`) **nunca se suscriben**:
son observadores y solo reciben tráfico si la red lo inunda. Con k receptores suscritos (los k primeros de la lista
`RECEPTORES`), los `5 − k` receptores restantes también actúan como observadores.

## Procedimiento de cada medición

1. Se limpian los contadores y se leen (bytes recibidos por cada host, bytes transmitidos por todos los puertos de los
   13 conmutadores, bytes del emisor).
2. Los k receptores arrancan `iperf -s -u -B 239.10.10.10 -y C -i 1` (se unen al grupo y envían su reporte IGMP).
3. Tras 4 s, el emisor envía `iperf -c 239.10.10.10 -u -b 5M -t 15 -T 8` (5 Mbit/s durante 15 s).
   En la variante **unicast**, el emisor envía en paralelo un flujo UDP de 5 Mbit/s a cada receptor.
4. Tras 3 s más se vuelven a leer los contadores y se recoge el resumen de iperf2 de cada receptor (bytes, jitter, pérdida).

**Diseño:** 10 repeticiones × 12 mediciones (tradicional: multicast y unicast × k = 1, 3, 5; snooping: × k; SDN: × k). En
cada repetición el orden de las arquitecturas y de las mediciones es **aleatorio** (semilla = número de repetición), de
modo que ninguna arquitectura se mide siempre antes que otra. En SDN, Ryu se reinicia en cada medición.

## Reproducir

Requisitos: GNS3 2.2.61 con servidor local, Docker (imágenes `gns3/ipterm`, `gns3/openvswitch`), Ryu 4.34 en
`~/ryu-controller/venv` (Python 3.8; otra ruta con la variable `RYU_MANAGER`), la red `virbr0` de libvirt en
192.168.122.1 (por ella los conmutadores alcanzan al controlador) y las credenciales del servidor en
`~/.config/GNS3/2.2/gns3_server.conf`. Si el proyecto no está en `gns3/Fase1-Nucleo-Administrativa/`,
`preparar_entorno.py` lo importa desde `paquete/Fase1-Nucleo-Administrativa.gns3project` con su mismo identificador.

```bash
gns3server --local &                                  # servidor de GNS3 en modo local
python3 gns3/multicast/preparar_entorno.py            # imagen con iperf2, proyecto, hosts, IP de gestión
python3 gns3/multicast/ejecutar_experimento.py        # 120 mediciones (~70 min); reanuda si se interrumpe
python3 gns3/multicast/analizar_multicast.py          # resumen, pruebas por pares y gráficas
```

Prueba rápida (≈ 3 min, no escribe en `datos/`): `MC_DATOS=/tmp/humo python3 gns3/multicast/ejecutar_experimento.py --reps 1 --duracion 6 --ks 1,3`.

Para ver la aplicación en funcionamiento (tras una medición SDN), en cualquier conmutador:
`ovs-ofctl -O OpenFlow13 dump-flows br0` — con miembros, una regla `nw_dst=239.10.10.10 actions=output:<puertos>`; sin
miembros, solo la regla de descarte de `224.0.0.0/4`.

## Contenido de esta carpeta

| Archivo | Qué es |
|---|---|
| `docker/Dockerfile` | Imagen de los hosts (gns3/ipterm + iperf2) |
| `lib_gns3.py`, `lib_experimento.py` | API de GNS3, cambio de arquitectura y medición |
| `agregar_hosts_multicast.py`, `preparar_entorno.py` | Montaje del entorno |
| `ejecutar_experimento.py`, `analizar_multicast.py` | Experimento y análisis |
| `datos/corridas.jsonl` | **Datos crudos**: una línea JSON por medición (contadores de todos los hosts y puertos, resumen de cada receptor, reglas de flujo de la primera repetición) |
| `datos/ryu/` | Registro de Ryu de cada medición SDN (uniones, consultas, vencimientos) |
| `datos/resumen_multicast.md/.csv` | Resultados resumidos y pruebas estadísticas |
| `../../ryu-apps/gestion_multicast_igmp.py` | Aplicación de Ryu |

## Límites que conviene tener presentes

- **El enrutador de fibra es un conmutador Ethernet de GNS3** (no un OVS ni un router): inunda el multicast y los reportes
  IGMP por todos sus puertos y no lo gobierna el controlador. Por eso los 6 enlaces que cuelgan de él llevan el flujo en
  todas las arquitecturas, y la poda se observa dentro de cada bloque. En el campus real ese equipo es un router MikroTik.
- **«Carga total» = bytes transmitidos por los puertos de los 13 conmutadores OVS.** No incluye lo que transmite el
  enrutador de fibra emulado (no tiene contadores), que inunda el multicast hacia los 6 bloques en todas las arquitecturas;
  la cifra subestima la carga real de la red de forma igual en las tres, y la comparación entre ellas es válida.
- **Los valores absolutos dependen del computador** que ejecuta la emulación; sirven para comparar arquitecturas entre sí,
  no como cifras de la red real. Las diferencias en bytes (inundación frente a poda) dependen de la topología y no del
  equipo; el jitter y la pérdida sí dependen de la carga de la máquina.
- **El control «snooping nativo» no es el mejor caso de una red tradicional:** sin consultor IGMP, OVS no construye el
  árbol entre conmutadores. Una red tradicional con consultor y snooping en todos sus equipos podría podar mejor; este
  experimento no lo evalúa.
- La aplicación de Ryu no implementa la salida rápida (leave): una baja se detecta por vencimiento de la membresía.
- Se mide un solo grupo y un solo emisor, con UDP a 5 Mbit/s, hasta 5 receptores: es una prueba de principio, no una prueba de escala.

## Resultados obtenidos (17/11/2026; 120 mediciones, 10 repeticiones, sin fallos)

Resumen completo con IC 95 % y pruebas por pares en `datos/resumen_multicast.md`; gráficas en `docs/graficas/mc_*.png`.

| Métrica (media de 10 repeticiones) | k | Tradicional | Snooping OVS | **SDN** | Unicast |
|---|---|---|---|---|---|
| Recibido por equipos que no lo pidieron (MB) | 1 | 91,06 | 70,82 | **0,01** | 0,00 |
| | 3 | 70,82 | 50,58 | **0,01** | 0,74 |
| | 5 | 50,59 | 20,23 | **0,00** | 4,35 |
| Carga total transmitida por los conmutadores (MB) | 1 | 172,1 | 151,8 | **30,6** | 30,4 |
| | 3 | 172,1 | 141,7 | **60,9** | 82,5 |
| | 5 | 172,1 | 131,6 | **91,2** | 140,3 |
| Transmitido por el emisor (MB) | 3 | 10,1 | 10,1 | **10,1** | 30,4 |
| | 5 | 10,1 | 10,1 | **10,1** | 50,6 |
| Jitter en receptores suscritos (ms) | 1 | 3,30 | 3,05 | **1,71** | 0,19 |
| | 5 | 3,34 | 2,88 | **1,90** | 1,63 |

- Frente al tradicional, SDN eliminó el 100 % del tráfico que llegaba a equipos que no lo pidieron y redujo la carga total
  en los conmutadores un 82,2 % (k = 1), 64,6 % (k = 3) y 47,0 % (k = 5); todas las diferencias por pares con p < 0,001
  (t pareada) y p = 0,002 (Wilcoxon, el mínimo posible con n = 10).
- Frente al unicast, el multicast gestionado por SDN redujo lo que transmite el emisor un 66,7 % (k = 3) y 80,0 % (k = 5),
  y la carga total un 26,2 % (k = 3) y 35,0 % (k = 5). Con un solo receptor ambos son equivalentes, como se espera.
- **Pérdida: 0 % en todas las mediciones** (5 Mbit/s no satura el camino emulado). Ningún receptor suscrito dejó de recibir
  el flujo completo (9,84 MB por medición) en ninguna arquitectura.
- El jitter fue menor con SDN que con el tradicional (diferencia de 1,4 a 1,6 ms, p < 0,001). Debe leerse con cuidado:
  la explicación más probable es que la emulación procesa mucho menos tráfico cuando no inunda (la carga del computador
  afecta el jitter), no una propiedad del protocolo. El unicast muestra el mismo patrón: menos tráfico, menos jitter.
- En el unicast hubo inundación ocasional de unicast desconocido mientras los conmutadores aprendían direcciones (de ahí
  los 0,74 y 4,35 MB y su alta variabilidad).
- Capturas (`datos/capturas/`): con el tradicional, el observador PC-LAB2, en el mismo conmutador que el receptor, recibió
  los 4462 paquetes del grupo; con SDN, 0.
