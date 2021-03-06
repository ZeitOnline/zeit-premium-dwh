# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = "ubuntu/bionic64"

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  config.vm.box_check_update = true

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # config.vm.network "forwarded_port", guest: 80, host: 8080

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network "private_network", ip: "192.168.33.10"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  config.vm.synced_folder ".", "/vagrant"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  config.vm.provider "virtualbox" do |vb, override|
    vb.linked_clone = true
    override.vm.network "private_network", ip: "192.168.34.13"
  end

  config.vm.provider "vsphere" do |v, override|
    override.vm.allowed_synced_folder_types = ["rsync"]
    override.vm.box = "vsphere"
    override.vm.synced_folder ".", "/vagrant", type: "rsync"
    v.compute_resource_name = "Zeit-DCC"
    v.data_center_name = ENV["GOVC_DATACENTER"]
    v.data_store_name = "Vmfs_ZON_Staging"
    v.host = "srv-vcenter.zeit.de"
    v.insecure = ENV["GOVC_INSECURE"]
    v.password = ENV["GOVC_PASSWORD"]
    v.template_name = "ZON Templates/ubuntu18-premium-services-template"
    v.user = ENV["GOVC_USERNAME"]
    v.vm_base_path = "ZON Templates"
  end

  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  config.vm.provision "shell", inline: <<-SHELL
    export DEBIAN_FRONTEND=noninteractive
    apt-get -y update
    apt-get -y install \
      git \
      ipython3 \
      libxml2-utils \
      python3-dev \
      python3-lxml \
      python3-pip \
      python3-twisted
    pip3 install -e /vagrant[testing]
  SHELL
end
