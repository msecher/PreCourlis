ARG QGIS_TAG=release-3_16
FROM qgis/qgis:${QGIS_TAG} as test

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt update \
    && apt remove -y python3-coverage \
    && DEBIAN_FRONTEND=noninteractive apt install -y \
        git \
        grass \
        make \
        pyqt5-dev-tools \
        python3-venv \
        qttools5-dev-tools \
        vim \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache \
    pip3 install \
        black==22.8.0 \
        coverage \
        debugpy \
        flake8 \
        matplotlib==3.1.3 \
        nose \
        numpy==1.18.3 \
        psycopg2-binary \
        pydevd \
        pytest \
        pytest-cov \
        pyyaml \
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

ARG EXPECTED_PATH
ENV EXPECTED_PATH=$EXPECTED_PATH

CMD ["pytest"]
