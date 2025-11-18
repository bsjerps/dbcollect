**Ansible Playbook to run dbcollect**

The Ansible playbook dbcollect.yml runs https://github.com/bsjerps/dbcollect on
a couple of hosts and copies the resulting zip files over to the local system.
By default the zip files are stored in the local subdirectory collects/ which is
removed during every run of the playbook. Please make sure to rename an existing
directory before you run the playbook or you will loose any existing zip files.

As dbcollect can take quite some time there is a proof of concept script called
testcollect you can use for dry runs of the playbook. Further you can control
some of the behavior of the playbook by redefining its vars on the command line.

Usage: ansible-playbook -i hosts dbcollect.yml [-e "var=value ..."]

The vars of the playbook are the following:

ansible_python_interpreter	The path to python on the target host.
				The default of auto_silent is usually fine for
				most systems.

collect_path			The path to the directory where the zip files are
				stored. The default is ./collects

dbcollect			The name of the command which is run on the target
				hosts. Defaults to dbcollect, can be replaced by
				testcollect for dry runs.

downloader			The path and filename of the downloader which is
				used to download the latest version of dbcollect.
				Please check "./download.py"

http_proxy			Define the proxy to use for downloads. Defaults
				to "" for no proxy required.

For details about the downloading mechanism of dbcollect please see
https://github.com/bsjerps/dbcollect/blob/master/INSTRUCTIONS.md
Hint: the playbook implements the **Easy way**

The playbook defaults to run on all hosts defined in the file `hosts`. As the
example file shows you can also work with groups in order to target only a
specific set of hosts.
