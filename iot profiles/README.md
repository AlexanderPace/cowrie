Each profile has the `honeyfs` folder which has files usually contained in the `etc` and `proc` folders. These files, and the other configuration files provided, have been fine-tuned to appear as different IoT devices.  
Simply replace the `honeyfs` folder with the one from the profile you choose before starting Cowrie. Also replace `share/cowrie/cmdoutput.json`, `share/cowrie/fs.pickle`, `share/cowrie/txtcmds/usr/bin/lscpu` and `etc/userdb.txt` with the same files provided in the profile folder.  
You must also change the honeypot>hostname field in the config file to the one specified in `honeyfs/etc/hostname`.  
You must also change the shell>arch and shell>kernel_version/kernel_build_string/hardware_platform/operating_system config fields to match the contents of `honeyfs/proc/version`.  
You must also change the ssh>version field to match the version in `honeyfs/proc/version`
