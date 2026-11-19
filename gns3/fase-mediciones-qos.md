# Mediciones QoS — escenario tradicional vs SDN (GNS3)

Objetivo: obtener datos reales de **latencia, jitter y pérdida de paquetes** en los dos escenarios
(tradicional y SDN), con 10 repeticiones cada uno, para el capítulo 4 y la prueba t.

Tiempo estimado: 1,5 a 2 horas (montaje 30–45 min, mediciones ~40 min, capturas 15 min).

---

## Idea general (por qué se hace así)

- **Mismos equipos, dos modos.** La comparación es justa solo si la topología no cambia. Por eso
  se usan los mismos Open vSwitch en ambos escenarios y lo único que cambia es quién decide el
  reenvío:
  - **Tradicional:** cada OVS funciona solo, como un switch normal que aprende direcciones
    (modo `standalone`, acción `NORMAL`). Es el equivalente a los switches actuales del campus.
  - **SDN:** los OVS no deciden nada; le preguntan a Ryu (modo `secure` + controlador).
- **Camino encadenado.** Se mide entre un host en el bloque más profundo (Aprisco, que cuelga de
  Salones antiguos) y un host en el núcleo, porque esa cadena es justamente el problema que
  encontró el inventario.
- **10 repeticiones por escenario.** La prueba t necesita varias muestras; con una sola medición
  no hay estadística.
- **Dos niveles de carga** (sin carga y con carga) para ver qué pasa cuando la red está ocupada.

---

## Paso 1 — Agregar nodos (Fase 2 del plan de nodos)

Abre el proyecto `Fase1-Nucleo-Administrativa` en GNS3.

1. Arrastra **2 nodos Open vSwitch** y renómbralos `Switch-SalonesAntiguos` y `Switch-Aprisco`.
2. Arrastra **2 hosts de prueba**. Usa el appliance **ipterm** (Marketplace de GNS3 → buscar
   "ipterm" → instalar). Trae `ping`, `iperf3` y `tcpdump` sin instalar nada más.
   Renómbralos `PC-Aprisco` y `Servidor-Nucleo`.
   - *Por qué ipterm y no VPCS:* VPCS no tiene iperf3, y sin iperf3 no hay jitter ni pérdida.
3. Cablea exactamente así:

| Origen | Puerto | Destino | Puerto |
|---|---|---|---|
| Router-Fibra | e1 | Switch-SalonesAntiguos | eth0 |
| Switch-SalonesAntiguos | eth1 | Switch-Aprisco | eth0 |
| Switch-Aprisco | eth1 | PC-Aprisco | eth0 |
| Core-Switch-48p | eth2 | Servidor-Nucleo | eth0 |

Camino de la prueba: PC-Aprisco → Aprisco → Salones antiguos → Router-Fibra → Core-Switch-48p →
Servidor-Nucleo (3 OVS en la cadena).

4. Click derecho en el lienzo → **Start all nodes**. Espera a que todo quede en verde.

**Captura para el documento:** el lienzo completo de GNS3 con todos los nodos en verde
(Figura: topología de pruebas).

---

## Paso 2 — Dar IP a los hosts

En la consola de **Servidor-Nucleo**:
```
ip addr add 172.30.0.12/16 dev eth0
ip link set eth0 up
```
En la consola de **PC-Aprisco**:
```
ip addr add 172.30.0.11/16 dev eth0
ip link set eth0 up
```
*Por qué 172.30:* es el rango de la VLAN 30 (Estudiantes) según el plan de direccionamiento.

---

## Paso 3 — Conectar los OVS nuevos a Ryu

En la consola de **Switch-SalonesAntiguos** y luego en **Switch-Aprisco** (Alpine, ya eres root):
```
udhcpc -i br0
ovs-vsctl set bridge br0 protocols=OpenFlow13
```
(El `Core-Switch-48p` ya quedó configurado en la Fase 1; si reiniciaste el nodo, repite
`udhcpc -i br0` en él también.)

---

## Paso 4 — Escenario TRADICIONAL

**4.1** Asegúrate de que **Ryu NO esté corriendo** (si está abierto, Ctrl+C en su terminal).

**4.2** En **cada uno de los 3 OVS** (Core-Switch-48p, Switch-SalonesAntiguos, Switch-Aprisco):
```
ovs-vsctl del-controller br0
ovs-vsctl set-fail-mode br0 standalone
ovs-ofctl -O OpenFlow13 dump-flows br0
```
Verificación: el `dump-flows` muestra una regla con `actions=NORMAL`. Eso significa "switch
normal, aprende solo".

**4.3** Prueba que hay conexión. En **PC-Aprisco**:
```
ping -c 3 172.30.0.12
```
Deben responder los 3. Si no responde, revisa el cableado del Paso 1 antes de seguir.

**4.4** Levanta los servidores de iperf3 en **Servidor-Nucleo**:
```
iperf3 -s -D
iperf3 -s -p 5202 -D
```
(El puerto 5201 es para medir; el 5202 es para la carga de fondo.)

