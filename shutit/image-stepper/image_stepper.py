import random
import logging
import string
import os
import inspect
from shutit_module import ShutItModule

class image_stepper(ShutItModule):


	def build(self, shutit):
		vagrant_image = shutit.cfg[self.module_id]['vagrant_image']
		vagrant_provider = shutit.cfg[self.module_id]['vagrant_provider']
		gui = shutit.cfg[self.module_id]['gui']
		memory = shutit.cfg[self.module_id]['memory']
		shutit.cfg[self.module_id]['vagrant_run_dir'] = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda:0))) + '/vagrant_run'
		run_dir = shutit.cfg[self.module_id]['vagrant_run_dir']
		module_name = 'image_stepper_' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
		shutit.send('command rm -rf ' + run_dir + '/' + module_name + ' && command mkdir -p ' + run_dir + '/' + module_name + ' && command cd ' + run_dir + '/' + module_name)
		if shutit.send_and_get_output('vagrant plugin list | grep landrush') == '':
			shutit.send('vagrant plugin install landrush')
		shutit.send('vagrant init ' + vagrant_image)
		shutit.send_file(run_dir + '/' + module_name + '/Vagrantfile','''Vagrant.configure("2") do |config|
  config.landrush.enabled = true
  config.vm.provider "virtualbox" do |vb|
    vb.gui = ''' + gui + '''
    vb.memory = "''' + memory + '''"
  end

  config.vm.define "imagestepper1" do |imagestepper1|
    imagestepper1.vm.box = ''' + '"' + vagrant_image + '"' + '''
    imagestepper1.vm.hostname = "imagestepper1.vagrant.test"
    config.vm.provider "virtualbox" do |vb|
      vb.name = "''' + module_name + '''_1"
    end
  end
end''')
		pw = shutit.get_env_pass()
		try:
			shutit.multisend('vagrant up --provider ' + shutit.cfg['shutit-library.virtualization.virtualization.virtualization']['virt_method'] + " imagestepper1",{'assword for':pw,'assword:':pw},timeout=99999)
		except NameError:
			shutit.multisend('vagrant up imagestepper1',{'assword for':pw,'assword:':pw},timeout=99999)
		if shutit.send_and_get_output("""vagrant status | grep -w ^imagestepper1 | awk '{print $2}'""") != 'running':
			shutit.pause_point("machine: imagestepper1 appears not to have come up cleanly")


		# machines is a dict of dicts containing information about each machine for you to use.
		machines = {}
		machines.update({'imagestepper1':{'fqdn':'imagestepper1.vagrant.test'}})
		ip = shutit.send_and_get_output('''vagrant landrush ls | grep -w ^''' + machines['imagestepper1']['fqdn'] + ''' | awk '{print $2}' ''')
		machines.get('imagestepper1').update({'ip':ip})

		for machine in sorted(machines.keys()):
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su -',password='vagrant')
			root_password = 'root'
			shutit.install('net-tools') # netstat needed
			if not shutit.command_available('host'):
				shutit.install('bind-utils') # host needed
			# Workaround for docker networking issues + landrush.
			shutit.send("""echo "$(host -t A index.docker.io | grep has.address | head -1 | awk '{print $NF}') index.docker.io" >> /etc/hosts""")
			shutit.send("""echo "$(host -t A registry-1.docker.io | grep has.address | head -1 | awk '{print $NF}') registry-1.docker.io" >> /etc/hosts""")
			shutit.send("""echo "$(host -t A auth.docker.io | grep has.address | head -1 | awk '{print $NF}') auth.docker.io" >> /etc/hosts""")
			shutit.multisend('passwd',{'assword:':root_password})
			shutit.send("""sed -i 's/.*PermitRootLogin.*/PermitRootLogin yes/g' /etc/ssh/sshd_config""")
			shutit.send("""sed -i 's/.*PasswordAuthentication.*/PasswordAuthentication yes/g' /etc/ssh/sshd_config""")
			shutit.send('service ssh restart || systemctl restart sshd')
			shutit.multisend('ssh-keygen',{'Enter':'','verwrite':'n'})
			shutit.logout()
			shutit.logout()
		for machine in sorted(machines.keys()):
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su -',password='vagrant')
			for copy_to_machine in machines:
				for item in ('fqdn','ip'):
					shutit.multisend('ssh-copy-id root@' + machines[copy_to_machine][item],{'assword:':root_password,'ontinue conn':'yes'})
			shutit.logout()
			shutit.logout()
		shutit.login(command='vagrant ssh ' + sorted(machines.keys())[0])
		shutit.login(command='sudo su -',password='vagrant')
		shutit.install('docker')
		shutit.install('git')
		shutit.send('systemctl start docker')
		shutit.send('git clone https://github.com/docker-in-practice/image-stepper')
		shutit.send('cd image-stepper/example')
		shutit.send('docker build -t myimage -q .')
		shutit.send('cd ..')
		shutit.send('docker run --rm -v /var/run/docker.sock:/var/run/docker.sock dockerinpractice/image-stepper myimage')
		shutit.pause_point('docker images')
		shutit.logout()
		shutit.logout()
		shutit.log('''Vagrantfile created in: ''' + shutit.cfg[self.module_id]['vagrant_run_dir'] + '/' + module_name,add_final_message=True,level=logging.DEBUG)
		shutit.log('''Run:

	cd ''' + shutit.cfg[self.module_id]['vagrant_run_dir'] + '/' + module_name + ''' && vagrant status && vagrant landrush ls

To get a picture of what has been set up.''',add_final_message=True,level=logging.DEBUG)
		return True


	def get_config(self, shutit):
		shutit.get_config(self.module_id,'vagrant_image',default='ubuntu/xenial64')
		shutit.get_config(self.module_id,'vagrant_provider',default='virtualbox')
		shutit.get_config(self.module_id,'gui',default='false')
		shutit.get_config(self.module_id,'memory',default='512')
		shutit.get_config(self.module_id,'vagrant_run_dir',default='/tmp')
		return True

	def test(self, shutit):
		return True

	def finalize(self, shutit):
		return True

	def is_installed(self, shutit):
		# Destroy pre-existing, leftover vagrant images.
		shutit.run_script('''#!/bin/bash
MODULE_NAME=image_stepper
rm -rf $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/vagrant_run/*
if [[ $(command -v VBoxManage) != '' ]]
then
	while true
	do
		VBoxManage list runningvms | grep ${MODULE_NAME} | awk '{print $1}' | xargs -IXXX VBoxManage controlvm 'XXX' poweroff && VBoxManage list vms | grep image_stepper | awk '{print $1}'  | xargs -IXXX VBoxManage unregistervm 'XXX' --delete
		# The xargs removes whitespace
		if [[ $(VBoxManage list vms | grep ${MODULE_NAME} | wc -l | xargs) -eq '0' ]]
		then
			break
		else
			ps -ef | grep virtualbox | grep ${MODULE_NAME} | awk '{print $2}' | xargs kill
			sleep 10
		fi
	done
fi
if [[ $(command -v virsh) ]] && [[ $(kvm-ok 2>&1 | command grep 'can be used') != '' ]]
then
	virsh list | grep ${MODULE_NAME} | awk '{print $1}' | xargs -n1 virsh destroy
fi
''')
		return False

	def start(self, shutit):
		return True

	def stop(self, shutit):
		return True

def module():
	return image_stepper(
		'image-stepper.image_stepper.image_stepper', 1713167213.0001,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['shutit.tk.setup','shutit-library.virtualization.virtualization.virtualization','tk.shutit.vagrant.vagrant.vagrant']
	)
