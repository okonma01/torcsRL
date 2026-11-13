FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git build-essential autoconf automake libtool \
    libglib2.0-dev libgl1-mesa-dev libglu1-mesa-dev freeglut3-dev \
    libplib-dev libopenal-dev libalut-dev libxi-dev libxmu-dev \
    libxrender-dev libxrandr-dev libpng-dev libvorbis-dev libxxf86vm-dev \
    python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Pin SCR with the Tita teacher action and lookahead telemetry.
ARG TORCS_REV=6c451cb779b24dcb42f8f1a20be57dd1d47a8f91
COPY docker/torcs-gui.patch /tmp/torcs-gui.patch
RUN git init /opt/torcs-src && cd /opt/torcs-src \
    && git remote add origin https://github.com/raphaelsenn/torcs-1.3.7 \
    && git fetch --depth 1 origin "$TORCS_REV" && git checkout --detach FETCH_HEAD \
    && git apply /tmp/torcs-gui.patch \
    # Upstream includes machine-specific dependencies and omits this helper.
    && find . -name .depend -delete \
    && cp /usr/share/automake-*/compile . \
    # Dependency generation needs local paths for the shared Tita sources.
    && for source in berniw.h mycar.cpp mycar.h pathfinder.cpp pathfinder.h spline.cpp spline.h trackdesc.cpp trackdesc.h; do \
        ln -s "../tita/$source" "src/drivers/scr_server/$source"; \
    done \
    && CFLAGS=-fPIC CPPFLAGS=-fPIC CXXFLAGS=-fPIC ./configure --prefix=/usr/local \
    && make -j1 && make install && make datainstall \
    && test -x /usr/local/lib/torcs/torcs-bin \
    && test -f /usr/local/lib/torcs/drivers/scr_server/scr_server.so \
    && rm -rf /opt/torcs-src

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV TORCSRL_DIRECT_GUI=1
WORKDIR /workspace
COPY requirements.txt setup.py ./
RUN pip install --no-cache-dir torch==2.11.0 --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir setuptools -r requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb x11vnc novnc websockify openbox xdotool x11-utils mesa-utils \
    && rm -rf /var/lib/apt/lists/*
COPY gym_torcs ./gym_torcs
COPY torcsrl ./torcsrl
COPY scripts ./scripts
RUN pip install --no-cache-dir --no-deps --no-build-isolation -e .
CMD ["python", "-m", "scripts.smoke_test", "--steps", "100"]
