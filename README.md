# Emulación SDN del campus UNIPAZ — material técnico del proyecto de grado

Material complementario del proyecto de grado **«Análisis de servicios IP Multicast utilizadas en redes corporativas del
campus universitario de la Universidad de la Paz (UNIPAZ) Barrancabermeja con tecnologías SDN»**.

Este repositorio reúne lo necesario para **abrir la topología emulada, repetir los experimentos y verificar los
resultados del documento a partir de los datos crudos**. El documento de grado, el artículo y los apéndices se entregan
por la plataforma institucional (SII).

**Para replicar el trabajo paso a paso (instalación, configuración, ejecución y solución de problemas), siga el
[manual de replicación](MANUAL.md).**

## Cómo está organizado

La topología del campus se construyó en GNS3 en tres fases y sobre ella se hicieron dos experimentos:

| Carpeta o archivo | Contenido | Documento |
|---|---|---|
| [`gns3/fase1/`](gns3/fase1/) | Fase 1: núcleo de la red (salidas a internet, conmutador de núcleo Open vSwitch y enrutador de fibra) conectado al controlador Ryu | 4.3 |
| [`gns3/fase2/`](gns3/fase2/) | Fase 2: cadena de prueba (Salones antiguos y Aprisco) y procedimiento del **experimento 1**, calidad de servicio con tráfico unicast | 4.4, 4.5 |
| [`gns3/mediciones/`](gns3/mediciones/) | Datos del experimento 1: salidas de ping e iperf3 de las diez repeticiones por escenario, resumen estadístico y captura | 4.5 (primera serie) |
| [`gns3/replica_unicast/`](gns3/replica_unicast/) | **Réplica del experimento 1** pedida por los calificadores: 30 repeticiones, cargas de 0 a 200 Mbit/s y orden aleatorio (300 mediciones), con scripts, datos crudos y registros del controlador | 4.4, 4.5 (Tablas 7 y 8, Figura 6) |
| [`gns3/fase3/`](gns3/fase3/) | Fase 3: construcción y verificación de los trece bloques del campus | 4.3 |
| [`gns3/topologia.md`](gns3/topologia.md) | Todos los nodos y enlaces de la topología, generados desde el proyecto de GNS3 | 4.3 (Figura 4) |
| [`gns3/multicast/`](gns3/multicast/) | **Experimento 2**, tráfico IP Multicast: guía detallada, scripts de preparación, ejecución, análisis y capturas, y Dockerfile de los equipos de prueba | 3.9, 4.6 |
| `gns3/multicast/paquete/Fase1-Nucleo-Administrativa.gns3project` | Proyecto portable de GNS3 con la topología completa (las tres fases y los equipos de los dos experimentos) | 4.3 |
| `gns3/multicast/datos/` | Datos crudos de las 120 mediciones (`corridas.jsonl`), registros del controlador y capturas de paquetes (`.pcap`) | 4.6 (Tablas 9 y 10), Apéndice D (D.5) |
| [`ryu-apps/gestion_multicast_igmp.py`](ryu-apps/gestion_multicast_igmp.py) | Aplicación de gestión multicast para Ryu: consultor IGMP, aprendizaje de miembros y poda de grupos | 3.9 |
| [`scripts/`](scripts/) | Generación de las figuras del documento (arquitectura, topología, calidad de servicio y proyección) | Capítulo 4 |
| [`docs/graficas/tesis/`](docs/graficas/tesis/) | Figuras tal como aparecen en el documento | Capítulo 4 |

## Verificación rápida

Sin instalar el entorno de emulación, solo con Python, SciPy y Matplotlib:

```bash
python3 gns3/multicast/analizar_multicast.py      # recalcula las Tablas 9 y 10 desde los datos crudos
python3 gns3/replica_unicast/analizar_replica.py  # recalcula las Tablas 7 y 8 (experimento 1)
python3 scripts/graficas_capitulo4.py             # recalcula las cifras de la primera serie del experimento 1
```

El resultado coincide con el publicado (`git diff` no muestra cambios en `gns3/multicast/datos/resumen_multicast.md` ni en
`gns3/replica_unicast/datos/resumen_replica.md`).
Para repetir los experimentos completos, ver el [manual](MANUAL.md).

## Uso de inteligencia artificial

En el desarrollo de este proyecto se usó **Claude** (Anthropic), un asistente de inteligencia artificial, como
herramienta de apoyo y guía: en la programación de los scripts de emulación, medición y análisis y de la aplicación de
gestión multicast para Ryu, en el procesamiento estadístico y la elaboración de gráficas, y en la revisión de la
redacción, las citas y el formato del documento. Las decisiones del proyecto, el levantamiento de información en campo y
la interpretación de los resultados corresponden al autor, quien revisó el contenido elaborado con la herramienta y
responde por él.

## Autor

**Yadier Andrey Socha Suárez** — ysocha1@udi.edu.co
Estudiante de Ingeniería de Sistemas, Universidad de Investigación y Desarrollo (UDI), sede Barrancabermeja.

Director: Willhelmys Duran Botia. Codirectora: Lizbeth Parada Diaz.
