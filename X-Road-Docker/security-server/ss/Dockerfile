FROM niis/xroad-security-server-sidecar:7.6.1

ARG XROAD_TOKEN_PIN=TokenPin@123!
ARG XROAD_ADMIN_USER=admin
ARG XROAD_ADMIN_PASSWORD=Admin123123@

RUN rm -f /etc/xroad/conf.d/local.ini
COPY local-config.ini /etc/xroad/conf.d/local.ini
