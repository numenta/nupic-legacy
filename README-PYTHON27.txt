WHAT 
I would like to refactor existing codebase to python2 (2.7). That means replacing all #!/usr/bin/env python -> #!/usr/bin/env python2 lines. 
And usages of plain "python" with python2 too.  

WHY
My distribution (archlinux) currently provides python3 as default python interpreter. Sooner or later other distros will follow, so this step is eventually needed. Of course I could use some python-config, or switch symlink, but this way other things break.. 

PROS/CONS
+ : helps users with both pythons (2,3). doesnt affect users on py2 already. 

TODO
1/ verify python2 always exist. I almost certainly know it does everywhere, if it doesnt on your system, please shout! 

2/ as described, find and edit all #!/usr/bin/env python and plain python lines and replace with python2 reference. 

2.2/ verify if python2.7 also runs. It should - minimal changes. 
http://docs.python.org/dev/whatsnew/2.7.html#porting-to-python-2-7

3/ test and enjoy :) 

WHERE 
I'll try the change in port-to-python27 branch in my repo: 
https://github.com/breznak/nupic/tree/port-to-python27 
If you want, please help and test there. 

Please let me know if you want to help or have any ideas/opinions! 
Cheers, breznak

