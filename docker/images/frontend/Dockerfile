FROM tornroos/ega:common

COPY frontend.sh /usr/local/bin/frontend.sh

RUN git clone --depth 1 https://github.com/NBISweden/LocalEGA.git /root/ega
RUN /usr/local/bin/frontend.sh

ENTRYPOINT ["ega-frontend"]

