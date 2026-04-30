# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

FROM php:8.2-apache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libzip-dev \
    libicu-dev \
    libpng-dev \
    libjpeg-dev \
    libfreetype6-dev \
    libonig-dev \
    libxml2-dev \
    libmagickwand-dev \
    libgmp-dev \
    libbz2-dev \
    libldap2-dev \
    libsmbclient-dev \
    libcurl4-openssl-dev \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Configure and install PHP extensions
RUN docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-configure ldap --with-libdir=lib/x86_64-linux-gnu/ \
        && docker-php-ext-install -j$(nproc) \
        zip \
        intl \
        gd \
        mbstring \
        xml \
        curl \
        fileinfo \
        bz2 \
        gmp \
        bcmath \
        exif \
        ldap \
        opcache

# Install ImageMagick PHP extension
RUN pecl install imagick \
    && docker-php-ext-enable imagick

# Install APCu
RUN pecl install apcu \
    && docker-php-ext-enable apcu

# Configure PHP
RUN { \
    echo 'opcache.enable=1'; \
    echo 'opcache.interned_strings_buffer=32'; \
    echo 'opcache.max_accelerated_files=10000'; \
    echo 'opcache.memory_consumption=128'; \
    echo 'opcache.save_comments=1'; \
    echo 'opcache.revalidate_freq=1'; \
} > /usr/local/etc/php/conf.d/opcache-recommended.ini

RUN { \
    echo 'apc.enable_cli=1'; \
    } > /usr/local/etc/php/conf.d/docker-php-ext-apcu.ini

RUN { \
    echo 'memory_limit=512M'; \
    echo 'upload_max_filesize=512M'; \
    echo 'post_max_size=512M'; \
    echo 'max_execution_time=300'; \
    echo 'max_input_time=300'; \
} > /usr/local/etc/php/conf.d/nextcloud.ini

# Enable Apache modules
RUN a2enmod rewrite headers env dir mime setenvif ssl

# Configure Apache for NextCloud
RUN { \
    echo '<VirtualHost *:80>'; \
    echo '    DocumentRoot /var/www/html'; \
    echo '    ServerName localhost'; \
    echo '    <Directory /var/www/html>'; \
    echo '        Require all granted'; \
    echo '        AllowOverride All'; \
    echo '        Options FollowSymLinks MultiViews'; \
    echo '        <IfModule mod_dav.c>'; \
    echo '            Dav off'; \
    echo '        </IfModule>'; \
    echo '    </Directory>'; \
    echo '</VirtualHost>'; \
} > /etc/apache2/sites-available/000-default.conf

# Set working directory
WORKDIR /var/www/html

# Download and extract Nextcloud
ARG NEXTCLOUD_VERSION=31.0.5
RUN curl -fsSL -o nextcloud.tar.bz2 "https://download.nextcloud.com/server/releases/nextcloud-${NEXTCLOUD_VERSION}.tar.bz2" \
    && tar -xjf nextcloud.tar.bz2 --strip-components=1 \
    && rm nextcloud.tar.bz2

# Set proper permissions
RUN chown -R www-data:www-data /var/www/html \
    && find /var/www/html -type d -exec chmod 755 {} \; \
    && find /var/www/html -type f -exec chmod 644 {} \;

# Create data directory
RUN mkdir -p /var/www/html/data \
    && chown -R www-data:www-data /var/www/html/data \
    && chmod 750 /var/www/html/data

USER www-data
RUN mkdir -p /var/www/html/config

# Install Nextcloud
RUN php occ maintenance:install \
    --database="sqlite" \
    --database-name="nextcloud" \
    --admin-user="admin" \
    --admin-pass="admin123" \
    --data-dir="/var/www/html/data" \
    --no-interaction

# Configure Nextcloud
RUN php occ config:system:set trusted_domains 0 --value="localhost" \
    && php occ config:system:set trusted_domains 1 --value="127.0.0.1" \
    && php occ config:system:set trusted_domains 2 --value="*" \
    && php occ config:system:set overwrite.cli.url --value="http://localhost" \
    && php occ config:system:set htaccess.RewriteBase --value="/" \
    && php occ config:system:set ratelimit.protection.enabled --value=false --type=boolean \
    && php occ config:system:set auth.bruteforce.protection.enabled --value=false --type=boolean \
    && php occ maintenance:update:htaccess
# Enable debugging
RUN php occ config:system:set debug --value=true --type=boolean \
    && php occ config:system:set loglevel --value=2 --type=integer

# Disable some background jobs that aren't needed for testing
RUN php occ config:app:set core backgroundjobs_mode --value="cron" \
    && php occ background:cron

# Disable password policy so we can use password "test".
# DO. NOT. DO. THIS.
RUN php occ app:disable password_policy

RUN php occ app:install calendar \
    && php occ app:install contacts \
    && php occ app:install tasks

# Setup users for testing
RUN OC_PASS=testtest php occ user:add --password-from-env --display-name="Test User" test \
    && php occ dav:create-addressbook test "Default Address Book" \
    && php occ dav:create-calendar test "Default Calendar"


# Final permission check
USER root
RUN chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html \
    && chmod -R 644 /var/www/html/config/config.php

# Create entrypoint script
RUN { \
    echo '#!/bin/bash'; \
    echo 'set -e'; \
    echo ''; \
    echo 'echo "Starting Nextcloud..."'; \
    echo 'exec apache2-foreground'; \
} > /entrypoint.sh \
    && chmod +x /entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
