FROM centos:latest
LABEL maintainer "Frédéric Haziza, NBIS"

RUN yum install -y epel-release && \
    yum -y update && \
    yum -y install gcc git make rsyslog \
		   openssh-server \
		   nss-tools nc nmap tcpdump lsof strace \
	       	   bash-completion bash-completion-extras \
		   postgresql-devel pam-devel libcurl-devel jq-devel ed

##################################
RUN mkdir -p /usr/local/lib/ega
COPY ega.ld.conf /etc/ld.so.conf.d/ega.conf

##################################
RUN mkdir -p /var/run/sshd

# Regenerate keys (no passphrase)
#RUN ssh-keygen -t rsa     -N '' -f /etc/ssh/ssh_host_rsa_key && \
#    ssh-keygen -t dsa     -N '' -f /etc/ssh/ssh_host_dsa_key && \
#    ssh-keygen -t ecdsa   -N '' -f /etc/ssh/ssh_host_ecdsa_key && \
#    ssh-keygen -t ed25519 -N '' -f /etc/ssh/ssh_host_ed25519_key 

##################################
COPY pam.ega /etc/pam.d/ega
RUN mv /etc/pam.d/sshd /etc/pam.d/sshd.bak
COPY pam.sshd /etc/pam.d/sshd

RUN cp /etc/nsswitch.conf /etc/nsswitch.conf.bak && \
    sed -i -e 's/^passwd:\(.*\)files/passwd:\1files ega/' /etc/nsswitch.conf

COPY banner /ega/banner
COPY sshd_config /etc/ssh/sshd_config

RUN useradd ega
RUN /usr/sbin/rsyslogd

RUN git clone https://github.com/NBISweden/LocalEGA.git /root/ega 
RUN adduser --system -s /bin/bash -u 1234321 -g 0 git # uid to replace later

COPY inbox.sh /usr/local/bin/inbox.sh

RUN /usr/local/bin/inbox.sh

RUN sed -i 's/#Port.*$/Port 2022/' /etc/ssh/sshd_config
RUN chmod 775 /var/run
RUN rm -f /var/run/nologin

# setup git user
#RUN adduser --system -s /bin/bash -u 1234321 -g 0 git # uid to replace later
RUN chmod 775 /etc/ssh /home # keep writable for openshift user group (root)
RUN chmod 660 /etc/ssh/sshd_config
RUN chmod 664 /etc/passwd /etc/group # to help uid fix

RUN chmod g+s /ega/inbox
RUN chmod +s /usr/sbin/sshd

EXPOSE 2022

USER git
# FYI sed -i uses a temporary fail which approach fails
CMD echo -e ",s/1234321/`id -u`/g\\012 w" | ed -s /etc/passwd && \
    mkdir -p /home/git/.ssh && \
    touch /home/git/.ssh/authorized_keys && \
    chmod 700 /home/git/.ssh && \
    chmod 600 /home/git/.ssh/authorized_keys && \
    ssh-keygen -A && \
    echo "Starting sshd..." && \
    exec /usr/sbin/sshd -D -e
