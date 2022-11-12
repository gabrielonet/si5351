from machine import I2C,Pin
import utime

i2c=I2C(0,sda=Pin(0),scl=Pin(1),freq=400000)
print (i2c.scan())

step_sw=Pin(15,Pin.IN,Pin.PULL_UP)
pinA = Pin(0,Pin.IN,Pin.PULL_UP)
pinB = Pin(1,Pin.IN,Pin.PULL_UP)

#Di5351A関係定義
Si5351A_ADDR = 0x60
MSNA_ADDR = 26
MSNB_ADDR = 34
MS0_ADDR = 42
MS1_ADDR = 50
MS2_ADDR = 58
CLK0_CTRL = 16
CLK1_CTRL = 17
CLK2_CTRL = 18
OUTPUT_CTRL = 3
XTAL_LOAD_C = 183
PLL_RESET = 177
XtalFreq = 25000000
df = -62 #周波数補正値
denom = 1048575
frequency = 7000000 #周波数初期値
frequency_old = frequency
step = 10000 #step初期値
old_fH=""
old_fM=""
old_fL=""
f_Max = 7200000 #周波数最大値
f_Min = 7000000 #周波数最小値


#Rotary Encoder関係定義
befDat=0x11
curDat=0
count=0

buf = bytearray(2)

def Si5351_write(reg,data):
     buf[0] = reg
     buf[1] = data
     i2c.writeto(Si5351A_ADDR,buf)

#Si5351A initialize
def Si5351_init():
     Si5351_write(OUTPUT_CTRL,0xFF)#Disable Output
     Si5351_write(CLK0_CTRL,0x80)   #CLK0 Power down
     Si5351_write(CLK1_CTRL,0x80)   #CLK1 Power down
     Si5351_write(CLK2_CTRL,0x80)   #CLK2 Power down
     Si5351_write(XTAL_LOAD_C,0x40)#Crystal Load Capacitance=6pF
     Si5351_write(PLL_RESET,0xA0)   #Reset PLLA and PLLB
     Si5351_write(CLK0_CTRL,0x4F)   #CLK0 Power up 8mA
#     Si5351_write(CLK1_CTRL,0x4F)   #CLK1 Power up 8mA
#     Si5351_write(CLK2_CTRL,0x4F)   #CLK2 Power up 8mA
     Si5351_write(OUTPUT_CTRL,0xFE)#Enable CLOK0

def PLLA_set(freq):
     global XtalFreq,divider,df,denom
     freq += df #df=周波数補正値
     divider = int(900000000 / freq)
     divider >> 1 #dividerは整数かつ偶数
     divider << 1
     PllFreq = divider * freq
     mult = PllFreq // XtalFreq
     l = PllFreq % XtalFreq
     f = l * denom
     num = f // XtalFreq
     P1 = int(128 * (num / denom))
     P1 = 128 * mult + P1 - 512
     P2 = int(128 * (num / denom))
     P2 = 128*num - denom * P2
     P3 = denom

     Si5351_write(MSNA_ADDR + 0,(P3 & 0x0000FF00) >> 8)  #MSNA_P3[15:8]
     Si5351_write(MSNA_ADDR + 1,(P3 & 0x000000FF))       #MSNA_P3[7:0]
     Si5351_write(MSNA_ADDR + 2,(P1 & 0x00030000) >> 16) #MSNA_P1[17:16]
     Si5351_write(MSNA_ADDR + 3,(P1 & 0x0000FF00) >> 8)  #MSNA_P1[15:8]
     Si5351_write(MSNA_ADDR + 4,(P1 & 0x000000FF))       #MSNA_P1[7:0]
     Si5351_write(MSNA_ADDR + 5,((P3 & 0x000F0000) >> 12) | ((P2 & 0X000F0000) >> 16))#MSNA_P3[19:16]MSNA_P2[19:16]
     Si5351_write(MSNA_ADDR + 6,(P2 & 0x0000FF00) >> 8)  #MSNA_P2[15:8]
     Si5351_write(MSNA_ADDR + 7,(P2 & 0x000000FF))       #MSNA_P2[7:0]

def MS0_set():
     global divider
     P1=128*divider-512
     P2=0
     P3=1
     Si5351_write(MS0_ADDR + 0,(P3 & 0x0000FF00) >> 8)   #MS0_P3[15:8]
     Si5351_write(MS0_ADDR + 1,(P3 & 0x000000FF))        #MS0_P3[7:0]
     Si5351_write(MS0_ADDR + 2,(P1 & 0x00030000) >> 16)  #MS0_P1[17:16]
     Si5351_write(MS0_ADDR + 3,(P1 & 0x0000FF00) >> 8)   #MS0_P1[15:8]
     Si5351_write(MS0_ADDR + 4,(P1 & 0x000000FF))        #MS0_P1[7:0]
     Si5351_write(MS0_ADDR + 5,((P3 & 0x000F0000) >> 12) | ((P2 & 0X000F0000) >> 16))#MS0_P3[19:16]MS0_P2[19:16]
     Si5351_write(MS0_ADDR + 6,(P2 & 0x0000FF00) >> 8)   #MS0_P2[15:8]
     Si5351_write(MS0_ADDR + 7,(P2 & 0x000000FF))        #MS0_P2[7:0 Si5351_init()

#周波数表示


#周波数変更
def Freq_Change():
     global frequency
     PLLA_set(frequency)
     MS0_set()
     Freq_Disp(frequency)

def hantei(p):
     global curDat,befDat,count
     global frequency,step
     global f_Max,f_Min
     curDat=pinA.value() + (pinB.value()<<1)
     if curDat != befDat:
         D = ((befDat<<1)^curDat)&3
         if D<2:
             count = count + 1
         else:
             count = count - 1
         befDat = curDat
         if count >= 3:
             frequency += step
             count=0
         elif count <= -3:
             frequency -= step
             count=0
     if frequency >= f_Max:
         frequency = f_Max
     if frequency <= f_Min:
         frequency = f_Min

Si5351_init()
PLLA_set(frequency)
MS0_set()




pinA.irq(trigger=Pin.IRQ_FALLING|Pin.IRQ_RISING,handler=hantei)
pinB.irq(trigger=Pin.IRQ_FALLING|Pin.IRQ_RISING,handler=hantei)




