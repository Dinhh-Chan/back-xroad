FROM niis/xroad-central-server:noble-7.6.1

ARG XROAD_TOKEN_PIN=TokenPin@123!
ARG XROAD_ADMIN_USER=admin
ARG XROAD_ADMIN_PASSWORD=Admin123123@

COPY local-config.ini /etc/xroad/conf.d/local.ini
COPY entrypoint.sh /root/entrypoint.sh
RUN chmod +x /root/entrypoint.sh

RUN deluser xrd
RUN adduser --disabled-password --gecos "" ${XROAD_ADMIN_USER}
RUN echo "${XROAD_ADMIN_USER}:${XROAD_ADMIN_PASSWORD}" | chpasswd
RUN adduser ${XROAD_ADMIN_USER} xroad-registration-officer
RUN adduser ${XROAD_ADMIN_USER} xroad-system-administrator
RUN adduser ${XROAD_ADMIN_USER} xroad-security-officer

CMD ["/root/entrypoint.sh"]
