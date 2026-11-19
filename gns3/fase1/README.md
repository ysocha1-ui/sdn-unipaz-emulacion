# Fase 1 — Núcleo de la red conectado al controlador

Primera etapa de construcción de la topología en GNS3 (apartado 4.3 del documento). Su objetivo fue comprobar que el
plano de control SDN funcionaba antes de agregar los bloques: un conmutador Open vSwitch gobernado por Ryu mediante
OpenFlow 1.3.

> Para replicar los experimentos no hace falta repetir esta fase: el proyecto portable
> (`gns3/multicast/paquete/Fase1-Nucleo-Administrativa.gns3project`) ya la contiene. Esta guía documenta cómo se hizo.

## Topología

```
ISP-Mediacomerce (NAT) ── Raisecom-Mediocomer ──┐
                                                ├── Router-Borde ── Core-Switch-48p ── Router-Fibra ── (bloques)
ISP-Ufinet (NAT) ──────── Raisecom-Unifet ──────┘                        │
                                                                OpenFlow 1.3 (TCP 6633)
                                                                         ▼
                                                        Ryu en el equipo anfitrión (192.168.122.1)
```

- **Core-Switch-48p** es un Open vSwitch (contenedor `gns3/openvswitch`): es el único equipo de esta fase que habla
  OpenFlow con el controlador.
- **Router-Borde, Router-Fibra y los Raisecom** se representan con conmutadores Ethernet de GNS3: no hay imágenes de los
  equipos reales (MikroTik CCR, Raisecom), y para el objetivo de la fase basta con que pasen el tráfico.
- **El firewall institucional queda fuera de la emulación**: sigue existiendo en la red real con sus políticas, y la
  propuesta SDN no lo reemplaza.

## Pasos

1. En GNS3, crear el proyecto `Fase1-Nucleo-Administrativa`.
2. Arrastrar al lienzo los nodos de la figura y renombrarlos (clic derecho → *Change hostname*): dos **NAT**, cuatro
   **Ethernet switch** (Raisecom-Mediocomer, Raisecom-Unifet, Router-Borde, Router-Fibra) y un **Open vSwitch**
   (Core-Switch-48p).
3. Cablear la cadena como en la figura y encender todos los nodos (*Start all nodes*). El Open vSwitch tarda 20 a 30
   segundos.
4. En la consola de **Core-Switch-48p** (Alpine Linux: la sesión ya es de root, sin `sudo` ni `dhclient`):

   ```sh
   udhcpc -i br0                                        # dirección en 192.168.122.0/24
   ip route                                             # debe mostrar: default via 192.168.122.1
   ovs-vsctl set bridge br0 protocols=OpenFlow13
   ovs-vsctl set-controller br0 tcp:192.168.122.1:6633
   ovs-vsctl show                                       # is_connected: false (Ryu aún no corre)
   ```

5. En una terminal del equipo anfitrión (no en la consola de GNS3):

   ```bash
   ~/ryu-controller/venv/bin/ryu-manager ryu.app.simple_switch_13
   ```

6. **Criterio de cierre:** en la consola del conmutador, `ovs-vsctl show` muestra `is_connected: true`; en Ryu
   aparecen mensajes `packet in` al generar tráfico, y `ovs-ofctl -O OpenFlow13 dump-flows br0` lista las reglas
   instaladas.

Nombres y enlaces de toda la topología: [`../topologia.md`](../topologia.md).
