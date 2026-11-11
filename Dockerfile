FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git build-essential autoconf automake libtool \
    libglib2.0-dev libgl1-mesa-dev libglu1-mesa-dev freeglut3-dev \
    libplib-dev libopenal-dev libalut-dev libxi-dev libxmu-dev \
    libxrender-dev libxrandr-dev libpng-dev libvorbis-dev libxxf86vm-dev \
    python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Pin the SCR-patched simulator; stock distro TORCS lacks this protocol.
ARG TORCS_REV=8134c27be99bc2039f51fd821129e1ddf7514f64
COPY docker/torcs-gui.patch /tmp/torcs-gui.patch
RUN git clone https://github.com/raphaelsenn/torcs-1.3.7 /opt/torcs-src \
    && cd /opt/torcs-src && git checkout "$TORCS_REV" \
    && git apply /tmp/torcs-gui.patch \
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
