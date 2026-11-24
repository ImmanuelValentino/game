FROM php:7.2-apache

RUN a2enmod headers rewrite

WORKDIR /var/www/html
COPY . /var/www/html/

RUN mkdir -p /var/www/html/saves \
    && chown -R www-data:www-data /var/www/html/saves \
    && chmod 755 /var/www/html/saves

EXPOSE 10000

CMD ["/bin/sh", "-c", "PORT=${PORT:-10000}; printf 'Listen %s\\n' \"$PORT\" > /etc/apache2/ports.conf && printf '<VirtualHost *:%s>\\n    DocumentRoot /var/www/html\\n    <Directory /var/www/html>\\n        Options -Indexes +FollowSymLinks\\n        AllowOverride All\\n        Require all granted\\n    </Directory>\\n    ErrorLog ${APACHE_LOG_DIR}/error.log\\n    CustomLog ${APACHE_LOG_DIR}/access.log combined\\n</VirtualHost>\\n' \"$PORT\" > /etc/apache2/sites-available/000-default.conf && exec apache2-foreground"]
