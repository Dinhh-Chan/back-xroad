FROM ghcr.io/orange-opensource/hurl:latest

ARG CA_HOST

ARG CS_HOST
ARG CS_PORT
ARG CS_INSTANCE_IDENTIFIER
ARG CS_ADMIN_USER
ARG CS_ADMIN_USER_PASSWORD
ARG CS_TOKEN_PIN

ARG SSM_HOST
ARG SSM_PORT
ARG SSM_MEMBER_CLASS
ARG SSM_MEMBER_CODE
ARG SSM_MEMBER_NAME
ARG SSM_SECURITY_SERVER_CODE
ARG SSM_ADMIN_USER
ARG SSM_ADMIN_USER_PASSWORD
ARG SSM_TOKEN_PIN

RUN mkdir -p /hurl-src
RUN mkdir -p /hurl-files

ADD setup.hurl /hurl-src/setup.hurl
RUN rm -f /hurl-src/vars.env
RUN echo "ca_host=${CA_HOST}" >> /hurl-src/vars.env
RUN echo "cs_host=${CS_HOST}" >> /hurl-src/vars.env
RUN echo "cs_port=${CS_PORT}" >> /hurl-src/vars.env
RUN echo "cs_instance_identifier=${CS_INSTANCE_IDENTIFIER}" >> /hurl-src/vars.env
RUN echo "cs_admin_user=${CS_ADMIN_USER}" >> /hurl-src/vars.env
RUN echo "cs_admin_user_password=${CS_ADMIN_USER_PASSWORD}" >> /hurl-src/vars.env
RUN echo "cs_token_pin=${CS_TOKEN_PIN}" >> /hurl-src/vars.env
RUN echo "ssm_host=${SSM_HOST}" >> /hurl-src/vars.env
RUN echo "ssm_port=${SSM_PORT}" >> /hurl-src/vars.env
RUN echo "ssm_member_class=${SSM_MEMBER_CLASS}" >> /hurl-src/vars.env
RUN echo "ssm_member_code=${SSM_MEMBER_CODE}" >> /hurl-src/vars.env
RUN echo "ssm_member_name=${SSM_MEMBER_NAME}" >> /hurl-src/vars.env
RUN echo "ssm_security_server_code=${SSM_SECURITY_SERVER_CODE}" >> /hurl-src/vars.env
RUN echo "ssm_admin_user=${SSM_ADMIN_USER}" >> /hurl-src/vars.env
RUN echo "ssm_admin_user_password=${SSM_ADMIN_USER_PASSWORD}" >> /hurl-src/vars.env
RUN echo "ssm_token_pin=${SSM_TOKEN_PIN}" >> /hurl-src/vars.env