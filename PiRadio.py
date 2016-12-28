#!/usr/bin/python
import os, time, socket
import Adafruit_CharLCD as LCD

# Constants:
HALT_ON_EXIT = False # Set to 'True' to shut down system when exiting
MAX_FPS      = 4 # Limit screen refresh rate for legibility
VOL_MIN      = 65
VOL_MAX      = 100
VOL_DEFAULT  = 100
HOLD_TIME    = 3.0 # Time (seconds) to hold select button for shut down
PICKLEFILE   = '/var/lib/mpd/playlists/sender.m3u'

# Global state:
volCur       = VOL_MIN     # Current volume
volNew       = VOL_DEFAULT # 'Next' volume after interactions
volSpeed     = 1.0         # Speed of volume change (accelerates w/hold)
volSet       = False       # True if currently setting volume
paused       = False       # True if music is paused
staSel       = False       # True if selecting station
volTime      = 0           # Time of last volume button interaction
playMsgTime  = 0           # Time of last 'Playing' message display
staBtnTime   = 0           # Time of last button press on station menu
xTitle       = 16          # X position of song title (scrolling)
xInfo        = 16          # X position of artist/album (scrolling)
xStation     = 0           # X position of station (scrolling)
xTitleWrap   = 0
xInfoWrap    = 0
xStationWrap = 0
songTitle   = ''
songInfo    = ''
stationNum  = 0            # Station currently playing
stationNew  = 0            # Station currently highlighted in menu
stationList = ['']
stationIDs  = ['']

# Char 7 gets reloaded for different modes.  These are the bitmaps:
charSevenBitmaps = [
  [0b10000, # Play (also selected station)
   0b11000,
   0b11100,
   0b11110,
   0b11100,
   0b11000,
   0b10000,
   0b00000],
  [0b11011, # Pause
   0b11011,
   0b11011,
   0b11011,
   0b11011,
   0b11011,
   0b11011,
   0b00000],
  [0b00000, # Next Track
   0b10100,
   0b11010,
   0b11101,
   0b11010,
   0b10100,
   0b00000,
   0b00000]]

# --------------------------------------------------------------------------

def get_ip_address(ifname):
	f = os.popen('ip addr show eth0 | grep "\<inet\>" | awk \'{ print $2 }\' | awk -F "/" \'{ print $1 }\'')
	return f.read()


# Draws song title or artist/album marquee at given position.
# Returns new position to avoid global uglies.
def marquee(s, x, y, xWrap):
    lcd.set_cursor(0, y)
    if x > 0: # Initially scrolls in from right edge
        lcd.message(' ' * x + s[0:16-x])
    else:     # Then scrolls w/wrap indefinitely
        lcd.message(s[-x:16-x])
        if x < xWrap: return 0
    return x - 1		 

def drawPlaying():
    lcd.create_char(7, charSevenBitmaps[0])
    lcd.set_cursor(0, 1)
    lcd.message('\x07 Playing       ')
    return time.time()


def drawPaused():
    lcd.create_char(7, charSevenBitmaps[1])
    lcd.set_cursor(0, 1)
    lcd.message('\x07 Paused        ')


def drawNextTrack():
    lcd.create_char(7, charSevenBitmaps[2])
    lcd.set_cursor(0, 1)
    lcd.message('\x07 Next track... ')

# Draw station menu (overwrites fulls screen to facilitate scrolling)
def drawStations(stationNew, listTop, xStation, staBtnTime):
    last = len(stationList)
    if last > 2: last = 2  # Limit stations displayed
    ret  = 0  # Default return value (for station scrolling)
    line = 0  # Line counter
    msg  = '' # Clear output string to start
    for s in stationList[listTop:listTop+2]: # For each station...
        sLen = len(s) # Length of station name
        if (listTop + line) == stationNew: # Selected station?
            msg += chr(7) # Show selection cursor
            if sLen > 15: # Is station name longer than line?
                if (time.time() - staBtnTime) < 0.5:
                    # Just show start of line for half a sec
                    s2 = s[0:15]
                else:
                    # After that, scrollinate
                    s2 = s + '   ' + s[0:15]
                    xStationWrap = -(sLen + 2)
                    s2 = s2[-xStation:15-xStation]
                    if xStation > xStationWrap:
                        ret = xStation - 1
            else: # Short station name - pad w/spaces if needed
                s2 = s[0:15]
                if sLen < 15: s2 += ' ' * (15 - sLen)
        else: # Not currently-selected station
            msg += ' '   # No cursor
            s2 = s[0:15] # Clip or pad name to 15 chars
            if sLen < 15: s2 += ' ' * (15 - sLen)
        msg  += s2 # Add station name to output message
        line += 1
        if line == last: break
        msg  += '\n' # Not last line - add newline
    lcd.set_cursor(0, 0)
    lcd.message(msg)
    return ret

