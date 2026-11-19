# Emulación SDN del campus UNIPAZ — material técnico del proyecto de grado

Material complementario del proyecto de grado **«Análisis de servicios IP Multicast utilizadas en redes corporativas del
campus universitario de la Universidad de la Paz (UNIPAZ) Barrancabermeja con tecnologías SDN»**, de Yadier Andrey Socha
Suárez (Ingeniería de Sistemas, Universidad de Investigación y Desarrollo — UDI, sede Barrancabermeja).

Este repositorio reúne lo necesario para **abrir la topología emulada, repetir los experimentos y verificar los
resultados del documento a partir de los datos crudos**. El documento de grado, el artículo y los apéndices se entregan
por la plataforma institucional (SII); aquí solo está el material técnico.

## Qué hay y con qué apartado del documento se relaciona

| Carpeta o archivo | Contenido | Documento |
|---|---|---|
| `gns3/multicast/paquete/Fase1-Nucleo-Administrativa.gns3project` | Proyecto portable de GNS3: topología de los trece bloques con los equipos de prueba | 4.3, 3.9 |
| `ryu-apps/gestion_multicast_igmp.py` | Aplicación de gestión multicast para el controlador Ryu (consultor IGMP, aprendizaje de miembros y poda) | 3.9 |
| `gns3/multicast/` | Experimento con tráfico IP Multicast: guía detallada (`README.md`), scripts de preparación, ejecución, análisis y capturas, y Dockerfile de los equipos de prueba | 3.9, 4.6 |
| `gns3/multicast/datos/corridas.jsonl` | Datos crudos de las 120 mediciones: contadores de todos los equipos y puertos, resumen de cada receptor y reglas de flujo | 4.6 (Tablas 9 y 10) |
| `gns3/multicast/datos/ryu/` | Registro del controlador en cada medición SDN | 4.6 |
| `gns3/multicast/datos/capturas/` | Capturas de paquetes (`.pcap`, se abren con Wireshark), su resumen y el registro de Ryu de la demostración | 4.6, Apéndice D (D.5) |
| `gns3/mediciones/` y `gns3/fase-mediciones-qos.md` | Experimento de calidad de servicio con tráfico unicast: salidas de ping e iperf3 de las diez repeticiones por escenario, resumen estadístico, captura y procedimiento | 4.4, 4.5 |
| `gns3/fase3/` y `gns3/plan-nodos-enlaces.md` | Construcción y verificación de la topología de los trece bloques | 4.3 |
| `scripts/` | Generación de las figuras del documento (arquitectura, topología, calidad de servicio y proyección) | 4.2 a 4.7 |
| `docs/graficas/tesis/` | Figuras tal como aparecen en el documento | Capítulo 4 |

## Verificar los resultados sin repetir el experimento

Con Python 3, SciPy y Matplotlib, desde la raíz del repositorio:

```bash
python3 gns3/multicast/analizar_multicast.py
```

Recalcula, a partir de `gns3/multicast/datos/corridas.jsonl`, las medias, los intervalos de confianza y las pruebas por
pares (t para muestras relacionadas y Wilcoxon) en `gns3/multicast/datos/resumen_multicast.md`, y regenera las gráficas.
El resultado coincide con las Tablas 9 y 10 del documento.

Las cifras del experimento unicast (Tablas 7 y 8 y Figura 6) se recalculan con `python3 scripts/graficas_capitulo4.py`
a partir de `gns3/mediciones/`.

## Repetir el experimento multicast

Requisitos: Linux con GNS3 2.2.61 (servidor local), Docker con las imágenes `gns3/openvswitch` y `gns3/ipterm`, Ryu 4.34
en un entorno de Python 3.8 (por defecto en `~/ryu-controller/venv`; otra ruta con la variable `RYU_MANAGER`) y la red
`virbr0` de libvirt en 192.168.122.1, por la que los conmutadores alcanzan al controlador.

```bash
gns3server --local &
python3 gns3/multicast/preparar_entorno.py      # construye la imagen con iperf2 e importa el proyecto portable
python3 gns3/multicast/ejecutar_experimento.py  # 120 mediciones, unos 70 minutos; se puede interrumpir y reanudar
python3 gns3/multicast/analizar_multicast.py
```

El procedimiento completo, el diseño del experimento y sus límites están en `gns3/multicast/README.md`. El proyecto
también se puede abrir en la interfaz de GNS3 con *File > Import portable project*, después de construir la imagen de
los equipos de prueba con `docker build -t unipaz/ipterm-mc:1 gns3/multicast/docker`.

Los valores absolutos (latencia, variación del retardo) dependen del equipo en que se ejecute la emulación; las
diferencias en bytes dependen de la topología.

## Qué no está en el repositorio

Por confidencialidad, no se incluyen el inventario detallado de la red de UNIPAZ, el informe de tráfico del firewall
institucional, las respuestas de los informantes clave ni datos personales. Las cifras agregadas que se usan en el
documento provienen de esas fuentes y se citan allí.

## Uso de inteligencia artificial

En el desarrollo de este proyecto se usó **Claude** (Anthropic), un asistente de inteligencia artificial, como
herramienta de apoyo y guía: en la programación de los scripts de emulación, medición y análisis y de la aplicación de
gestión multicast para Ryu, en el procesamiento estadístico y la elaboración de gráficas, y en la revisión de la
redacción, las citas y el formato del documento. Las decisiones del proyecto, el levantamiento de información en campo y
la interpretación de los resultados corresponden al autor, quien revisó el contenido elaborado con la herramienta y
responde por él.

## Autor

Yadier Andrey Socha Suárez — Ingeniería de Sistemas, UDI Barrancabermeja.
Director: Willhelmys Duran Botia. Codirectora: Lizbeth Parada Diaz.
