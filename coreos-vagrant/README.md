Bring up vm image with vagrant, convert vm image to vdi and resize, replacing
<VM> below with the value that applies to your own environment:

  vagrant up
  vagrant halt
  cd ~/VirtualBox\ VMs/<VM>/
  VBoxManage clonehd coreos_production_vagrant_image.vmdk clone-coreos_production_vagrant_image.vdi --format vdi
  VBoxManage modifyhd clone-coreos_production_vagrant_image.vdi --resize 1048576
  VBoxManage showvminfo <VM> | grep Storage
  VBoxManage storageattach <VM> --storagectl "IDE Controller" --port 0 --device 0 --type hdd --medium clone-coreos_production_vagrant_image.vdi
  cd -
  vagrant up --provision
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
