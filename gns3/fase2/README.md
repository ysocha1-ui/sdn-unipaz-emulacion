# Fase 2 — Cadena de prueba y experimento 1 (calidad de servicio con tráfico unicast)

Segunda etapa (apartados 4.4 y 4.5 del documento): se agregaron los bloques **Salones antiguos** y **Aprisco**, que
forman la cadena más representativa del campus (un bloque encadenado a otro), y sobre ella se comparó la red
tradicional con la red SDN. Los datos están en [`../mediciones/`](../mediciones/).

> Para repetir el experimento con el proyecto portable ya abierto, empiece en el paso 2: los nodos de esta fase ya
> están en el proyecto.

## Paso 1 — Nodos y enlaces

Dos **Open vSwitch** (`Switch-SalonesAntiguos`, `Switch-Aprisco`) y dos equipos de prueba con la imagen
**gns3/ipterm**, que trae `ping`, `iperf3` y `tcpdump` (`PC-Aprisco`, `Servidor-Nucleo`):

| Origen | Puerto | Destino | Puerto |
|---|---|---|---|
| Router-Fibra | e1 | Switch-SalonesAntiguos | eth0 |
| Switch-SalonesAntiguos | eth1 | Switch-Aprisco | eth0 |
| Switch-Aprisco | eth1 | PC-Aprisco | eth0 |
| Core-Switch-48p | eth2 | Servidor-Nucleo | eth0 |

Camino medido: PC-Aprisco → Aprisco → Salones antiguos → Router-Fibra → Core-Switch-48p → Servidor-Nucleo (tres
conmutadores Open vSwitch en la cadena).

## Paso 2 — Direcciones de los equipos

```sh
# consola de Servidor-Nucleo
ip addr add 172.30.0.12/16 dev eth0 && ip link set eth0 up
iperf3 -s -D                 # puerto 5201: flujo medido
iperf3 -s -p 5202 -D         # puerto 5202: carga de fondo

# consola de PC-Aprisco
ip addr add 172.30.0.11/16 dev eth0 && ip link set eth0 up
ping -c 3 172.30.0.12        # deben responder los tres
```

En la consola de cada Open vSwitch de la cadena: `udhcpc -i br0` y `ovs-vsctl set bridge br0 protocols=OpenFlow13`.

## Paso 3 — Escenario tradicional

Con Ryu detenido, en cada uno de los tres Open vSwitch:

```sh
ovs-vsctl del-controller br0
ovs-vsctl set-fail-mode br0 standalone     # el conmutador aprende solo (regla actions=NORMAL)
```

En **PC-Aprisco**, diez repeticiones sin carga y luego diez con carga de fondo de 40 Mbit/s:

```sh
for i in $(seq 1 10); do echo "== Corrida $i ==" >> /root/trad_base.txt; \
  ping -c 20 -i 0.2 -q 172.30.0.12 | tail -1 >> /root/trad_base.txt; \
  iperf3 -c 172.30.0.12 -u -b 10M -t 20 | grep receiver >> /root/trad_base.txt; sleep 2; done

iperf3 -c 172.30.0.12 -p 5202 -u -b 40M -t 500 > /dev/null & sleep 3
for i in $(seq 1 10); do echo "== Corrida $i ==" >> /root/trad_carga.txt; \
  ping -c 20 -i 0.2 -q 172.30.0.12 | tail -1 >> /root/trad_carga.txt; \
  iperf3 -c 172.30.0.12 -u -b 10M -t 20 | grep receiver >> /root/trad_carga.txt; sleep 2; done
pkill iperf3
```

- `ping ... | tail -1` da la latencia (rtt mín/promedio/máx/desv. en ms).
- `iperf3 -u -b 10M -t 20` simula un flujo de video de 10 Mbit/s durante 20 s; la línea `receiver` trae la variación
  del retardo (jitter) y la pérdida.
- La carga de fondo de 40 Mbit/s es cerca del 70 % de la capacidad del camino emulado (unos 60 Mbit/s con TCP). Una
  primera prueba con 200 Mbit/s saturó el entorno y se descartó.

## Paso 4 — Escenario SDN

En el equipo anfitrión: `~/ryu-controller/venv/bin/ryu-manager ryu.app.simple_switch_13`. En cada Open vSwitch:

```sh
ovs-vsctl set-fail-mode br0 secure
ovs-vsctl set-controller br0 tcp:192.168.122.1:6633
ovs-vsctl show                              # is_connected: true en los tres
```

Repetir los dos bloques del paso 3 cambiando los archivos a `/root/sdn_base.txt` y `/root/sdn_carga.txt`. Al final,
`ovs-ofctl -O OpenFlow13 dump-flows br0` muestra las reglas que instaló Ryu.

## Paso 5 — Evidencia y análisis

- Captura con Wireshark: clic derecho sobre el enlace `Switch-Aprisco ↔ PC-Aprisco` → *Start capture*.
- Los cuatro archivos de resultados se copiaron a [`../mediciones/`](../mediciones/) y se analizan con
  `python3 scripts/graficas_capitulo4.py` (prueba t de Welch, intervalos de confianza y g de Hedges).

## Límites que declara el documento

Las mediciones se hicieron en secuencia (primero el escenario tradicional y después el SDN), con diez repeticiones y
con la aplicación `simple_switch_13`, que reenvía como un conmutador convencional una vez instala sus reglas; el flujo
fue unicast, porque iperf3 no genera multicast. El tráfico multicast se evaluó en el experimento 2
([`../multicast/`](../multicast/)), con orden aleatorio.

**Este experimento se repitió** con orden aleatorio, 30 repeticiones y cargas de 0 a 200 Mbit/s en
[`../replica_unicast/`](../replica_unicast/) (apartado 4.5.1): la diferencia de latencia de esta primera serie
(2,85 ms con 40 Mbit/s) no se confirmó, y las dos arquitecturas ofrecieron la misma calidad de servicio.
