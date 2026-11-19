# Manual de replicación

Paso a paso para instalar el entorno, abrir la topología y repetir los experimentos del proyecto de grado, con las
soluciones a los problemas que se presentaron durante el trabajo. Si solo quiere comprobar las cifras del documento sin
instalar el entorno de emulación, vaya directo al [apartado 4.1](#41-verificar-los-resultados-desde-los-datos-crudos).

**Contenido**

1. [Qué se va a reproducir](#1-qué-se-va-a-reproducir)
2. [Requisitos](#2-requisitos)
3. [Instalación](#3-instalación)
4. [Ejecución](#4-ejecución)
5. [Cómo comprobar que todo funciona](#5-cómo-comprobar-que-todo-funciona)
6. [Problemas frecuentes y solución](#6-problemas-frecuentes-y-solución)

---

## 1. Qué se va a reproducir

La topología del campus se construyó en GNS3 en tres etapas, y sobre ella se hicieron dos experimentos (el primero,
con una réplica):

| Etapa | Qué se hizo | Carpeta | Documento |
|---|---|---|---|
| Fase 1 | Núcleo: salida a internet, conmutador de núcleo (Open vSwitch) y enrutador de fibra, conectados al controlador Ryu | [`gns3/fase1/`](gns3/fase1/) | 4.3 |
| Fase 2 | Cadena de prueba (Salones antiguos y Aprisco) y **experimento 1**: calidad de servicio con tráfico unicast | [`gns3/fase2/`](gns3/fase2/), datos en [`gns3/mediciones/`](gns3/mediciones/) | 4.4, 4.5 |
| Fase 3 | Los diez bloques restantes, hasta completar los trece | [`gns3/fase3/`](gns3/fase3/) | 4.3 |
| Réplica del experimento 1 | Calidad de servicio con tráfico unicast sobre los trece bloques: 30 repeticiones, cargas de 0 a 200 Mbit/s y **orden aleatorio** | [`gns3/replica_unicast/`](gns3/replica_unicast/) | 4.5.1 |
| Experimento 2 | Seis equipos de prueba más y **experimento con tráfico IP Multicast** | [`gns3/multicast/`](gns3/multicast/) | 3.9, 4.6 |

Estas fases son etapas de construcción de la topología en GNS3; no corresponden a las cinco fases del plan de trabajo
del documento (apartado 1.4.4).

**Para replicar no hace falta repetir las fases 1 a 3:** el proyecto portable
[`gns3/multicast/paquete/Fase1-Nucleo-Administrativa.gns3project`](gns3/multicast/paquete/) ya contiene la topología
completa, con los trece bloques y todos los equipos de prueba. Las carpetas de cada fase documentan cómo se construyó.

## 2. Requisitos

| Elemento | Usado en el proyecto | Mínimo recomendado |
|---|---|---|
| Sistema operativo | Ubuntu 26.04 LTS, instalado de forma nativa | Ubuntu 22.04 o posterior (GNS3 con contenedores Docker funciona mejor fuera de una máquina virtual) |
| Procesador y memoria | 8 núcleos, 14 GB de RAM | 4 núcleos, 8 GB de RAM (la topología tiene 30 nodos) |
| Disco | — | 5 GB libres |
| GNS3 | 2.2.61 (servidor y cliente) | La misma versión: el proyecto portable es de la 2.2 |
| Docker | Docker CE 29 | Cualquier versión reciente |
| Ryu | 4.34 sobre Python 3.8 | La misma: Ryu no funciona con Python 3.10 o posterior |
| Python del sistema | 3.14, con SciPy y Matplotlib | Python 3.9 o posterior, con SciPy y Matplotlib |

## 3. Instalación

Todos los comandos se ejecutan en una terminal de Ubuntu como usuario normal (con `sudo` cuando se indica).

### 3.1 Paquetes base

```bash
sudo apt update
sudo apt install -y git curl software-properties-common python3-scipy python3-matplotlib
```

### 3.2 GNS3

```bash
sudo add-apt-repository -y ppa:gns3/ppa
sudo apt update
sudo apt install -y gns3-gui gns3-server
```

Durante la instalación, responda **Sí** cuando pregunte si los usuarios sin privilegios pueden usar `ubridge` y capturar
paquetes con Wireshark.

### 3.3 Docker

```bash
sudo apt install -y docker.io
```

(En el proyecto se usó Docker CE desde el repositorio oficial de Docker; cualquiera de los dos sirve.)

### 3.4 Red de libvirt (`virbr0`)

El nodo NAT de GNS3 y la conexión de los conmutadores con el controlador usan la red `virbr0` de libvirt, en
192.168.122.1:

```bash
sudo apt install -y libvirt-daemon-system qemu-kvm
sudo virsh net-autostart default
sudo virsh net-start default
ip -4 addr show virbr0          # debe mostrar 192.168.122.1/24
```

### 3.5 Permisos del usuario

```bash
sudo usermod -aG ubridge,libvirt,kvm,wireshark,docker $USER
```

**Cierre la sesión y vuelva a entrar** (o reinicie) para que los grupos se apliquen. Compruébelo con `id -nG`.

### 3.6 Imágenes de Docker

```bash
docker pull gns3/openvswitch:latest
docker pull gns3/ipterm:latest
```

La imagen de los equipos del experimento multicast (`unipaz/ipterm-mc:1`, que agrega Iperf2 a `gns3/ipterm`) la
construye `preparar_entorno.py` automáticamente; si prefiere hacerlo a mano:
`docker build -t unipaz/ipterm-mc:1 gns3/multicast/docker`.

### 3.7 Ryu 4.34 con Python 3.8

Ryu dejó de mantenerse y sus dependencias no funcionan con versiones recientes de Python, así que se instala en un
entorno aparte con Python 3.8:

```bash
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.8 python3.8-venv python3.8-dev
mkdir -p ~/ryu-controller && cd ~/ryu-controller
python3.8 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install setuptools==67.6.1 eventlet==0.30.2
pip install ryu==4.34
ryu-manager --version          # debe responder: ryu-manager 4.34
deactivate
```

Las versiones de `setuptools` y `eventlet` van fijas a propósito (ver la [sección 6](#6-problemas-frecuentes-y-solución)).
Si instala Ryu en otra ruta, indíquela a los scripts con la variable `RYU_MANAGER`, por ejemplo
`export RYU_MANAGER=/otra/ruta/venv/bin/ryu-manager`.

### 3.8 Este repositorio

```bash
git clone https://github.com/ysocha1-ui/sdn-unipaz-emulacion.git
cd sdn-unipaz-emulacion
```

### 3.9 Configuración del servidor de GNS3

Los scripts usan la API local de GNS3 (`localhost:3080`) con el usuario y la clave que GNS3 guarda en
`~/.config/GNS3/2.2/gns3_server.conf`. Ese archivo se crea al abrir GNS3 por primera vez:

1. Abra GNS3 (`gns3`), acepte el asistente con la opción **Run appliances on my local computer** y ciérrelo.
2. Compruebe que el archivo tiene la sección `[Server]` con `auth`, `user` y `password`:

   ```bash
   grep -E '^(auth|user|password)' ~/.config/GNS3/2.2/gns3_server.conf
   ```

   Si no aparecen, agréguelas bajo `[Server]` (por ejemplo `auth = True`, `user = admin`, `password = una-clave`).

## 4. Ejecución

Todos los comandos se ejecutan desde la raíz del repositorio.

### 4.1 Verificar los resultados desde los datos crudos

No requiere GNS3, Docker ni Ryu; solo Python con SciPy y Matplotlib.

```bash
python3 gns3/multicast/analizar_multicast.py      # experimento multicast: Tablas 10 y 11, Figura 8
python3 gns3/replica_unicast/analizar_replica.py  # réplica unicast: Tabla 9, Figura 7
python3 scripts/graficas_capitulo4.py             # primera serie unicast: Tablas 7 y 8, Figura 6
```

Los dos primeros reescriben `gns3/multicast/datos/resumen_multicast.md` y
`gns3/replica_unicast/datos/resumen_replica.md`; con `git diff` puede comprobar que el resultado es idéntico al
publicado.

### 4.2 Abrir la topología en GNS3 (para verla)

1. Construya la imagen de los equipos de prueba: `docker build -t unipaz/ipterm-mc:1 gns3/multicast/docker`.
2. En GNS3: **File > Import portable project** y elija
   `gns3/multicast/paquete/Fase1-Nucleo-Administrativa.gns3project`.
3. **Start all nodes** (el botón verde). Los 30 nodos tardan uno o dos minutos en quedar en verde.

### 4.3 Repetir el experimento multicast completo

```bash
gns3server --local &                            # 1. servidor de GNS3 (cierre antes la interfaz gráfica)
python3 gns3/multicast/preparar_entorno.py      # 2. imagen, proyecto, nodos encendidos, IP de gestión
python3 gns3/multicast/ejecutar_experimento.py  # 3. 120 mediciones, unos 70 minutos
python3 gns3/multicast/analizar_multicast.py    # 4. resumen, pruebas y gráficas
```

- El paso 2 importa el proyecto portable con su identificador original, del que dependen los nombres de los contenedores.
  Si ya lo importó por la interfaz gráfica con otro identificador, bórrelo de GNS3 antes.
- El paso 3 se puede interrumpir con `Ctrl+C` y reanudar con el mismo comando: continúa donde quedó.
- Para escribir en otra carpeta y no sobrescribir los datos publicados: `MC_DATOS=/tmp/prueba python3 ...`.
- Prueba rápida, de unos 3 minutos:
  `MC_DATOS=/tmp/humo python3 gns3/multicast/ejecutar_experimento.py --reps 1 --duracion 6 --ks 1,3`.
- Para repetir las capturas de paquetes del Apéndice D: `python3 gns3/multicast/demostracion_capturas.py`.

El diseño del experimento y sus límites se detallan en [`gns3/multicast/README.md`](gns3/multicast/README.md).

### 4.4 Repetir el experimento unicast

**Réplica (apartado 4.5.1), automatizada.** Con el entorno preparado (pasos 1 y 2 del apartado 4.3):

```bash
RU_DATOS=/tmp/replica python3 gns3/replica_unicast/ejecutar_replica_unicast.py --reps 30 --cargas 0,20,40,60,200
```

Tarda unas 3 horas (300 mediciones); se puede interrumpir con `Ctrl+C` y reanudar con el mismo comando. Para una prueba
rápida, `--reps 1` (unos 6 minutos). Detalles en [`gns3/replica_unicast/README.md`](gns3/replica_unicast/README.md).

**Primera serie (apartados 4.4 y 4.5).** Se hizo a mano, desde las consolas de los equipos en GNS3; el procedimiento exacto, con los comandos usados, está en
[`gns3/fase2/README.md`](gns3/fase2/README.md). Con el proyecto portable ya abierto, empiece en su paso 2.

### 4.5 Regenerar las figuras del documento

```bash
TESIS=1 python3 scripts/graficas_capitulo4.py      # Figuras 1 y 6
python3 scripts/diagramas_arquitectura.py          # Figuras 2 y 3
python3 scripts/diagrama_topologia_gns3.py         # Figura 4
TESIS=1 python3 gns3/replica_unicast/analizar_replica.py   # Figura 7
TESIS=1 python3 gns3/multicast/analizar_multicast.py   # Figura 8
TESIS=1 python3 scripts/proyeccion_campus.py       # Figura 9
```

Las figuras quedan en `docs/graficas/tesis/`.

## 5. Cómo comprobar que todo funciona

| Qué comprobar | Comando | Resultado esperado |
|---|---|---|
| Red de libvirt | `ip -4 addr show virbr0` | `inet 192.168.122.1/24` |
| Docker sin `sudo` | `docker ps` | Una lista (vacía o no), sin error de permisos |
| Servidor de GNS3 | `curl -s localhost:3080/v2/version` | Una respuesta con `"version": "2.2.61"` (o un error de autenticación, que también indica que está corriendo) |
| Ryu | `~/ryu-controller/venv/bin/ryu-manager --version` | `ryu-manager 4.34` |
| Nodos encendidos | `docker ps --format '{{.Names}}' \| grep -c GNS3` | 24 contenedores (los otros 6 nodos son conmutadores Ethernet y salidas NAT de GNS3) |
| Conmutador conectado a Ryu | `docker exec GNS3.Core-Switch-48p.a895d4f8-2166-405c-9885-d8d8d387d508 ovs-vsctl show` | `is_connected: true` durante una medición SDN |
| Reglas del controlador | mismo contenedor, `ovs-ofctl -O OpenFlow13 dump-flows br0` | Con receptores, una regla `nw_dst=239.10.10.10 actions=output:…` |
| Registro de Ryu | `gns3/multicast/datos/ryu/*.log` | Líneas `puerto de subida` (una por conmutador) y `union … grupo=239.10.10.10` |

## 6. Problemas frecuentes y solución

### Instalación

| Síntoma | Causa | Solución |
|---|---|---|
| `AttributeError: get_script_args` al instalar o ejecutar Ryu | `setuptools` 68 o posterior eliminó esa función | `pip install setuptools==67.6.1` dentro del entorno de Ryu |
| `ImportError: cannot import name 'ALREADY_HANDLED'` | `eventlet` 0.31 o posterior eliminó esa constante | `pip install eventlet==0.30.2` dentro del entorno de Ryu |
| `python3.8: orden no encontrada` | El PPA deadsnakes no está agregado o no tiene paquetes para su versión de Ubuntu | Repita la sección 3.7; si su versión no tiene Python 3.8, instálelo con `pyenv install 3.8` o `uv python install 3.8` |
| `permission denied ... docker.sock` | El usuario no está en el grupo `docker` | Sección 3.5 y volver a iniciar sesión |
| GNS3 pide permisos para `ubridge` o los enlaces no pasan tráfico | `ubridge` sin permisos para el usuario | `sudo dpkg-reconfigure ubridge` (responder Sí) y estar en el grupo `ubridge` |
| No existe `virbr0` | La red `default` de libvirt está apagada | `sudo virsh net-start default` y `sudo virsh net-autostart default` |
| `KeyError: 'Server'` o `KeyError: 'user'` al correr un script | No existe `~/.config/GNS3/2.2/gns3_server.conf` o no tiene usuario y clave | Sección 3.9 |

### Topología y GNS3

| Síntoma | Causa | Solución |
|---|---|---|
| `HTTP Error 403` al cargar o importar el proyecto | El servidor no se inició en modo local | Cerrar la interfaz gráfica y arrancar `gns3server --local` |
| `HTTP Error 409` al exportar el proyecto | Hay nodos encendidos | Detener todos los nodos antes de exportar |
| Al importar, los nodos Docker quedan en rojo | Faltan las imágenes de Docker | Sección 3.6 y, para los equipos multicast, `docker build -t unipaz/ipterm-mc:1 gns3/multicast/docker` |
| Los scripts dicen que no existe el contenedor `GNS3.<nodo>.<id>` | El proyecto se importó con otro identificador | Borrar el proyecto de GNS3 y dejar que `preparar_entorno.py` lo importe |
| `pkill -f gns3server` cierra también la terminal | El patrón coincide con la propia orden | `pkill -x gns3server` o detenerlo por su número de proceso |
| En la consola de Open vSwitch, `sudo` o `dhclient` no existen | El contenedor usa Alpine Linux y la sesión ya es de root | Usar los comandos sin `sudo` y `udhcpc -i br0` en lugar de `dhclient` |
| `udhcpc` no obtiene dirección | El nodo NAT o `virbr0` no están activos | Comprobar `virbr0` (sección 5) y que el nodo NAT esté encendido |
| `ovs-ofctl: version negotiation failed` | El puente solo admite OpenFlow 1.3 | Agregar `-O OpenFlow13` a cada orden `ovs-ofctl` |

### Controlador y experimento

| Síntoma | Causa | Solución |
|---|---|---|
| `is_connected: false` en los conmutadores | Ryu no está corriendo, o el conmutador no tiene dirección en 192.168.122.0/24 | Comprobar Ryu y `virbr0`; en el conmutador, `udhcpc -i br0`. Si hay cortafuegos, abrir el puerto TCP 6633 |
| No todos los conmutadores se conectan a Ryu, o no aprenden su «puerto de subida» | Se conectaron antes de que el controlador estuviera listo | `modo_sdn` ya conecta primero los bloques y al final el núcleo, y espera; si persiste, repetir la medición (el ejecutor reanuda) |
| Iperf2 dice `multicast join failed: No such device` | El equipo no tiene ruta para 224.0.0.0/4 | `ip route replace 224.0.0.0/4 dev eth0` en el equipo (`preparar_entorno.py` lo hace) |
| Con el snooping de Open vSwitch no pasa ningún paquete multicast | Con `mcast-snooping-disable-flood-unregistered` y sin consultor IGMP, los conmutadores no aprenden receptores | Usar la configuración por defecto, como el control del experimento (ver límites en `gns3/multicast/README.md`) |
| Mediciones lentas o pérdidas que no aparecen en los datos publicados | Equipo con poca memoria o procesador ocupado | Cerrar otros programas; los valores absolutos dependen del equipo, las diferencias en bytes no |
| La ejecución se interrumpió | Corte de energía, cierre de la terminal | Volver a ejecutar el mismo comando: continúa desde la última medición registrada |
| `ModuleNotFoundError: scipy` o `matplotlib` | Faltan librerías en el Python del sistema | `sudo apt install python3-scipy python3-matplotlib` |

Si un problema no aparece aquí, revise primero el registro del controlador (`gns3/multicast/datos/ryu/`) y la salida
de `ovs-vsctl show` del conmutador involucrado: la mayoría de las fallas son de conexión con el controlador.
