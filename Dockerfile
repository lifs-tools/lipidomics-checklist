FROM wordpress

# Install python3, urllib, sqlite3 and texlive without documentation
RUN apt-get update; \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-urllib3 \
    python3-openpyxl \
    python3-et-xmlfile \
    sqlite3 \
    texlive \
    texlive-fonts-recommended \
    texlive-latex-extra \
    texlive-fonts-extra \
    texlive-luatex \
    ; \
    rm -rf /var/lib/apt/lists/* 

RUN mkdir /var/www/html/lipidomics-checklist && chown www-data:www-data /var/www/html/lipidomics-checklist
RUN chown -R www-data:www-data /var/www/html/lipidomics-checklist
