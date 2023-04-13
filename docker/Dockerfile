FROM qgis/qgis:release-3_10 as test

RUN apt update \
     && apt remove -y python3-coverage \
     && apt install -y \
        python3-venv \
        vim

RUN pip3 install \
    black==22.8.0 \
    coverage \
    flake8 \
    matplotlib==3.1.3 \
    nose \
    numpy==1.18.3 \
    pydevd \
    pytest \
    pytest-cov \
    scipy==1.4.1

RUN mkdir -p /app /home/user && chmod 777 /home/user

# Keep QGIS settings in a volume
RUN mkdir -p /home/user/.local/share/QGIS/QGIS3/profiles/default \
    && chmod -R 777 /home/user/.local
VOLUME /home/user/.local/share/QGIS/QGIS3/profiles/default

WORKDIR /app

ENV DISPLAY=:99 \
    HOME=/home/user

RUN mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix
COPY /docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]

CMD ["pytest"]
