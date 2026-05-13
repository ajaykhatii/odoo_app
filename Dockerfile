FROM odoo:18

# Copy addons
COPY ./cats4u /mnt/extra-addons
COPY ./src/odoo_18_e /mnt/enterprise

# Switch to root for package installations
USER root

# Upgrade pip
# RUN pip install --no-cache-dir --upgrade pip --break-system-packages

# Install Python dependencies
RUN pip install --break-system-packages phonenumbers
   

# Copy config
COPY ./config/odoo.conf /etc/odoo/odoo.conf

# Fix permissions
RUN chmod -R 777 /mnt/extra-addons/ && \
    chmod -R 777 /mnt/enterprise/

# Switch back to Odoo user
USER odoo

EXPOSE 8069 8071


#This is for custom plugins