FROM debian:bookworm

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y dovecot-imapd dovecot-pop3d && \
    apt-get clean

# Mail storage
RUN mkdir -p /mail && \
    groupadd -g 1000 vmail && \
    useradd -u 1000 -g vmail -d /mail -m vmail && \
    chmod 777 /mail

COPY dovecot.conf /etc/dovecot/dovecot.conf

EXPOSE 143

CMD ["dovecot", "-F"]