# Vagrant + CoreOS + Docker

The included `Vagrantfile` and configuration files are provided to support a
docker-based workflow on top of [CoreOS](https://coreos.com/) and
[Vagrant](https://www.vagrantup.com/), in which nupic may be built in an
isolated, and replicable Linux environment.  CoreOS, the guest OS in the
virtual machine (VM) in this example, is a minimal linux distribution that
works particularly well with [Docker](https://www.docker.com/), a platform for
automating and running isolated linux containers.  Vagrant provides a
high-level interface for provisioning and launching VMs

Before you begin, install Vagrant from
https://www.vagrantup.com/downloads.html, clone this repository from
https://github.com/numenta/nupic, and cd into
`nupic/coreos-vagrant`.

Bring up vm with vagrant and log in:

    vagrant up
    vagrant ssh

Once logged in, cd into `~/nupic` and build the docker container:

    cd nupic
    docker build -t nupic:`git rev-parse HEAD` .

In the end you will see something like:

    Step 23 : WORKDIR /home/docker
     ---> Running in 4bf37dbaeb13
     ---> <container id>
    Removing intermediate container 4bf37dbaeb13
    Successfully built <container id>

Then, launch the docker container, replacing the id with your own:

    docker run -t -i nupic:`git rev-parse HEAD` /bin/bash

Then, cd into /usr/local/src/nupic and run tests:

    cd /usr/local/src/nupic
    bin/py_region_test
    scripts/run_nupic_tests -u --coverage

