# Pi_Radio
Streaming Radio for RasperryPi as a weekend project. 
This is a documentation for myself, so I know what I have done so far.

## Roadmap
- [x] Pi plays Radio from Url Stream
- [x] PiRadio has some kind of UI (WebInterface and Buttons/LCD)
- [x] PiRadio has LCD that displays currently playing station/song
- [ ] Make UI robust. (Problem is actually mpd)
- [ ] Minimize boot-time
- [x] build case for Pi and custom speakers
- [ ] on/off switch
- [ ] use different Webserver

## Hardware
- Raspberry Pi Model B+ V1.2
- Adafruit Blue&White 16x2 LCD+Keypad Kit for Raspberry Pi
- Active Speaker

## OS Image
- Raspian

#### Tutorials used:
- MPD, Webserver [SemperVideo](https://www.youtube.com/watch?v=pnpnWMh-IG4)
- LCD-Kit Setup I2C [Adafruit](https://learn.adafruit.com/adafruit-16x2-character-lcd-plus-keypad-for-raspberry-pi/usage)
- LCD-Kit Python script [Adafruit](https://github.com/adafruit/Python-WiFi-Radio/blob/master/PiPhi.py)


## MPD/MPC
```shell
apt-get update
apt-get upgrade
```
```shell
apt-get install mpd mpc alsa-utils
mv /etc/mpd.conf /etc/mpd.conf.orig
```
paste new mpd.conf as /etc/mpd.conf
```shell
service mpd restart
```
paste new sender.m3u as /var/lib/mpd/playlists/sender.m3u
```shell
mpc load sender.m3u
```
## WebServer
```shell
apt-get install apache2 php5 libapache2-mod-php5
```
access Pi at http://\<my-ip\>

## FTPServer
```shell
apt-get install proftpd
```
access with e.g. Filezilla

```shell
cd /var/www
chmod 777 -R /var/www
```

paste html folder in /var/www

(icons from [iconfinder.com](http://iconfinder.com), images from radiostations are missing in rep)

## Launch at startup

paste rc.local in /etc/rc.local

## Static Ip

via Router

## LCD-Kit
### I2C Support
```shell
apt-get install python-smbus i2c-tools
```
(i2c-tools is optional)

add these lines in /etc/modules
```shell
i2c-bcm2708
i2c-dev
```
comment out these lines in /etc/modprobe.d/raspi-blacklist.conf
```shell
#blacklist spi-bcm2708
#blacklist i2c-bcm2708
```

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
sudo apt-get update
sudo apt-get install build-essential python-dev python-smbus python-pip git
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