def getStations():
	print('Retrieving station list...')
	lcd.clear()
	lcd.message('Retrieving\nstation list...')
	a = os.popen('mpc playlist').read()
	a = a.splitlines()
	names = []
	ids = []
	for idx, b in enumerate(a):
		ids.append(idx)
		names.append(b)
	return names, ids	

#-----------------------------------------------------------------
# Initialization

lcd = LCD.Adafruit_CharLCDPlate()
lcd.clear()

# Create volume bargraph custom characters (chars 0-5):
for i in range(6):
    bitmap = []
    bits   = (255 << (5 - i)) & 0x1f
    for j in range(8): bitmap.append(bits)
    lcd.create_char(i, bitmap)

# Create up/down icon (char 6)
lcd.create_char(6,
  [0b00100,
   0b01110,
   0b11111,
   0b00000,
   0b00000,
   0b11111,
   0b01110,
   0b00100])

# By default, char 7 is loaded in 'pause' state
lcd.create_char(7, charSevenBitmaps[1])

lcd.clear()
#lcd.message('My IP address is\n' + get_ip_address('eth0'))
#time.sleep(1)
# Show IP address (if network is available).  System might be freshly
# booted and not have an address yet, so keep trying for a couple minutes
# before reporting failure.
t = time.time()
while True:
    if (time.time() - t) > 120:
        # No connection reached after 2 minutes
        lcd.message('Network is\nunreachable')
        time.sleep(30)
        exit(0)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        lcd.message('My IP address is\n' + s.getsockname()[0])
        time.sleep(5)
        break         # Success -- let's hear some music!
    except:
        time.sleep(1) # Pause a moment, keep trying

#print('Playing Default Station')
#os.system('mpc stop')
#time.sleep(1)
#os.system('mpc play 1')
stationList, stationIDs = getStations()
time.sleep(1)

lastTime = 0

