# base-image for python on any machine using a template variable,
# see more about dockerfile templates here:http://docs.resin.io/pages/deployment/docker-templates
FROM resin/%%RESIN_MACHINE_NAME%%-buildpack-deps

# use apt-get if you need to install dependencies,
# for instance if you need ALSA sound utils, just uncomment the lines below.
RUN apt-get update && apt-get install -yq python python-serial python-pyside.qtgui python-pyside.qtxml && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set our working directory
WORKDIR /usr/src/app

# Copy requirements.txt first for better cache on later pushes
#COPY ./requirements.txt /requirements.txt

# pip install python deps from requirements.txt on the resin.io build server
#RUN pip install -r /requirements.txt

# This will copy all files in our root to the working  directory in the container
COPY game/*.py /usr/src/app/

# switch on systemd init system in container
ENV INITSYSTEM on

# main.py will run when container starts up on the device
CMD ["python", "/usr/src/app/client.py", "-s", "/dev/ttyACM0"]

#ENTRYPOINT ["/usr/bin/qemu-arm-static", "-execve", "-0", "/bin/bash"]
