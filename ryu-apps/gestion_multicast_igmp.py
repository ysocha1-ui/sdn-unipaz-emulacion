"""Gestión de tráfico IP multicast para el campus UNIPAZ: consultor IGMP + IGMP snooping sobre OpenFlow 1.3.

Qué hace (en una frase): el controlador aprende qué puertos de cada conmutador tienen receptores de un grupo multicast
y programa los conmutadores para que el flujo del grupo salga SOLO por esos puertos; el multicast sin receptores se descarta
en lugar de inundar la red, que es lo que hace un conmutador tradicional sin IGMP snooping.

Por qué no se usó ryu.lib.igmplib tal cual:
  - solo entiende reportes IGMP v1/v2 y los hosts Linux envían v3 (esta app entiende v2 y v3);
  - trata como miembro cualquier puerto por el que llegue un reporte; en la emulación el «enrutador de fibra» es un
    conmutador Ethernet de GNS3 que inunda los reportes, así que los conmutadores de bloques sin receptores aprenderían
    miembros falsos por su puerto de subida (aquí los reportes que llegan por el puerto de subida se ignoran);
  - inunda el multicast de grupos sin miembros (aquí se descarta).

Cómo funciona:
  1. Al conectarse un conmutador se instalan tres reglas base: IGMP -> controlador (prioridad 200), cualquier otro IPv4
     multicast -> descartar (prioridad 100) y el table-miss que hereda de simple_switch_13.
  2. El conmutador del servidor multicast (datapath id = MC_CONSULTOR_DPID) hace de consultor: cada INTERVALO_CONSULTA s
     inunda una consulta general IGMP. Los demás conmutadores aprenden por qué puerto les llega la consulta
     (su «puerto de subida») y la reenvían hacia abajo.
  3. Cuando un host se une a un grupo envía un reporte. El conmutador lo recibe en un puerto que no es el de subida,
     registra el puerto como miembro, programa la regla «ipv4_dst = grupo -> salir por los puertos miembros» (prioridad
     300) y reenvía el reporte por el puerto de subida, para que los conmutadores de arriba aprendan que hay receptores
     por ese lado.
  4. La membresía es de estado blando: si un puerto no vuelve a reportar en VENCIMIENTO s, se retira. No se implementa
     la salida rápida (leave): la baja de un miembro se detecta por vencimiento.

Qué debería observarse al ejecutarla:
  - En la salida de Ryu, líneas «[MC] ...» con cada consulta enviada, cada unión (grupo, puerto) y cada vencimiento.
  - `ovs-ofctl -O OpenFlow13 dump-flows br0` en un conmutador con miembros muestra una regla con `nw_dst=<grupo>` y
    `actions=output:<puertos miembros>`; en un conmutador sin miembros solo se ve la regla de descarte del multicast.

Variables de entorno: MC_CONSULTOR_DPID (entero, por defecto 1), MC_IP_CONSULTOR (por defecto 172.30.0.254).
Python 3.8, OpenFlow 1.3. Ejecutar: ryu-manager ryu-apps/gestion_multicast_igmp.py
"""
import os
import time

from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import DEAD_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.lib import hub
from ryu.lib.dpid import dpid_to_str
from ryu.lib.packet import ethernet, igmp, ipv4, packet
from ryu.ofproto import ether, inet, ofproto_v1_3

INTERVALO_CONSULTA = 20          # s entre consultas generales
RESPUESTA_MAX = 5                # s que tienen los hosts para responder una consulta
VENCIMIENTO = 2 * INTERVALO_CONSULTA + RESPUESTA_MAX
PRIORIDAD_DESCARTE = 100         # multicast sin receptores registrados
PRIORIDAD_IGMP = 200             # mensajes IGMP -> controlador
PRIORIDAD_GRUPO = 300            # flujo de un grupo -> puertos miembros
CONSULTOR_DPID = int(os.environ.get('MC_CONSULTOR_DPID', '1'))
IP_CONSULTOR = os.environ.get('MC_IP_CONSULTOR', '172.30.0.254')


def es_enlace_local(grupo):
    """224.0.0.0/24 es de control de la red (no se gestiona por grupo)."""
    return grupo.startswith('224.0.0.')


