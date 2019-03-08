# Pi_Radio
Streaming Radio for RasperryPi as a weekend project. 
This is a documentation for myself, so I know what I have done so far.

## Roadmap
- [x] Pi plays Radio from Url Stream
- [x] PiRadio has some kind of UI (Buttons/LCD)
- [x] PiRadio has LCD that displays currently playing station/song
- [x] Make UI robust. (Problem is actually mpd -> fixed mpd version 0.20.12)
- [ ] Minimize boot-time (~5 sec. Problem is start of LCD)
- [x] build case for Pi and custom speakers
- [x] on/off switch
- [x] Volume control

![1](https://github.com/loaded02/Pi_Radio/raw/master/doc/pic_1.jpg)

## Hardware
- Raspberry Pi Model B+ V1.2
- Sandisk 32GB MicroSD HC1 Ultra, Class 10, Read 80MB/s, Write 10MB/s
- Adafruit Blue&White 16x2 LCD+Keypad Kit for Raspberry Pi
- Adafruit Stereo 3.7W Class D Audio Amplifier - MAX98306
- 8 Ohm 5 Watt Speakers

## OS Image
- ArchLinuxARM-2018.12-rpi

#### Tutorials used:
- Arch Linux for RasperryPi [ArchLinux ARM](https://archlinuxarm.org/platforms/armv6/raspberry-pi)
- MPD, Webserver [SemperVideo](https://www.youtube.com/watch?v=pnpnWMh-IG4)
- LCD-Kit Setup I2C [Adafruit](https://learn.adafruit.com/adafruit-16x2-character-lcd-plus-keypad-for-raspberry-pi/usage)
- LCD-Kit Python script [Adafruit](https://github.com/adafruit/Python-WiFi-Radio/blob/master/PiPhi.py)
- Amplifier & Speakers [Adafruit](https://learn.adafruit.com/stereo-3-7w-class-d-audio-amplifier/build-a-portable-sound-system)

## Speed Up Boot Time

> TODO: - initramfs, minimal Yocto Image

## MPD/MPC
```shell
pacman -Syu
```
```shell
pacman -S mpd
mv /etc/mpd.conf /etc/mpd.conf.orig
```
> install mpc-git from ArchAUR. Unmute sound with alsamixer.

paste new mpd.conf as /etc/mpd.conf
```shell
systemctl start mpd.service
systemctl enable mpd.service
```
paste new sender.m3u as /var/lib/mpd/playlists/sender.m3u
```shell
mpc load sender
```

## FTPServer
```shell
pacman -S vsftpd
```
add these lines in /etc/vsftp.conf
```shell
anonymous_enable=NO
local_enable=YES
```
access with e.g. Filezilla

## Launch at startup

create new file in /etc/systemd/system named mystart.service
create new file in /usr/bin named mystartscript.sh
```shell
chmod 755 /usr/bin/mystartscript.sh
systemctl start mystart.service
systemctl enable mystart.service
```

## Static Ip

via Router

## LCD-Kit
### I2C Support

> install i2c-tools-git, python-smbus-git, raspi-config from ArchAUR

(i2c-tools is optional)
add these lines in /boot/config.txt
```shell
dtparam=i2c1=on
dtparam=i2c_arm=on
```
now
```shell
sudo reboot
```
test
```shell
sudo i2cdetect -y 1
```
### Python Code
```shell
pacman -S python python-pip git
sudo pip install RPi.GPIO
git clone https://github.com/adafruit/Adafruit_Python_CharLCD.git
cd Adafruit_Python_CharLCD
sudo python setup.py install
```
test
```shell
cd examples
sudo python char_lcd_plate.py
```
python script
```shell
mkdir ~/PiRadio
cd PiRadio
ln -s ../Adafruit_Python_CharLCD/Adafruit_CharLCD/*.py .
```
paste PiRadio.py in ~/PiRadio

test
```
sudo python PiRadio.py
```

## Pictures

![1](https://github.com/loaded02/Pi_Radio/raw/master/doc/pic_1.jpg)
![2](https://github.com/loaded02/Pi_Radio/raw/master/doc/pic_2.jpg)
![1](https://github.com/loaded02/Pi_Radio/raw/master/doc/pic_3.jpg)
![2](https://github.com/loaded02/Pi_Radio/raw/master/doc/pic_4.jpg)

