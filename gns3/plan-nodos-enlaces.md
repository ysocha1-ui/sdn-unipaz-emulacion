# Plan de nodos y enlaces — Topología GNS3 Campus UNIPAZ

Referencia para Fases 1, 2 y 3. Refleja exactamente la jerarquía del inventario del campus — no agregar
enlaces que no estén aquí sin actualizar primero este documento y el inventario del campus.

## Convención de nombres de nodo en GNS3

`<TipoEquipo>-<Bloque>` — ej. `Switch-LBA`, `NVR-LBA`, `Core-Switch-48p`.
Todos los nodos OVS de bloque llevan el bridge por defecto `br0` (GNS3 mete ahí todas sus
interfaces automáticamente).

## Fase 1 — Núcleo (bloque Administrativa) — ESTADO: en construcción

> **Actualización 2026-09-29:** el Firewall Sophos queda fuera de la simulación (sigue en la red real con sus políticas) y el Router de borde tampoco se simula; el nodo NAT representa todo lo que está aguas arriba del Core Switch.

| # | Nodo A | Puerto | Nodo B | Puerto | Tipo de nodo B |
|---|---|---|---|---|---|
| 1 | NAT | nat0 | Core-Switch-48p | eth0 | **OVS (habla OpenFlow 1.3 con Ryu)** |
| 2 | Core-Switch-48p | eth1 | Router-Fibra | e0 | Ethernet switch GNS3 (sin imagen CCR2004 importada) |

Controlador: Ryu en `~/ryu-controller/venv`, `tcp:192.168.122.1:6633` (IP real verificada de la
VM en la red NAT/libvirt de GNS3, ver `fase1-nucleo-administrativa.md`), conectado a
`Core-Switch-48p`. Decisión de nodo confirmada: sin imágenes de router/firewall importadas en el
entorno (verificado 2026-09-15), solo Router-Fibra se simula como
Ethernet switch de GNS3 hasta que se importen las imágenes reales — no afecta el cableado ni el
plano OpenFlow, que solo involucra a Core-Switch-48p.

## Fase 2 — Patrón de bloque (pendiente hasta validar Fase 1)

Bloques de prueba: **Salones antiguos** (conexión directa al Router de fibra) y **Aprisco**
(encadenado vía Salones antiguos), según el inventario del campus.

| # | Nodo A | Puerto | Nodo B | Puerto | Tipo de nodo B |
|---|---|---|---|---|---|
| 3 | Router-Fibra | eth1 | Switch-SalonesAntiguos | eth0 | OVS |
| 4 | Switch-SalonesAntiguos | eth1 | Switch-Aprisco | eth0 | OVS (encadenado) |

Verificar el patrón completo (cableado + `set-controller` + `is_connected: true` en ambos OVS)
antes de tocar Fase 3.

## Fase 3 — Replicación (pendiente)

Aplicar el mismo patrón de Fase 2 a los 10 bloques restantes (13 bloques − Administrativa en Fase 1 − Salones antiguos y Aprisco en Fase 2: 5 conectan directo al Router de fibra y 5 van encadenados). Tabla de destino final (según
jerarquía del inventario del campus — **no inventar nodos intermedios**, especialmente ojo con el error ya
corregido del falso "Core Switch GREIP"):

### Conectan directo al Router de fibra óptica (5 bloques, adicionales a Salones antiguos ya en Fase 2; Núcleo de producción usa 2 troncales, por eso son 6 enlaces)

| Nodo A | Puerto | Nodo B (bloque) |
|---|---|---|
| Router-Fibra | eth2 | Switch-NucleoProduccion-A (Tp-Link TL-SF1008D) |
| Router-Fibra | eth3 | Switch-NucleoProduccion-B (Tp-Link TL-SF1008D) — enlace independiente de A |
| Router-Fibra | eth4 | Switch-Porteria |
| Router-Fibra | eth5 | Switch-LBA (Laboratorio 3) |
| Router-Fibra | eth6 | Switch-Biblioteca |
| Router-Fibra | eth7 | Switch-EdificioAulas |

Nota: el Router de fibra es un Mikrotik CCR2004-1G-12S+2XS de 12 puertos SFP+; con Fase 1 (1
puerto usado hacia Core-Switch-48p aguas arriba, no cuenta) + Fase 2 Salones antiguos + estas
6 líneas ya son 7 puertos hacia bloques — dentro del límite físico de 12.

### Bloques encadenados (cuelgan de otro bloque, NO directo del Router de fibra)

| Nodo A (bloque padre) | Nodo B (bloque hijo) | Relación real |
|---|---|---|
| Switch-Porteria | Switch-Entrada | Entrada ← Portería |
| Switch-Entrada | Switch-ParadaBuses | Parada de autobuses ← Entrada |
| Switch-LBA | NVR-LBA → Cámaras-Psicosocial | Psicosocial no tiene switch propio: sus 2 cámaras van directo al NVR de LBA |
| Switch-LBA | Switch-LAB2 (GREIP) | Laboratorio 2 ← LBA directo (NO existe "Core Switch GREIP") |
| Switch-LBA | Switch-LAB1 | Laboratorio 1 ← LBA directo |

Profundidad máxima resultante en la simulación desde el Core-48p: 4 saltos (Core-48p → Router-Fibra
→ Switch-LBA → Switch-LAB2 → AP/cámara); son los 5 saltos del inventario contando el firewall físico.

## Puntos únicos de falla a marcar visualmente en GNS3 (opcional, sugerido para Fase 3)

Rotula con color/ícono distinto estos 2 nodos simulados — si caen, se pierde todo el campus
(el Router de borde y el Firewall también lo son en la red física, pero no forman parte de la simulación):
`Core-Switch-48p`, `Router-Fibra`.

Y recordar en las pruebas de resiliencia: si cae `Switch-LBA`, caen con él `Switch-LAB2`,
`Switch-LAB1` y las cámaras de Psicosocial (no tienen ruta alterna en el diseño actual).

## Pendientes de verificar contra inventario antes de construir Fase 3

- Confirmar en `inventario/inventario_maestro_UNIPAZ.xlsx` el número exacto de switches/APs
  por bloque para no simplificar de más al representar cada bloque como un único nodo OVS.
- Confirmar si las 2 cámaras de Psicosocial se modelan en GNS3 como nodos VPCS separados o se
  omiten a nivel de topología de switches (Fase 3, decisión pendiente de discutir con el usuario).