class GestionMulticast(simple_switch_13.SimpleSwitch13):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(GestionMulticast, self).__init__(*args, **kwargs)
        self.datapaths = {}      # dpid -> datapath conectado
        self.subida = {}         # dpid -> puerto por el que llega la consulta (hacia el consultor)
        self.miembros = {}       # dpid -> grupo -> {puerto: instante del último reporte}
        hub.spawn(self._barrido_vencimientos)

    # ------------------------------------------------------------------------------------------------------------
    # Conexión de conmutadores y reglas base
    # ------------------------------------------------------------------------------------------------------------
    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _cambio_de_estado(self, ev):
        dp = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            self.datapaths[dp.id] = dp
            self._reglas_base(dp)
            self.subida.pop(dp.id, None)
            self.miembros[dp.id] = {}
            self.logger.info('[MC] conectado sw=%s', dpid_to_str(dp.id))
            if dp.id == CONSULTOR_DPID:
                # Se espera 2 s para que las consultas lleguen a conmutadores que ya estén conectados.
                hub.spawn_after(2, self._bucle_consulta, dp)
        elif ev.state == DEAD_DISPATCHER and dp.id in self.datapaths:
            del self.datapaths[dp.id]
            self.logger.info('[MC] desconectado sw=%s', dpid_to_str(dp.id))

    def _reglas_base(self, dp):
        ofp, parser = dp.ofproto, dp.ofproto_parser
        # IGMP -> controlador: necesita verlo para aprender consultas y reportes.
        self._flow(dp, PRIORIDAD_IGMP, parser.OFPMatch(eth_type=ether.ETH_TYPE_IP, ip_proto=inet.IPPROTO_IGMP),
                   [parser.OFPActionOutput(ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER)])
        # Multicast sin receptores registrados: se descarta (en un conmutador tradicional se inunda).
        self._flow(dp, PRIORIDAD_DESCARTE,
                   parser.OFPMatch(eth_type=ether.ETH_TYPE_IP, ipv4_dst=('224.0.0.0', '240.0.0.0')), [])

    def _flow(self, dp, prioridad, match, acciones):
        ofp, parser = dp.ofproto, dp.ofproto_parser
        inst = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, acciones)] if acciones else []
        dp.send_msg(parser.OFPFlowMod(datapath=dp, priority=prioridad, match=match, instructions=inst))

    def _programar_grupo(self, dp, grupo):
        """Instala (o quita, si ya no hay miembros) la regla del grupo en este conmutador."""
        ofp, parser = dp.ofproto, dp.ofproto_parser
        puertos = sorted(self.miembros[dp.id].get(grupo, {}))
        match = parser.OFPMatch(eth_type=ether.ETH_TYPE_IP, ipv4_dst=grupo)
        if puertos:
            self._flow(dp, PRIORIDAD_GRUPO, match, [parser.OFPActionOutput(p) for p in puertos])
        else:
            dp.send_msg(parser.OFPFlowMod(datapath=dp, command=ofp.OFPFC_DELETE_STRICT, priority=PRIORIDAD_GRUPO,
                                          match=match, out_port=ofp.OFPP_ANY, out_group=ofp.OFPG_ANY))
            self.miembros[dp.id].pop(grupo, None)

    # ------------------------------------------------------------------------------------------------------------
    # Consultor
    # ------------------------------------------------------------------------------------------------------------
    def _bucle_consulta(self, dp):
        ofp, parser = dp.ofproto, dp.ofproto_parser
        while dp.id in self.datapaths:
            q = igmp.igmp(msgtype=igmp.IGMP_TYPE_QUERY, maxresp=RESPUESTA_MAX * 10, csum=0, address='0.0.0.0')
            pkt = packet.Packet()
            pkt.add_protocol(ethernet.ethernet(dst='01:00:5e:00:00:01', src=dp.ports[ofp.OFPP_LOCAL].hw_addr,
                                               ethertype=ether.ETH_TYPE_IP))
            pkt.add_protocol(ipv4.ipv4(total_length=len(ipv4.ipv4()) + len(q), proto=inet.IPPROTO_IGMP, ttl=1,
                                       src=IP_CONSULTOR, dst='224.0.0.1'))
            pkt.add_protocol(q)
            pkt.serialize()
            self._paquete_salida(dp, pkt.data, ofp.OFPP_CONTROLLER, ofp.OFPP_FLOOD)
            self.logger.info('[MC] consulta general enviada sw=%s', dpid_to_str(dp.id))
            hub.sleep(INTERVALO_CONSULTA)

    def _paquete_salida(self, dp, datos, in_port, out_port):
        ofp, parser = dp.ofproto, dp.ofproto_parser
        dp.send_msg(parser.OFPPacketOut(datapath=dp, buffer_id=ofp.OFP_NO_BUFFER, in_port=in_port,
                                        actions=[parser.OFPActionOutput(out_port)], data=datos))

    # ------------------------------------------------------------------------------------------------------------
    # Mensajes que llegan al controlador
    # ------------------------------------------------------------------------------------------------------------
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        puerto = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        ip = pkt.get_protocol(ipv4.ipv4)
        if ip is not None and ip.proto == inet.IPPROTO_IGMP:
            self._igmp(dp, puerto, msg, pkt.get_protocol(igmp.igmp))
            return
        if ip is not None and 224 <= int(ip.dst.split('.')[0]) <= 239:
            return   # multicast IPv4 de datos: la regla de descarte ya lo cubre; no se inunda
        super(GestionMulticast, self)._packet_in_handler(ev)   # el resto (ARP, unicast) lo resuelve simple_switch_13

    def _igmp(self, dp, puerto, msg, mensaje):
        if mensaje is None:
            return
        if isinstance(mensaje, igmp.igmpv3_report):
            for reg in mensaje.records:
                unirse = reg.type_ in (igmp.MODE_IS_EXCLUDE, igmp.CHANGE_TO_EXCLUDE_MODE) or (
                    reg.type_ in (igmp.MODE_IS_INCLUDE, igmp.CHANGE_TO_INCLUDE_MODE, igmp.ALLOW_NEW_SOURCES)
                    and reg.srcs)
                if unirse and not es_enlace_local(reg.address):
                    self._reporte(dp, puerto, msg, reg.address)
        elif mensaje.msgtype in (igmp.IGMP_TYPE_REPORT_V1, igmp.IGMP_TYPE_REPORT_V2):
            if not es_enlace_local(mensaje.address):
                self._reporte(dp, puerto, msg, mensaje.address)
        elif mensaje.msgtype == igmp.IGMP_TYPE_QUERY and dp.id != CONSULTOR_DPID:
            self._consulta(dp, puerto, msg)
        # La baja (leave) no se procesa: el puerto se retira por vencimiento.

    def _consulta(self, dp, puerto, msg):
        """Aprende el puerto de subida y reenvía la consulta hacia abajo (a todos los demás puertos)."""
        if self.subida.get(dp.id) != puerto:
            self.subida[dp.id] = puerto
            self.logger.info('[MC] sw=%s puerto de subida=%s', dpid_to_str(dp.id), puerto)
        self._paquete_salida(dp, msg.data, puerto, dp.ofproto.OFPP_FLOOD)

    def _reporte(self, dp, puerto, msg, grupo):
        subida = self.subida.get(dp.id)
        if puerto == subida:
            return   # reporte de otro lado inundado por el enrutador de fibra: no es un miembro de este conmutador
        tabla = self.miembros[dp.id].setdefault(grupo, {})
        nuevo = puerto not in tabla
        tabla[puerto] = time.time()
        if nuevo:
            self._programar_grupo(dp, grupo)
            self.logger.info('[MC] union sw=%s grupo=%s puerto=%s miembros=%s', dpid_to_str(dp.id), grupo, puerto,
                             sorted(tabla))
        if subida is not None:
            # Se reenvía hacia el consultor para que los conmutadores de arriba sepan que hay receptores por este lado.
            self._paquete_salida(dp, msg.data, puerto, subida)

    # ------------------------------------------------------------------------------------------------------------
    # Vencimiento de membresías
    # ------------------------------------------------------------------------------------------------------------
    def _barrido_vencimientos(self):
        while True:
            hub.sleep(5)
            ahora = time.time()
            for dpid, grupos in list(self.miembros.items()):
                dp = self.datapaths.get(dpid)
                if dp is None:
                    continue
                for grupo, puertos in list(grupos.items()):
                    vencidos = [p for p, t in puertos.items() if ahora - t > VENCIMIENTO]
                    for p in vencidos:
                        del puertos[p]
                        self.logger.info('[MC] vencimiento sw=%s grupo=%s puerto=%s', dpid_to_str(dpid), grupo, p)
                    if vencidos:
                        self._programar_grupo(dp, grupo)
