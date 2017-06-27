WP Deploy
=========

A simple python script to deploy changes to Wordpress installations on (most) linux environments.

Features
--------

* Grabs Codebase and database backups before deploying changes.
* Run database updates after code changes from repository have been retrieved.
* Aborts process at different stages if one of the steps fails (e.g: unable to backup database).
* Rolls back to the previous version of the code and database if the database update fails.
* Restart services (apache) deployment has been successful.
* Keeps the backups taken before the last deployment.

Installation
------------

Place script in any desired directory, on the server where the deployments will happen.
Suggestion is to use the home directory of the user that will execute the script.

Setup
-----

The user that executes the script will need *sudo* access on the system. If you're not running
the script manually, and it's run from something like Jenkins, you may want to grant
*passwordless sudo* access to the following commands, in a file under /etc/sudoers.d:

``/usr/bin/mysqldump, /usr/bin/mysql, /etc/init.d/apache2, /bin/chown, /bin/rm``

I don't need to tell you to harden the SSH access to your server properly, if you plan to allow
such *passwordless access* to the sudo command. The above is just a possible way of doing it, not 
the standard one.

If you're running the script manually, it'll be enough with entering your sudo password upon
request.
 
Note the script will put the **uploads** directory and the **wp-config.php** file out of the docroot,
and create symlinks to them in the relevant places of the codebase. You'll need a directory where those
linked files and directories will be kept (e.g: /var/www/symlinks, or /var/www/shared).

Also, the script expects **both** the code repository and the live site to be in different directories, and
both of them under the same directory. For example:

`/var/www`

`/var/www/my-wp-repo`

`/var/www/my-wp-live-site`

Usage
-----

Once the setup has been sorted, simply execute the script with the right arguments to deploy changes to the site.

Run it with the `-h` flag to show what each argument is for:
 
 `python wp_deploy.py -h`


Arguments
---------

The arguments expected by the script, in order:


| Argument     	| Description                                                            	|
|--------------	|------------------------------------------------------------------------	|
| project_name 	| Directory of the git repository of the project (Under,"codebase_dir"). 	|
| host_user    	| User running the script in the host.                                   	|
| db_name      	| Name of the wordpress database.                                        	|
| codebase_dir 	| Directory where the "live_dir" and "project_name" dir are located.     	|
| live_dir     	| LIVE directory of the project (Under "codebase_dir").                  	|
| symlinks_dir 	| Directory where wp-config.php and uploads folder will live.            	|
  
  
So what the script expects is:

``python wp_deploy.py [project_name] [host_user] [db_name] [codebase_dir] [live_dir] [symlinks_dir]``

Example call:

``python wp_deploy.py mrfaulty_blog basil mrfaulty_blog_db /var/www mrfaulty_blog_live /var/www/shared``

License
-------

This project has no License, at least yet. Do with it whatever you please.

Author
------

Salva Molina (salvamomo) - @Salva_bg.
