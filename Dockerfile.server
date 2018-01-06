FROM debian:stretch

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -yq \
   python python-pyside.qtgui python-pyside.qtxml x11vnc xvfb fluxbox && \
   apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir -p ~/.vnc && x11vnc -storepasswd secret ~/.vnc/passwd

ENV PORT=7079
EXPOSE 7079
EXPOSE 5900

COPY game/*.py /usr/src/app/
COPY game/server-entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD [ "python", "server.py" ]
