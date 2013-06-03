cd ~/autobuild/releases
echo 'cleaning up releases...'
rm -force -recurse r*
echo 'cleaning up builds...'
cd ../builds
rm -force -recurse build.* 
cd ../installs
echo 'cleaning up installs...'
rm -force -recurse install.*
cd ~
echo 'setting up substitution drive'
subst x: 'c:\\Documents and Settings\\buildaccount\\Local Settings\\Temp'
echo 'changing to substitution drive'
x:
echo 'cleaning up testit_dir...'
rm -force -recurse testit_dir.*
echo 'cleaning up testoutput...'
rm -force -recurse testoutput.*
echo 'cleaning up build_source...'
rm -force -recurse build_source.*
echo 'cleaning up install_copy...'
rm -force -recurse install_copy.*
echo 'cleaning up release_testing...'
rm -force -recurse release_testing.*
c:
# subst /d x:
echo 'done' 

