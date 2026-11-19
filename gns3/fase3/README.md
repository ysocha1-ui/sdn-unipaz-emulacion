# Fase 3 — Los trece bloques del campus

Tercera etapa (apartado 4.3 del documento): se agregaron los diez bloques restantes con el mismo patrón validado en la
fase 2, respetando la jerarquía física del inventario: bloques conectados directamente al enrutador de fibra y bloques
encadenados a través de otros.

> Para replicar no hace falta repetir esta fase: el proyecto portable ya tiene los trece bloques.

## Archivos

| Archivo | Qué es |
|---|---|
| `construir_fase3.py` | Crea por la API de GNS3 los conmutadores Open vSwitch de los diez bloques y los equipos de prueba, los cablea según [`../topologia.md`](../topologia.md) y conecta cada conmutador a Ryu |
| `registro_construccion.txt` | Registro de lo que hizo el script, paso a paso |
| `verificar_fase3.py` | Comprueba que los trece conmutadores tienen sesión OpenFlow activa con el controlador y que hay conectividad desde el bloque más profundo |
| `verificacion_fase3.txt` | Resultado de la verificación usado en el documento |

## Uso

Con el proyecto de las fases 1 y 2 abierto en GNS3 y Ryu corriendo:

```bash
python3 gns3/fase3/construir_fase3.py
python3 gns3/fase3/verificar_fase3.py
```

**Criterio de cierre:** los trece conmutadores con `is_connected: true` y conectividad de extremo a extremo desde
Laboratorio 2, el bloque más profundo (cinco saltos desde el núcleo).

Los nodos del experimento multicast (un emisor y cinco receptores) se agregaron después, con
[`../multicast/agregar_hosts_multicast.py`](../multicast/agregar_hosts_multicast.py).
