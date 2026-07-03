FROM odoo:18.0

USER root

RUN mkdir -p /mnt/extra-addons
RUN mkdir -p /mnt/enterprise
# Copy custom modules into image
COPY ./cats4u /mnt/extra-addons
COPY ./src/odoo_18_e /mnt/enterprise

USER odoo

EXPOSE 8069

