FROM ghcr.io/orange-opensource/hurl:latest

ARG CA_HOST

ARG CS_HOST
ARG CS_INSTANCE_IDENTIFIER

ARG SS_HOST
ARG SS_PORT
ARG SS_MEMBER_CLASS
ARG SS_MEMBER_CODE
ARG SS_MEMBER_NAME
ARG SS_SECURITY_SERVER_CODE
ARG SS_ADMIN_USER
ARG SS_ADMIN_USER_PASSWORD
ARG SS_TOKEN_PIN

RUN mkdir -p /hurl-src
RUN mkdir -p /hurl-files
RUN mkdir -p /hurl-files/anchors/

ADD setup.hurl /hurl-src/setup.hurl
ADD internal-anchor.xml /hurl-files/anchors/internal-anchor.xml

RUN rm -f /hurl-src/vars.env
RUN echo "ca_host=${CA_HOST}" >> /hurl-src/vars.env
RUN echo "cs_host=${CS_HOST}" >> /hurl-src/vars.env
RUN echo "cs_instance_identifier=${CS_INSTANCE_IDENTIFIER}" >> /hurl-src/vars.env
RUN echo "ss_host=${SS_HOST}" >> /hurl-src/vars.env
RUN echo "ss_port=${SS_PORT}" >> /hurl-src/vars.env
RUN echo "ss_member_class=${SS_MEMBER_CLASS}" >> /hurl-src/vars.env
RUN echo "ss_member_code=${SS_MEMBER_CODE}" >> /hurl-src/vars.env
RUN echo "ss_member_name=${SS_MEMBER_NAME}" >> /hurl-src/vars.env
RUN echo "ss_security_server_code=${SS_SECURITY_SERVER_CODE}" >> /hurl-src/vars.env
RUN echo "ss_admin_user=${SS_ADMIN_USER}" >> /hurl-src/vars.env
RUN echo "ss_admin_user_password=${SS_ADMIN_USER_PASSWORD}" >> /hurl-src/vars.env
RUN echo "ss_token_pin=${SS_TOKEN_PIN}" >> /hurl-src/vars.env