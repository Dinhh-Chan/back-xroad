FROM ubuntu:24.04

# ACME
ADD acme2certifier_0.35-1_all.deb /tmp/

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -qq update \
    && apt-get -qq install --no-install-recommends  \
    python3 nginx supervisor bash openssl curl python3-pip uwsgi uwsgi-plugin-python3 \
    && apt -y install --no-install-recommends /tmp/acme2certifier_0.35-1_all.deb \
    && apt-get -qq clean \
    #Setup CA with TSA and OCSP
    && useradd -m ca -U \
    && useradd -G ca ocsp

COPY home /home
COPY etc /etc
COPY usr /usr

COPY files/init.sh /home/ca/CA/
COPY files/ca.py /home/ca/CA/

RUN chown -R ca:ca /home/ca/CA \
    && find /home/ca/TSA -type f -exec chmod 0664 {} + \
    && find /home/ca/CA -type f -exec chmod 0740 {} + \
    && chmod 0700 /home/ca/CA/init.sh \
    && mkdir -p /var/log/ \
    && touch /var/log/ocsp.log \
    && chown ca:ca /var/log/ocsp.log \
    && chmod 0664 /var/log/ocsp.log \
    && chmod 0754 /home/ca/CA/ca.py \
    && chmod 0754 /home/ca/CA/sign_req.sh

COPY files/ca-entrypoint.sh /root/entrypoint.sh
COPY --chown=root:root files/ca.conf /etc/supervisor/conf.d/ca.conf

RUN sed -i "s/run\/uwsgi\/acme.sock/var\/www\/acme2certifier\/acme.sock/g" /var/www/acme2certifier/examples/nginx/nginx_acme_srv.conf \
    && sed -i "s/80/8887/g" /var/www/acme2certifier/examples/nginx/nginx_acme_srv.conf \
    && cp /var/www/acme2certifier/examples/nginx/nginx_acme_srv.conf /etc/nginx/sites-available/acme_srv.conf \
    && ln -s /etc/nginx/sites-available/acme_srv.conf /etc/nginx/sites-enabled/acme_srv.conf \
    && sed -i "s/\/run\/uwsgi\/acme.sock/acme.sock/g" /var/www/acme2certifier/examples/nginx/acme2certifier.ini \
    && sed -i "s/nginx/www-data/g" /var/www/acme2certifier/examples/nginx/acme2certifier.ini \
    && echo "plugins = python3" >> /var/www/acme2certifier/examples/nginx/acme2certifier.ini \
    && cp /var/www/acme2certifier/examples/nginx/acme2certifier.ini /var/www/acme2certifier \
    && usermod -a -G ca www-data
COPY --chown=www-data:www-data acme2certifier/acme_srv.cfg /var/www/acme2certifier/acme_srv/acme_srv.cfg
COPY --chown=www-data:www-data acme2certifier/kid_profiles.json /var/www/acme2certifier/examples/eab_handler/kid_profiles.json
COPY --chown=www-data:www-data acme2certifier/openssl_ca_handler.py /var/www/acme2certifier/examples/ca_handler/openssl_ca_handler.py

CMD ["/root/entrypoint.sh"]

EXPOSE 8888 8899