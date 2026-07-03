# SPDX-FileCopyrightText: 2026 Noham Devillers <nde@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

FROM ghcr.io/kozea/radicale:3.7

USER root

# Create data directory
RUN mkdir -p /data/collections/collection-root/test

# Create calendar
RUN mkdir -p /data/collections/collection-root/test/calendar \
    && echo '{"tag": "VCALENDAR", "D:displayname": "Default Calendar"}' > /data/collections/collection-root/test/calendar/.Radicale.props \
    && touch /data/collections/collection-root/test/calendar/calendar.ics

# Create addressbook
RUN mkdir -p /data/collections/collection-root/test/addressbook \
    && echo '{"tag": "VADDRESSBOOK", "D:displayname": "Default Address Book"}' > /data/collections/collection-root/test/addressbook/.Radicale.props \
    && touch /data/collections/collection-root/test/addressbook/addressbook.vcf

# Create users file (htpasswd format)
RUN printf "test:testtest\n" > /data/users

# Fix permissions
RUN chown -R radicale:radicale /data

# Create config directory
RUN mkdir -p /etc/radicale

# Provide config
RUN printf "\
[server]\n\
hosts = 0.0.0.0:5232\n\
\n\
[auth]\n\
type = htpasswd\n\
htpasswd_filename = /data/users\n\
htpasswd_encryption = plain\n\
\n\
[storage]\n\
filesystem_folder = /data/collections\n\
\n\
[rights]\n\
type = owner_only\n\
" > /etc/radicale/config

USER radicale

EXPOSE 5232