while True:
	x = os.popen('mpc current').read()
	if x is not None:
		x = x.strip()
		s = x + '    '
                n = len(s)
                xTitleWrap = -n + 2
                # 1+ copies + up to 15 chars for repeating scroll
                songTitle = s * (1 + (16 / n)) + s[0:16]
		s = '*** My PiRadio ***'
		n = len(s)
		xInfoWrap = -n + 2
		songInfo = s * (2 + (16 / n)) + s[0:16]

	btnUp = lcd.is_pressed(LCD.UP)
	btnDown = lcd.is_pressed(LCD.DOWN)
	btnLeft = lcd.is_pressed(LCD.LEFT)
	btnRight = lcd.is_pressed(LCD.RIGHT)
	btnSel = lcd.is_pressed(LCD.SELECT)

	# Certain button actions occur regardless of current mode.
    	# Holding the select button (for shutdown) is a big one.
	if btnSel:
		# If tapped, different things in different modes...
        	if staSel:                  # In station select menu...
            		staSel = False          #  Cancel menu and return to
            		if paused: drawPaused() #  play or paused state
        	else:                       # In play/pause state...
            		volSet = False          #  Exit volume-setting mode (if there)
            		paused = not paused     #  Toggle play/pause
                	if paused:
				os.system('mpc pause') 
				drawPaused() #  Display play/pause change
            		else:   
				os.system('mpc play')   
				playMsgTime = drawPlaying()

	# Right button advances to next track in all modes, even paused,
    	# when setting volume, in station menu, etc.
	elif btnRight:
		print('Next Station')
		drawNextTrack()
		if staSel: # Cancel station select, if there
			staSel = False
		paused = False # Un-pause, if there
		volSet = False
		os.system('mpc next')

	# Left button enters station menu (if currently in play/pause state),
    	# or selects the new station and returns.
	elif btnLeft:
		print('Left Button')
		staSel = not staSel # Toggle station menu state
        	if staSel:
            		# Entering station selection menu.  Don't return to volume
            		# select, regardless of outcome, just return to normal play.
            		lcd.create_char(7, charSevenBitmaps[0])
            		volSet     = False
            		cursorY    = 0 # Cursor position on screen
            		stationNew = 0 # Cursor position in list
            		listTop    = 0 # Top of list on screen
            		xStation   = 0 # X scrolling for long station names
			# Just keep the list we made at start-up
			#stationList, stationIDs = getStations()
            		staBtnTime = time.time()
            		drawStations(stationNew, listTop, 0, staBtnTime)
        	else:
            		# Just exited station menu with selection - go play.
            		stationNum = stationNew # Make menu selection permanent
            		print 'Selecting station: "{}"'.format(stationIDs[stationNum])
            		os.system('mpc play ' + str(stationIDs[stationNum]))
            		paused = False

    	# Up/down buttons either set volume (in play/pause) or select station
	elif btnUp or btnDown:

        	if staSel:
            		# Move up or down station menu
            		if btnDown:
                		if stationNew < (len(stationList) - 1):
                    			stationNew += 1              # Next station
                    			if cursorY < 1: cursorY += 1 # Move cursor
                    			else:           listTop += 1 # Y-scroll
                    			xStation = 0                 # Reset X-scroll
            		elif stationNew > 0:                 # btnUp implied
                    		stationNew -= 1              # Prev station
                    		if cursorY > 0: cursorY -= 1 # Move cursor
                    		else:           listTop -= 1 # Y-scroll
                    		xStation = 0                 # Reset X-scroll
            		staBtnTime = time.time()             # Reset button time
            		xStation = drawStations(stationNew, listTop, 0, staBtnTime)
        	else:
            		# Not in station menu
            		if volSet is False:
                		# Just entering volume-setting mode; init display
                		lcd.set_cursor(0, 1)
                		volCurI = int((volCur - VOL_MIN) + 0.5)
                		n = int(volCurI / 5)
                		s = (chr(6) + ' Volume ' +
                     			chr(5) * n +       # Solid brick(s)
                     			chr(volCurI % 5) + # Fractional brick 
                     			chr(0) * (6 - n))  # Spaces
                		lcd.message(s)
                		volSet   = True
                		volSpeed = 1.0
            		# Volume-setting mode now active (or was already there);
            		# act on button press.
            		if btnUp:
                		volNew = volCur + volSpeed
                		if volNew > VOL_MAX: volNew = VOL_MAX
            		else:
                		volNew = volCur - volSpeed
                		if volNew < VOL_MIN: volNew = VOL_MIN
            			volTime   = time.time() # Time of last volume button press
            			volSpeed *= 1.15        # Accelerate volume change


	# Other logic specific to unpressed buttons:
    	else:
        	if staSel:
            		# In station menu, X-scroll active station name if long
            		if len(stationList[stationNew]) > 15:
                		xStation = drawStations(stationNew, listTop, xStation,
                  			staBtnTime)
        	elif volSet:
            		volSpeed = 1.0 # Buttons released = reset volume speed
            		# If no interaction in 4 seconds, return to prior state.
            		# Volume bar will be erased by subsequent operations.
            		if (time.time() - volTime) >= 4:
                		volSet = False
                		if paused: drawPaused()

	#else:
		#lcd.set_cursor(0, 1)
                #volCurI = 32 #35 max
                #n = int(volCurI / 5)
                #s = (chr(6) + ' Volume ' +
                #     chr(5) * n +       # Solid brick(s)
                #     chr(volCurI % 5) + # Fractional brick 
                #     chr(0) * (6 - n))  # Spaces
                #lcd.message(s)
	
	# Various 'always on' logic independent of buttons
    	if not staSel:
        	# Play/pause/volume: draw upper line (song title)
        	if songTitle is not None:
            		xTitle = marquee(songTitle, xTitle, 0, xTitleWrap)

		# Integerize current and new volume values
        	volCurI = int((volCur - VOL_MIN) + 0.5)
        	volNewI = int((volNew - VOL_MIN) + 0.5)
        	volCur  = volNew
       	 	# Issue change to mpc
        	if volCurI != volNewI:
            		d = volNewI - volCurI
            		#if d > 0: s = ')' *  d
            		#else:     s = '(' * -d
            		#pianobar.send(s)

        	# Draw lower line (volume or artist/album info):
        	if volSet:
            		if volNewI != volCurI: # Draw only changes
               			if(volNewI > volCurI):
                    			x = int(volCurI / 5)
                    			n = int(volNewI / 5) - x
                    			s = chr(5) * n + chr(volNewI % 5)
                		else:
                    			x = int(volNewI / 5)
                    			n = int(volCurI / 5) - x
                    			s = chr(volNewI % 5) + chr(0) * n
                		lcd.set_cursor(x + 9, 1)
                		lcd.message(s)
        	elif paused == False:
            		if (time.time() - playMsgTime) >= 3:
                		# Display artist/album (rather than 'Playing')
                		xInfo = marquee(songInfo, xInfo, 1, xInfoWrap)

	 # Throttle frame rate, keeps screen legible
    	while True:
        	t = time.time()
        	if (t - lastTime) > (1.0 / MAX_FPS): break
    	lastTime = t
