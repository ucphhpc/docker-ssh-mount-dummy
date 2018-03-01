FROM debian:latest
MAINTAINER Rasmus Munk <rasmus.munk@nbi.ku.dk>

RUN apt-get update \
    && apt-get install -yq --no-install-recommends \
    openssh-server \
    python3-dev \
    python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


#RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd \
    && mkdir -p /run/sshd

COPY main.py /app/main.py
COPY requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install setuptools wheel
RUN pip3 install -r requirements.txt \
    && python3 main.py

# Setup key
RUN echo -e "\n" | ssh-keygen -t rsa -N ""

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]