**4.5 Medición SIN carga.** En **PC-Aprisco**, copia y pega todo el bloque:
```
for i in $(seq 1 10); do
  echo "== Corrida $i ==" >> /root/trad_base.txt
  ping -c 20 -i 0.2 -q 172.30.0.12 | tail -1 >> /root/trad_base.txt
  iperf3 -c 172.30.0.12 -u -b 10M -t 20 | grep receiver >> /root/trad_base.txt
  sleep 2
done
cat /root/trad_base.txt
```
Tarda ~4 minutos. Qué mide cada línea:
- `ping ... | tail -1` → latencia (rtt min/**avg**/max/mdev en ms).
- `iperf3 -u -b 10M` → un flujo de video simulado de 10 Mbit/s durante 20 s; la línea
  `receiver` trae el **jitter (ms)** y la **pérdida (%)**.

**Captura para el documento:** la salida del `cat` en pantalla.

**4.6 Medición CON carga.** En **PC-Aprisco**, primero lanza la carga de fondo y luego el bloque:
```
iperf3 -c 172.30.0.12 -p 5202 -u -b 200M -t 400 > /dev/null &
sleep 3
for i in $(seq 1 10); do
  echo "== Corrida $i ==" >> /root/trad_carga.txt
  ping -c 20 -i 0.2 -q 172.30.0.12 | tail -1 >> /root/trad_carga.txt
  iperf3 -c 172.30.0.12 -u -b 10M -t 20 | grep receiver >> /root/trad_carga.txt
  sleep 2
done
cat /root/trad_carga.txt
```
*Por qué:* la carga de 200 Mbit/s compite por la misma cadena de enlaces, como pasa en el campus
cuando muchos usuarios usan la red a la vez.

---

## Paso 5 — Escenario SDN

**5.1** En la terminal de la VM, levanta Ryu:
```
cd ~/ryu-controller && source venv/bin/activate
ryu-manager ryu.app.simple_switch_13
```

**5.2** En **cada uno de los 3 OVS**:
```
ovs-vsctl set-fail-mode br0 secure
ovs-vsctl set-controller br0 tcp:192.168.122.1:6633
ovs-vsctl show
```
Verificación: los 3 muestran `is_connected: true`.

**Captura para el documento:** `ovs-vsctl show` con `is_connected: true` y la terminal de Ryu
mostrando los `packet-in`.

**5.3** En **PC-Aprisco**: `ping -c 3 172.30.0.12` (deben responder). Si los servidores iperf3
se cayeron, repite el Paso 4.4 en Servidor-Nucleo.

**5.4 Medición SIN carga:** el mismo bloque del 4.5, pero cambiando el archivo a
`/root/sdn_base.txt` (en las dos líneas `>>` y en el `cat`).

**5.5 Medición CON carga:** el mismo bloque del 4.6, cambiando el archivo a
`/root/sdn_carga.txt`.

**5.6** Al final, en uno de los OVS:
```
ovs-ofctl -O OpenFlow13 dump-flows br0
```
**Captura para el documento:** las reglas que instaló Ryu.

---

## Paso 6 — Captura con Wireshark (evidencia)

Durante una corrida cualquiera: click derecho sobre el enlace `Switch-Aprisco ↔ PC-Aprisco` →
**Start capture**. Deja correr unos segundos y toma la captura de pantalla de Wireshark.
*Por qué:* demuestra que el tráfico pasó realmente por la red emulada.

---

## Paso 7 — Entregar los datos

Haz `cat` de los 4 archivos y copia el texto (o toma foto clara de cada uno):
- `/root/trad_base.txt`
- `/root/trad_carga.txt`
- `/root/sdn_base.txt`
- `/root/sdn_carga.txt`

Con eso se arman la tabla de resultados, la prueba t de Student, las gráficas y se cierran los
`[Pendiente]` de los apartados 4.4, 4.5, la conclusión del tercer objetivo, el resumen y el abstract.

---

## Advertencias honestas (léelas antes de interpretar)

- **El resultado puede no favorecer al SDN.** Con `simple_switch_13`, Ryu solo reemplaza al
  switch normal; no aplica prioridades ni multicast. Puede que salgan números parecidos o incluso
  algo peores en SDN por el primer paquete que va al controlador. Eso **también es un resultado
  válido** y se reporta tal cual; no se ajustan los datos.
- **El flujo de prueba es UDP unicast,** no multicast nativo (iperf3 no hace multicast). Se
  declara así en el documento, en coherencia con lo encontrado sobre Meet.
- **El tiempo de conmutación por falla entre proveedores no se puede medir** con la simulación
  actual: la cadena de borde son switches Ethernet de GNS3 sin enrutamiento ni protocolo de
  respaldo entre proveedores. Se recomienda declararlo como limitación en vez de dejarlo pendiente.
- Las cifras dependen del computador donde corre GNS3; son válidas para comparar los dos
  escenarios entre sí, no como valores de la red real.
