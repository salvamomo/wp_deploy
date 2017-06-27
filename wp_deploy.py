import os
import subprocess
import argparse


def show_arguments():
    print "===> Executing deployment with the following variables:"
    global host_user, db_name, codebase_dir, live_dir, symlinks_dir

    print "\n     [+] PROJECT_NAME: %s" % project_name
    print "     [+] HOST_USER: %s" % host_user
    print "     [+] DB_NAME: %s" % db_name
    print "     [+] CODEBASE_DIR: %s" % codebase_dir
    print "     [+] LIVE_DIR: %s" % live_dir
    print "     [+] SYMLINKS_DIR: %s" % symlinks_dir


def database_backup():
    print "===> Grabbing database dump."
    if subprocess.call(["mkdir", "-p", "/home/" + host_user + "/dbbackups"], shell=False) == 0:
        print "DB Backups directory is in place. Continue..."
    else:
        print "DB Backups directory could not be found. Aborting..."

    # todo Compress this, too.
    dbdump_success = subprocess.call(
        ["sudo", "mysqldump", "--defaults-file=/etc/mysql/debian.cnf", db_name, "--result-file=/home/" + host_user + "/dbbackups/" + db_name + ".sql"])

    if dbdump_success == 0:
        print "Backup stored successfully."
    else:
        raise SystemExit("Could not take database backup prior to launching new build! Aborting early.")


def codebase_backup():
    print "===> Backing up codebase."

    if subprocess.call(["mkdir", "-p", "/home/" + host_user + "/codebasebackups"], shell=False) == 0:
        print "Codebase backups directory is in place. Continue..."
    else:
        print "Codebase backups directory could not be found. Aborting..."

    os.chdir(codebase_dir)
    codebase_compress_success = subprocess.call(["tar", "-cjf", live_dir + ".tbz2", live_dir])

    subprocess.call(["mv", live_dir + ".tbz2", "/home/" + host_user + "/codebasebackups"])
    codebase_moved = os.path.isfile("/home/" + host_user + "/codebasebackups/" + live_dir + ".tbz2")

    if codebase_compress_success == 0 and codebase_moved is True:
        print "Codebase backed up successfully."
    else:
        raise SystemExit("Could not take a copy of the codebase prior to launching new build! Aborting deployment.")


def codebase_update():
    print "===> Updating codebase."
    os.chdir(codebase_dir + '/' + project_name)
    git_pull_result = subprocess.call(["git", "pull"])

    if git_pull_result == 0:
        print "Codebase updated from git successfully."
        os.chdir(codebase_dir)

        subprocess.call(["sudo", "rm", "-R", live_dir])

        codebase_move = subprocess.call(["cp", "-R", codebase_dir + '/' + project_name, './' + live_dir])
        if codebase_move == 0:
            print "Codebase successfully moved to live folder."
            ensure_symlinks()

            # Ensure live dir ownership.
            os.chdir(codebase_dir)
            subprocess.call(["sudo", "chown", "-R", "www-data:www-data", live_dir])
        else:
            print "[+] Codebase could not be updated. Rolling back to previous version of code."
            rollback_codebase()
            raise SystemExit("Could not move codebase to Live folder. Code reverted. Site remains in previous build.")
    else:
        raise SystemExit("Could not pull latest changes from repository. Aborting deployment.")


def database_update():
    print "===> Updating database."
    os.chdir(codebase_dir + "/" + live_dir + "/www")

    if subprocess.call(['wp', 'core', 'update-db']) == 0:
        print "[+] Database successfully updated."

        # todo: Consider if the rest of these calls should be in another function.
        subprocess.call(['wp', 'cache', 'flush'])

        # wp core is-installed. (Doesn't produce output. Communicates with return codes.
        subprocess.call(['wp', 'checksum', 'core'])
        subprocess.call(['wp', 'core', 'is-installed'])
        restart_services()
    else:
        print "[+] Database could not be updated. Rolling back to previous version of code and database."
        rollback_codebase()
        rollback_database()
        raise SystemExit("Could not update Wordpress database. Code and database reverted. Site remains in previous build.")


def rollback_database():
    print "Rolling back database."

    os.chdir("/home/" + host_user + "/dbbackups/")
    # Technically, it's safer to delete the existing DB and put the new dump for it. No real need for the blog.
    subprocess.call(["sudo", "mysql", "--defaults-file=/etc/mysql/debian.cnf", db_name, "<", db_name + ".sql"])
    print "Database rolled back."


def rollback_codebase():
    print "Rolling back codebase."

    # Uncompress backup, move to site position, and leave backup in place in case it's needed later on.
    os.chdir("/home/" + host_user + "/codebasebackups/")
    subprocess.call(["tar", "-xjf", live_dir + ".tbz2"])
    os.chdir(codebase_dir)
    subprocess.call(["sudo", "rm", "-R", live_dir])
    subprocess.call(["mv", "/home/" + host_user + "/codebasebackups/" + live_dir, "./"])
    subprocess.call(["sudo", "chown", "-R", "www-data:www-data", live_dir])

    print "Codebase rolled back."


def delete_codebase_backup():
    # todo
    print "Deleting codebase backup."


def delete_database_backup():
    # todo
    print "Deleting codebase backup."


def restart_services():
    print "===> Restarting services."
    subprocess.call(['sudo', '/etc/init.d/apache2', 'reload'])
    print "[+] Restarted apache2."


def ensure_symlinks():
    print "===> Creating symlinks for the relevant files and folders."
    os.chdir(codebase_dir + '/' + live_dir)
    # Should the linked file be named to .inc instead?.
    # Leaving file out of docroot. See https://wordpress.stackexchange.com/a/74972.
    os.symlink(symlinks_dir + '/config_live_' + project_name + '.wp-config.php', 'wp-config.php')
    print "[+] Symlink created for wp-config.php."

    os.chdir(codebase_dir + '/' + live_dir + '/www/wp-content/')
    os.symlink(symlinks_dir + '/files_live_' + project_name, 'uploads')
    print "[+] Symlink created for uploads directory under wp-content."


def main():
    print "===> Starting zero-touch deployment of master branch."

    show_arguments()

    database_backup()

    codebase_backup()

    codebase_update()

    database_update()

    # Not really doing these for the time being. Leaving the last backups in place, just in case.
    # delete_codebase_backup()
    # delete_database_backup()

parser = argparse.ArgumentParser(description='Deploy a wordpress site.')
parser.add_argument('project_name', help='Directory of the git repository of the project (Under "codebase_dir").')
parser.add_argument('host_user', help='User running the script in the host.')
parser.add_argument('db_name', help='Name of the wordpress database.')
parser.add_argument('codebase_dir', help='Directory where the "live_dir" and "project_name" dir are located.')
parser.add_argument('live_dir', help='LIVE directory of the project (Under "codebase_dir").')
parser.add_argument('symlinks_dir', help='Directory where wp-config.php and uploads folder will live.')
args = parser.parse_args()

# Hydrate global vars from args.
project_name = args.project_name
host_user = args.host_user
db_name = args.db_name
codebase_dir = args.codebase_dir
live_dir = args.live_dir
symlinks_dir = args.symlinks_dir

main()
