# SPDX-FileCopyrightText: 2026 Noham Devillers <nde@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

FROM tomsquest/docker-radicale:latest

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
RUN printf "test:{SHA}W6ph5Mm5Pz8GgiULbPgzG37mj9g=\n" > /data/users

# Fix permissions
RUN chown -R radicale:radicale /data

# Provide config
RUN mkdir -p /etc/radicale
RUN printf "\
[server]\n\
hosts = 0.0.0.0:5232\n\
\n\
[auth]\n\
type = htpasswd\n\
htpasswd_filename = /data/users\n\
htpasswd_encryption = sha1\n\
\n\
[storage]\n\
filesystem_folder = /data/collections\n\
\n\
[rights]\n\
type = owner_only\n\
" > /etc/radicale/config

USER radicale

EXPOSE 5232