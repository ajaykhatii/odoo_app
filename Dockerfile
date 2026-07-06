FROM odoo:18.0

USER root

RUN mkdir -p /mnt/extra-addons /mnt/enterprise
COPY ./cats4u /mnt/extra-addons
COPY ./src/odoo_18_e /mnt/enterprise
RUN chown -R odoo:odoo /mnt/extra-addons /mnt/enterprise

USER odoo

EXPOSE 8069