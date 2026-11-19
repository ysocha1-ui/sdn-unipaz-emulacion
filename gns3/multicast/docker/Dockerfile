# Imagen de los hosts del experimento multicast: la imagen ipterm de GNS3 (iperf3, tcpdump, ping) más iperf2,
# que sí genera y recibe tráfico UDP multicast (iperf3 no lo soporta).
# Construcción: docker build -t unipaz/ipterm-mc:1 gns3/multicast/docker
FROM gns3/ipterm:latest
RUN apt-get update \
 && apt-get install -y --no-install-recommends iperf \
 && rm -rf /var/lib/apt/lists/*
