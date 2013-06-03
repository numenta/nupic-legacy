function Remove-3-Days-Old-Files($mask)
{
  ls $mask |? {$_.PsIsContainer} |? {$_.LastWriteTime -lt (get-date).AddDays(-3)} | rm -recurse
}

echo 'cleaning up releases...'
Remove-3-Days-Old-Files('~/autobuild/releases/r*')
echo 'cleaning up builds...'
Remove-3-Days-Old-Files('~/autobuild/builds/build.*')
echo 'cleaning up installs...'
Remove-3-Days-Old-Files('~/autobuild/installs/install.*')
echo 'setting up substitution drive'
subst x: 'c:/Documents and Settings/buildaccount/Local Settings/Temp'
echo 'cleaning up testit_dir...'
Remove-3-Days-Old-Files('x:/testit_dir.*')
rm -force -recurse testit_dir.*
echo 'cleaning up testoutput...'
Remove-3-Days-Old-Files('x:/testoutput.*')
echo 'cleaning up build_source...'
Remove-3-Days-Old-Files('x:/build_source.*')
echo 'cleaning up install_copy...'
Remove-3-Days-Old-Files('x:/install_copy.*')
echo 'cleaning up release_testing...'
Remove-3-Days-Old-Files('x:/release_testing.*')

echo 'done' 

