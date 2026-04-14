# SPDX-FileCopyrightText: 2026 Noham Devillers <nde@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

FROM debian:trixie-slim

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y \
        cyrus-imapd \
        cyrus-admin \
        libcyrus-imap-perl \
        libsasl2-modules \
        sasl2-bin \
        rsyslog \
    && apt-get clean

RUN mkdir -p \
        /srv/cyrus/conf \
        /srv/cyrus/run \
        /srv/cyrus/var/spool/mail \
        /srv/cyrus/var/spool/sieve \
    && chown -R cyrus:mail /srv/cyrus

COPY imapd.conf /srv/cyrus/imapd.conf
COPY cyrus.conf /etc/cyrus.conf

RUN mkdir -p /etc/sasl2 && \
    echo "pwcheck_method: alwaystrue" > /etc/sasl2/imapd.conf && \
    echo "mech_list: PLAIN LOGIN" >> /etc/sasl2/imapd.conf

EXPOSE 143

CMD ["/usr/lib/cyrus/bin/master", "-C", "/srv/cyrus/imapd.conf", "-M", "/etc/cyrus.conf", "-D"]
