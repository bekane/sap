# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "generic/ubuntu2204"

  config.vm.provider :libvirt do |libvirt|
    libvirt.cpus = 4
    libvirt.memory = 4096
  end 

  config.vm.define "sap" do |master|
    master.vm.hostname = "sap"
  end


  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "playbook.yml"
  end

end
