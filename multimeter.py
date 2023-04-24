import time
import serial
import sys
from datetime import datetime, timedelta

# tested with BTMETER BT-90EPC multimeter on OS-X

# configure the serial connections (the parameters differs on the device you are connecting to)
ser = serial.Serial(
    port='/dev/cu.usbserial-221320',
    baudrate=2400,
    timeout=0,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    dsrdtr=True,
    rtscts=False,
)
ser.isOpen()

# given a binary string, pad it with leading zeros to make it 4 bits long
def padbin(binstring):
        message = str(binstring).split('b')[1]
        message = '0'*(4-len(message)) + message
        return message

# this resolves a number given an array of seven "lcd" segments from the screen as described by
# string of 1s in ABCDEFG order:
# --A--
# F   B
# --G--
# E   C
# --D--
def getdigit(segments):
        match segments:
                case '1111110': return '0'
                case '0110000': return '1'
                case '1101101': return '2'
                case '1111001': return '3'
                case '0110011': return '4'
                case '1011011': return '5'
                case '1011111': return '6'
                case '1110000': return '7'
                case '1111111': return '8'
                case '1111011': return '9'
                case '0000000': return ' '        
        return 'L'

# this class represents a reading from the multimeter
# it is constructed from an array of 14 binary strings representing the 14 segments of the LCD display
# in alignment with the Voltcraft RS232 protocol popular in the BTMETER multimeters.
class Reading:
        def __init__(self, signals):
                self.timestamp = datetime.now()
                if signals[3][0] == '1':
                        self.p1 = '.'
                else:
                        self.p1 = ''
                
                if signals[5][0] == '1':
                        self.p2 = '.'
                else:
                        self.p2 = ''
                
                if signals[7][0] == '1':
                        self.p3 = '.'
                else:
                        self.p3 = ''
                if signals[0][0] == '1':
                        self.AC = True
                else:
                        self.AC = False
                if signals[0][1] == '1':
                        self.DC = True
                else:
                        self.DC = False
                if signals[0][2] == '1':
                        self.AUTO = True
                else:
                        self.AUTO = False
                if signals[0][3] == '1':
                        self.RS232 = True
                else:
                        self.RS232 = False
                
                if signals[1][0] == '1':
                        self.polarity = '-'
                else:
                        self.polarity = '+'
                
                self.digit1 = getdigit(
                        "%s%s%s%s%s%s%s" % (
                        signals[1][3],
                        signals[2][3],
                        signals[2][1],
                        signals[2][0],
                        signals[1][1],
                        signals[1][2],
                        signals[2][2])
                )
                self.digit2 = getdigit(
                        "%s%s%s%s%s%s%s" % (
                        signals[3][3],
                        signals[4][3],
                        signals[4][1],
                        signals[4][0],
                        signals[3][1],
                        signals[3][2],
                        signals[4][2])
                )     
                self.digit3 = getdigit(
                        "%s%s%s%s%s%s%s" % (
                        signals[5][3],
                        signals[6][3],
                        signals[6][1],
                        signals[6][0],
                        signals[5][1],
                        signals[5][2],
                        signals[6][2])
                )
                self.digit4 = getdigit(
                        "%s%s%s%s%s%s%s" % (
                        signals[7][3],
                        signals[8][3],
                        signals[8][1],
                        signals[8][0],
                        signals[7][1],
                        signals[7][2],
                        signals[8][2])
                )

                if signals[12][3] == '1':
                        self.lowbat = True
                else:
                        self.lowbat = False
                
                if signals[9][3] == '1':
                        self.diodetest = True
                else:
                        self.diodetest = False
                if signals[9][2] == '1':
                        self.scale = 'k'
                elif signals[9][1] == '1':
                        self.scale = 'n'
                elif signals[9][0] == '1':
                        self.scale = 'u'
                elif signals[10][0] == '1':
                        self.scale = 'm'
                elif signals[10][2] == '1':
                        self.scale = 'M'
                else:
                        self.scale = ''
                
                if signals[11][0] == '1':
                        self.unit = 'F'
                elif signals[11][1] == '1':
                        self.unit = 'Ohm'
                elif signals[11][2] == '1':
                        self.unit = 'delta'
                elif signals[12][0] == '1':
                        self.unit = 'A'
                elif signals[12][1] == '1':
                        self.unit = 'V'
                elif signals[12][2] == '1':
                        self.unit = 'Hz'
                else:
                        self.unit =''

        def __str__(self):
                message = f'{self.timestamp} '
                if (self.DC):
                        message += "DC "
                if (self.AC):
                        message += "AC "
                if (self.AUTO):
                        message += "Auto "
                if (self.RS232):
                        message += "RS232 "
                message += f'{self.polarity}{self.digit1}{self.p1}{self.digit2}{self.p2}{self.digit3}{self.p3}{self.digit4}'
                message += f' {self.scale}{self.unit}'
                return message




packet = []

# the BTMETER multimeter sends a continuous stream of data with no start or end bytes 
# delimiting the stream, instead they take the first hex digit of each byte and use it to order a packet of 14 bytes
# so we can detect the first byte with initial digit "1" and then collect the packet and send it to the decoder function

while True:
        sys.stdout.flush()
        data = ser.read(1)
        for i in data:
                val = hex(i)
                segn = int(str(val)[2:3],base=16)
                valstr = str(val)[2:]
                signal = int(str(val)[-1:],base=16)
                sigbi = padbin(bin(signal))

                if valstr[0] == '1':
                        packet = []
                packet.append(sigbi)
                if len(packet) == 14: 
                        newread = Reading(packet)
                        print(newread)