FROM centos:latest
LABEL maintainer "Frédéric Haziza, NBIS"

CMD mkdir -p /etc/ega
COPY ega.conf /etc/ega/conf.ini

RUN yum -y update && \
    yum -y install gcc git curl make bzip2 unzip \
    	   	   openssl \
		   nss-tools nc nmap tcpdump lsof strace \
	       	   bash-completion bash-completion-extras

RUN [[ -e /lib64/libpython3.6m.so ]] || ln -s /lib64/libpython3.6m.so.1.0 /lib64/libpython3.6m.so

##################################
# For Python 3.6
##################################

RUN yum -y install https://centos7.iuscommunity.org/ius-release.rpm
RUN yum -y install gcc python36u python36u-pip

# And some extra ones, to speed up booting the VMs
RUN pip3.6 install --upgrade pip && \
    pip3.6 install PyYaml Markdown pika==0.10.0 aiohttp==2.2.5 pycryptodomex==3.4.5 aiopg==0.13.0 colorama==0.3.7 aiohttp-jinja2==0.13.0

