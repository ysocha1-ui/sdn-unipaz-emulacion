# Topología emulada en GNS3

Generado a partir del proyecto portable (`multicast/paquete/Fase1-Nucleo-Administrativa.gns3project`): son exactamente
los nodos y enlaces del proyecto. La Figura 4 del documento muestra esta misma topología organizada por niveles.

## Nodos

| Nodo | Tipo |
|---|---|
| ISP-Mediacomerce(NAT) | Salida a internet (NAT) |
| ISP-Ufinet(NAT) | Salida a internet (NAT) |
| Raisecom-Mediocomer | Conmutador Ethernet de GNS3 |
| Raisecom-Unifet | Conmutador Ethernet de GNS3 |
| Router-Borde | Conmutador Ethernet de GNS3 |
| Router-Fibra | Conmutador Ethernet de GNS3 |
| Core-Switch-48p | Open vSwitch |
| Switch-Aprisco | Open vSwitch |
| Switch-Biblioteca | Open vSwitch |
| Switch-EdificioAulas | Open vSwitch |
| Switch-Entrada | Open vSwitch |
| Switch-LAB1 | Open vSwitch |
| Switch-LAB2 | Open vSwitch |
| Switch-LBA | Open vSwitch |
| Switch-NucleoProduccion-A | Open vSwitch |
| Switch-NucleoProduccion-B | Open vSwitch |
| Switch-ParadaBuses | Open vSwitch |
| Switch-Porteria | Open vSwitch |
| Switch-SalonesAntiguos | Open vSwitch |
| Camara-LAB2 | Equipo de prueba (gns3/ipterm) |
| NVR-LBA | Equipo de prueba (gns3/ipterm) |
| PC-Aprisco | Equipo de prueba (gns3/ipterm) |
| PC-LAB2 | Equipo de prueba (gns3/ipterm) |
| Servidor-Nucleo | Equipo de prueba (gns3/ipterm) |
| Emisor-MC | Equipo de prueba con Iperf2 (experimento multicast) |
| Rx-Aprisco | Equipo de prueba con Iperf2 (experimento multicast) |
| Rx-Aulas | Equipo de prueba con Iperf2 (experimento multicast) |
| Rx-Biblioteca | Equipo de prueba con Iperf2 (experimento multicast) |
| Rx-Entrada | Equipo de prueba con Iperf2 (experimento multicast) |
| Rx-LAB2 | Equipo de prueba con Iperf2 (experimento multicast) |

Total: 30 nodos, de ellos 13 conmutadores Open vSwitch (el de núcleo y los de los bloques).

## Enlaces

| Nodo A | Puerto | Nodo B | Puerto |
|---|---|---|---|
| Core-Switch-48p | eth1 | Router-Fibra | e0 |
| Emisor-MC | eth0 | Core-Switch-48p | eth3 |
| ISP-Mediacomerce(NAT) | nat0 | Raisecom-Mediocomer | e0 |
| ISP-Ufinet(NAT) | nat0 | Raisecom-Unifet | e0 |
| PC-Aprisco | eth0 | Switch-Aprisco | eth1 |
| Raisecom-Mediocomer | e1 | Router-Borde | e0 |
| Raisecom-Unifet | e1 | Router-Borde | e1 |
| Router-Borde | e2 | Core-Switch-48p | eth0 |
| Router-Fibra | e1 | Switch-SalonesAntiguos | eth0 |
| Router-Fibra | e2 | Switch-NucleoProduccion-A | eth0 |
| Router-Fibra | e3 | Switch-NucleoProduccion-B | eth0 |
| Router-Fibra | e4 | Switch-Porteria | eth0 |
| Router-Fibra | e5 | Switch-LBA | eth0 |
| Router-Fibra | e6 | Switch-Biblioteca | eth0 |
| Router-Fibra | e7 | Switch-EdificioAulas | eth0 |
| Rx-Aprisco | eth0 | Switch-Aprisco | eth2 |
| Rx-Aulas | eth0 | Switch-EdificioAulas | eth1 |
| Rx-Biblioteca | eth0 | Switch-Biblioteca | eth1 |
| Rx-Entrada | eth0 | Switch-Entrada | eth2 |
| Rx-LAB2 | eth0 | Switch-LAB2 | eth3 |
| Servidor-Nucleo | eth0 | Core-Switch-48p | eth2 |
| Switch-Aprisco | eth0 | Switch-SalonesAntiguos | eth1 |
| Switch-Entrada | eth1 | Switch-ParadaBuses | eth0 |
| Switch-LAB2 | eth1 | PC-LAB2 | eth0 |
| Switch-LAB2 | eth2 | Camara-LAB2 | eth0 |
| Switch-LBA | eth1 | Switch-LAB2 | eth0 |
| Switch-LBA | eth2 | Switch-LAB1 | eth0 |
| Switch-LBA | eth3 | NVR-LBA | eth0 |
| Switch-Porteria | eth1 | Switch-Entrada | eth0 |

Total: 29 enlaces.

## Cómo se corresponde con la red real

- **Router-Borde, Router-Fibra y los dos Raisecom** se representan con conmutadores Ethernet de GNS3, porque no hay
  imágenes de los equipos reales; pasan el tráfico, pero no los gobierna el controlador.
- **El firewall institucional no se emula**: sigue en la red real con sus políticas.
- **Cada bloque es un conmutador Open vSwitch**; Núcleo de producción tiene dos troncales independientes (A y B).
- **Bloques encadenados:** Aprisco cuelga de Salones antiguos; Entrada, de Portería; Parada de buses, de Entrada;
  Laboratorio 1 y Laboratorio 2, de Laboratorio 3 (LBA). Las cámaras de Psicosocial van al grabador de LBA (`NVR-LBA`).
- **Profundidad máxima:** Laboratorio 2, a cuatro saltos del conmutador de núcleo (cinco contando el firewall de la red real).
