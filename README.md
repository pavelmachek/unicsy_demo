# unicsy_demo

Demo of phone functionality

This is mainly meant for PostmarketOS, but I try to keep it working on
Debian, too, because development is easier there.

In PostmarketOS, can be run on weston as
XDG_RUNTIME_DIR=/tmp/0-runtime-dir/ python2 ./demo.py . Needs to be
ran as root for some functionality.

unicsy_demo needs to be symlinked into /usr/share/unicsy -- like
sudo ln -s /my/unicsy_demo /usr/share/unicsy

Actually, most of unicsy is meant for python2 -- as that one is faster.

xscreensaver-demo. Powermanagement needs to be enabled. Default timeouts are 120 minutes, set it to 1 minute.

* On Mobian/Phosh

ssh-keygen
.ssh/authorized_keys



sudo apt-get install aptitude

openssh-server foxtrotgps

https://github.com/pavelmachek/unicsy_demo

vpravo nahore, settings
https://github.com/settings/keys

sudo aptitude install git emacs-nox

mobian@mobian:~$ sudo mkdir /my
mobian@mobian:~$ sudo chown mobian /my
cd /my
git clone git@github.com:pavelmachek/unicsy_demo.git

https://gitlab.com/tui/tui

vpravo nahore preferences, vlevo v menu ssh keys

python3-gi ?

root@mobian:/my/unicsy_demo/demo# cd /usr/share/
root@mobian:/usr/share# ln -s /my/unicsy_demo/ unicsy

/my/tui/tricorder$ python3 ruler.py
# dobry test.

git clone pavel@10.0.0.9:~/v



* On Maemo Leste

run /etc/expandcard.sh

sudo su
aptitude install python-gtk2 python-dbus ofono git
# Also needs yad libqmi-utils

cd /usr/share/unicsy
git clone https://github.com/pavelmachek/unicsy_demo.git


ofono modem rules https://gitlab.com/postmarketOS/pmaports/blob/master/device/device-nokia-n900/udev/10-nokia-modem.rules
ofono compilation:

sudo aptitude install gcc make automake libtool libglib2.0-dev libdbus-1-dev libudev-dev mobile-broadband-provider-info

Running as GTK2_RC_FILES= demo/demo.py provides more reasonable
graphics output.

sudo modprobe ssi_protocol
sudo modprobe cmt_speech
sudo modprobe nokia-modem

# Authors

This project started in November 2014, in the "tui" project.

Copyright 2014-2018 Pavel Machek <pavel@ucw.cz>

Distribute under GPLv3 or later, as described in the COPYING file.

