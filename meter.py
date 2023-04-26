from argparse import ArgumentParser
from serial import Serial, PARITY_NONE, STOPBITS_ONE, EIGHTBITS
from serial.tools.list_ports import comports
from sys import stdout
from datetime import datetime, timedelta

def binpad(binstring):
        message = '0'*(4-len(binstring)) + binstring
        return message

def chop_segment(foo):
        left =  binpad(str(bin(int(hex(foo)[2],base=16))[2:]))
        right = binpad(str(bin(int(hex(foo)[3],base=16))[2:]))
        return left, right

def decode(message):
        # print (len(message))
        data = str(message)
        return data

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

class Reading:
        def __init__(self, signals):
                self.timestamp = datetime.now()
                self.p1 = '.' if signals[3][0] == '1' else ''
                self.p2 = '.' if signals[5][0] == '1' else ''
                self.p3 = '.' if signals[7][0] == '1' else ''
                self.AC = True if signals[0][0] == '1' else False
                self.DC = True if signals[0][1] == '1' else False
                self.AUTO = True if signals[0][2] == '1' else False
                self.RS232 = True if signals[0][3] == '1' else False
                self.polarity = '-' if signals[1][0] == '1' else '+'
                self.lowbat = True if signals[12][3] == '1' else False
                self.diodetest = True if signals[9][3] == '1' else False
                
                self.digit4 = getdigit(
                        "%s%s%s%s%s%s%s" % (
                        signals[1][3],
                        signals[2][3],
                        signals[2][1],
                        signals[2][0],
                        signals[1][1],
                        signals[1][2],
                        signals[2][2])
                )
                self.digit3 = getdigit(
                        "%s%s%s%s%s%s%s" % (
                        signals[3][3],
                        signals[4][3],
                        signals[4][1],
                        signals[4][0],
                        signals[3][1],
                        signals[3][2],
                        signals[4][2])
                )     
                self.digit2 = getdigit(
                        "%s%s%s%s%s%s%s" % (
                        signals[5][3],
                        signals[6][3],
                        signals[6][1],
                        signals[6][0],
                        signals[5][1],
                        signals[5][2],
                        signals[6][2])
                )
                self.digit1 = getdigit(
                        "%s%s%s%s%s%s%s" % (
                        signals[7][3],
                        signals[8][3],
                        signals[8][1],
                        signals[8][0],
                        signals[7][1],
                        signals[7][2],
                        signals[8][2])
                )

                self.scale = ''
                if signals[9][2] == '1':  self.scale = 'k'
                if signals[9][1] == '1':  self.scale = 'n'
                if signals[9][0] == '1':  self.scale = 'u'
                if signals[10][0] == '1': self.scale = 'm'
                if signals[10][2] == '1': self.scale = 'M'
                
                self.unit = ''
                if signals[11][0] == '1': self.unit = 'F'
                if signals[11][1] == '1': self.unit = 'Ohm'
                if signals[11][2] == '1': self.unit = 'delta'
                if signals[12][0] == '1': self.unit = 'A'
                if signals[12][1] == '1': self.unit = 'V'
                if signals[12][2] == '1': self.unit = 'Hz'
   
        def __str__(self):
                message = f'{self.timestamp} '
                if (self.DC): message += "DC "
                if (self.AC): message += "AC "
                if (self.AUTO): message += "Auto "
                if (self.RS232): message += "RS232 "
                message += f'{self.polarity}{self.digit4}{self.p1}{self.digit3}{self.p2}{self.digit2}{self.p3}{self.digit1}'
                message += f' {self.scale}{self.unit}'
                return message
        


def __main__():
    parser = ArgumentParser(prog='meter.py', description='Decode RS232 Voltcraft protocol.')
    parser.add_argument('--port', help='Serial port to read from', default='UNKNOWN')
    parser.add_argument('--baud', help='Baud rate to use', default='2400')
    parser.add_argument('--samples', help='Number of readings to take', default='0')
    args = parser.parse_args()
    if args.port == 'UNKNOWN':
      print(f'No port specified, your ports:')
      for port in comports():
        print(f'  {port}')
      exit(1)
    else: comport = args.port
    samples = int(args.samples)
    baud = int(args.baud)
    messagebuf = []
    count = 0
    ser = Serial(
        port=comport,
        baudrate=baud,
        timeout=0,
        parity=PARITY_NONE,
        stopbits=STOPBITS_ONE,
        bytesize=EIGHTBITS,
        dsrdtr=True,
        rtscts=False,
    )
    ser.isOpen()


    while True:
            stdout.flush()
            data = ser.read(1)
           
            if(len(data) > 0): 
                left,right =  chop_segment(data[0])
                if left == '0001':
                    count += 1 
                    if (len(messagebuf) == 14):
                            reading = Reading(messagebuf)
                            print (reading)
                    messagebuf = []
                messagebuf.append(right)

            if (count > samples and samples > 0):
                  print (count,samples)
                  exit()
__main__()