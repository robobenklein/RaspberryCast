#!/bin/sh

if [ `id -u` -ne 0 ]
then
  echo "Please run this script with root privileges!"
  echo "Try again with sudo."
  exit 0
fi

echo "This script will install RaspberryCast"

read -p "Which user do you want to install RaspberryCast as? (Leave blank to set to default): " USER

if ! [ -n "$USER" ]; then
    echo "Setting user to default value 'pi'."
    USER="pi"
fi

if ! getent passwd $USER > /dev/null 2>&1; then
    echo "User $USER does not exist. Exiting."
    exit
fi

echo "Do you wish to continue? (y/n)"

while true; do
  read -p "" yn
  case $yn in
      [Yy]* ) break;;
      [Nn]* ) exit 0;;
      * ) echo "Please answer with Yes or No [y|n].";;
  esac
done
echo ""
echo "============================================================"
echo ""
echo "Installing necessary dependencies... (This could take a while)"
echo ""
echo "============================================================"
apt-get update
apt-get install -y lsof python3-pip git wget omxplayer libnss-mdns fbi
echo "============================================================"

if [ "$?" = "1" ]
then
  echo "An unexpected error occured during apt-get!"
  exit 0
fi

pip3 install youtube-dl bottle livestreamer

if [ "$?" = "1" ]
then
  echo "An unexpected error occured during pip install!"
  exit 0
fi

echo ""
echo "============================================================"
echo ""
echo "Adding project to startup sequence and custom options"
echo ""
echo "============================================================"

#Gives right to all user to get out of screen standby
chmod 666 /dev/tty1

#Add to rc.local startup
sed -i '$ d' /etc/rc.local
echo "su - $USER -c \"cd ./RaspberryCast/ && ./RaspberryCast.sh start\"" >> /etc/rc.local
echo "exit 0" >> /etc/rc.local

#Adding right to current pi user to shutdown
chmod +s /sbin/shutdown

#Adding right to sudo fbi without password
echo "$USER ALL = (root) NOPASSWD: /usr/bin/fbi" >> /etc/sudoers

echo "============================================================"
echo "Setup was successful."
echo "Do not delete the 'RaspberryCast' folder as it contains all application data!"
echo "Please reboot the system now!"
echo "============================================================"

sleep 2

exit 0
