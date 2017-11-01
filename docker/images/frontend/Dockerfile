FROM tornroos/ega:common3

COPY frontend.sh /usr/local/bin/frontend.sh

RUN git clone --depth 1 https://github.com/NBISweden/LocalEGA.git /root/ega
RUN pip3.6 install /root/ega/src

CMD ega-frontend 
