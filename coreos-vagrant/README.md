
Bring up vm image with vagrant and log in:

    vagrant up
    vagrant ssh

Once logged in, cd into ~/nupic and build the docker container:

    cd nupic
    docker build .

In the end you will see something like:

    Step 23 : WORKDIR /home/docker
     ---> Running in 4bf37dbaeb13
     ---> <container id>
    Removing intermediate container 4bf37dbaeb13
    Successfully built <container id>

Then, launch the docker container, replacing the id with your own:

    docker run -t -i <container id> /bin/bash

Then, cd into /usr/local/src/nupic and run tests"

    cd /usr/local/src/nupic
    ./run_tests.sh -u
    bin/testpyhtm
