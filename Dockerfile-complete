FROM numenta/nupic

MAINTAINER Allan Costa <allaninocencio@yahoo.com.br>

# Install MySQL. It's the only extra dependency for NuPIC swarm.
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y mysql-server

# Create a startup.sh bash script to start mysql before running any command
RUN echo "#!/bin/bash\nservice mysql start\nexec \$*" >> /home/docker/startup.sh && \
    chmod +x /home/docker/startup.sh

# Test the swarm connection to MySQL
RUN /home/docker/startup.sh python $NUPIC/examples/swarm/test_db.py

ENTRYPOINT ["/home/docker/startup.sh"]
