import RPi.GPIO as GPIO
from time import sleep
from Tkinter import *
import math
import time
import numpy as np
import spidev
from datetime import datetime, timedelta
import sys

#this is a test web edit

#To Do
#       eventually a particle counter lable 
## look into SSH remot control/screen sharing
## backwash time determined by flow past a certian point
## see if Graph can scroll with time rather than a set window
## prompt to save data
## make target data defineable in the program
## add in pressure drop over the solenoids
## Emergency shutoff needs to pass in an argument or else it doesn't work
#______________________________________________________________________________________________________________________
#----------------------------------------------------------------------------------------------------------------------
                                                                                                                                                                                                                         

print("start")
#Setting up Spi to read ADC
spi_0 = spidev.SpiDev()
spi_0.open(0, 0)  #the second number indicates which SPI pin CE0 or CE1
#to_send = [0x01,0x02,0x03] # speed Hz,Delay, bits per word
#spi_0.xfer(to_send)

#Setting up Global Variables
ForwardPumpTarget=15
ForwardFlowCount = 0.0
oldForwardFlowCount= 0.0
forwardflow = 0.0
BackwashPumpTarget=45
BackwashFlowCount = 0.0
oldBackwashFlowCount= 0.0
backwashflow = 0.0
FlowTarget = 1.0
PumpThreshold = 1
StartTime = datetime.now()
samplePeriod = 100  #milliseconds, time between data points written to txt file
minimumtime = 1000
destination = "/home/pi/Desktop/Data/AutosavedData.txt"
a=open(destination,'w') #a means append to existing file, w means overwrite old data
a.write("\n\n"+ str(datetime.now())+","+str(ForwardPumpTarget)+","+str(BackwashPumpTarget)+","+str(FlowTarget)+","+str(PumpThreshold))
backwash = False
switched = False
cycles = 0
Average= 3 # taking 15 samples per second average of 15 will average over one second
flowshow = 0.0
backshow = 0.0
FPshow = ForwardPumpTarget
BPshow = BackwashPumpTarget
Diffshow= ForwardPumpTarget


#Setting up GUI
class popupWindow(object):
    def __init__(self,master):
        top=self.top=Toplevel(master)
        self.l=Label(top,text="Set Value")
        self.l.pack()
        self.e=Entry(top)
        self.e.pack()
        self.b=Button(top,text='Done',command=self.cleanup)
        self.b.pack()
    def cleanup(self):
        self.value=self.e.get()
        self.top.destroy()

class mainWindow(object):
    def __init__(self,master):
        self.master=master
        self.b=Button(master,text="Click Here",command=self.popup)
        self.b.pack()
        self.b2=Button(master,text="Update Flow Target",command=lambda: FTdisplay.set((str(self.entryValue()))))
        self.b2.pack()
        self.b3=Button(master,text="Update Pump Threshold",command=lambda: PTdisplay.set((str(self.entryValue()))))
        self.b3.pack()


    def popup(self):
        self.w=popupWindow(self.master)
        self.master.wait_window(self.w.top)

    def entryValue(self):
        return self.w.value


root = Tk()
root.title("Backwash Control")

#----initializing GUI------------------
background_image = PhotoImage(file='/home/pi/Desktop/Code/background.gif')
w=background_image.width()
h=background_image.height() 
C = Canvas(root, bg='#333',height=(h+5),width=(w+5))
C.focus_set() # Sets the keyboard focus to the canvas
bg_label = Label(C , image=background_image)
bg_label.pack()
Ftank_text = Label(C, text='psi:', padx=5)
Ftank_text.place(x=320,y=41)
Btank_text = Label(C, text='psi:', padx=5)
Btank_text.place(x=318,y=338)
FTL= StringVar()
FTL.set('0')
forward_tank_label = Label(C, textvariable=FTL, padx=5)
forward_tank_label.place(x=350,y=41)
BTL= StringVar()
BTL.set('0')
back_tank_label = Label(C, textvariable=BTL, padx=5)
back_tank_label.place(x=350,y=338)
DL= StringVar()
DL.set('0')
differential_label = Label(C, textvariable=DL, padx=5)
differential_label.place(x=400,y=200)
Flowrate_text = Label(C, text='Flow Rate:', padx=5,pady=3)
Flowrate_text.place(x=418,y=89)
Flowrate_text2 = Label(C, text='Flow Rate:', padx=5,pady=3)
Flowrate_text2.place(x=418,y=274)
FRL= StringVar()
FRL.set('0')
Flowrate_label = Label(C, textvariable=FRL,pady=3)
Flowrate_label.place(x=489,y=89)
BFL= StringVar()
BFL.set('0')
BackFlowrate_label = Label(C, textvariable=BFL,pady=3)
BackFlowrate_label.place(x=489,y=274)
Cycle_text = Label(C,text='Cycles:', padx=5,pady=3)
Cycle_text.place(x=605,y=182)
CY= StringVar()
CY.set('0')
Cycle_label = Label(C, textvariable=CY, padx=5,pady=3)
Cycle_label.place(x=655,y=182)
Concentrate_text = Label(C,text='Liters:', padx=5)
Concentrate_text.place(x=760,y=145)
CL= StringVar()
CL.set('0')
Concentrate_label = Label(C, textvariable=CL, padx=5)
Concentrate_label.place(x=805,y=145)
Filtrate_text = Label(C,text='Liters:', padx=5)
Filtrate_text.place(x=760,y=320)
FL= StringVar()
FL.set('0')
Filtrate_label = Label(C, textvariable=FL, padx=5)
Filtrate_label.place(x=805,y=320)
frame=Frame(root)
frame.pack(anchor=NW)


#----Threshold set up-----------------
FTdisplay = StringVar()
FTdisplay.set((str(FlowTarget)))
FTlabel = Label(frame, textvariable=FTdisplay)
FTlabel.pack()


PTdisplay = StringVar()
PTdisplay.set((str(PumpThreshold)))
Plabel = Label(frame, textvariable=PTdisplay)
Plabel.pack()

#----Manual control switchs----------------
Switch=StringVar()
Switch.set('Forward')
ManualSwitch = Checkbutton(frame,indicatoron=0,textvariable=Switch)
ManualSwitch.pack()
##Switch2=StringVar()
##Switch2.set('Liters')
##boolvar= IntVar()
##boolvar.set(1)
##ConversionSwitch = Checkbutton(frame,indicatoron=0,textvariable=Switch2,variable=boolvar)
##ConversionSwitch.pack()

#--- Graph settings
screenWidth = 450
resolution = 1 #number of pixels between data points, for visual purposes only
timeRange = .5 #minutes
baseTime = int(timeRange*60*1000/screenWidth)
x0Coords = []
y0Coords = []
xy0Coords = []
FlowrateAvg = []
BackflowAvg = []
FPumpAvg = []
BPumpAvg = []
DiffAvg = []

coordLength = int(screenWidth/resolution)
#---initiation of lists
for i in range(0,coordLength):
    x0Coords.append(i*resolution)
    y0Coords.append(249)
    xy0Coords.append(0)
    xy0Coords.append(0)
for i in range(0,Average):
    FlowrateAvg.append(FlowTarget)
    BackflowAvg.append(0)
    FPumpAvg.append(ForwardPumpTarget)
    BPumpAvg.append(BackwashPumpTarget)
    DiffAvg.append(0)
    
#putting X and Y corrdinites in a list
def coordinate():
    global x0Coords, y0Coords, xy0Coords
    for i in range(0,coordLength*2,2):
        xy0Coords[i] = x0Coords[i/2]
        xy0Coords[i+1] = y0Coords[i/2]
#---End initiation of lists

Graph= LabelFrame(root, text="Flow Graph",height=250,width=screenWidth)
Graph.pack()
GraphC=Canvas(Graph, bg = "gray", height = 249, width = screenWidth-1)
c0 = GraphC.create_rectangle(0,0,20,50)
cl0 = GraphC.create_line(xy0Coords,smooth=True)
ctar = GraphC.create_line(0,(249-FlowTarget*20),450,(249-FlowTarget*20), fill='red')
scale5 = Label(GraphC, text=' 20-', bg = "gray")
scale5.place(x=0,y=(240-20*12))
scale7 = Label(GraphC, text=' 18-', bg = "gray")
scale7.place(x=0,y=(240-18*12))
scale9 = Label(GraphC, text=' 16-', bg = "gray")
scale9.place(x=0,y=(240-16*12))
scale11 = Label(GraphC, text='14-', bg = "gray")
scale11.place(x=0,y=(240-14*12))
scale12 = Label(GraphC, text='12-', bg = "gray")
scale12.place(x=0,y=(240-12*12))
scale10 = Label(GraphC, text='10-', bg = "gray")
scale10.place(x=0,y=(240-10*12))
scale8 = Label(GraphC, text=' 8-', bg = "gray")
scale8.place(x=0,y=(240-8*12))
scale6 = Label(GraphC, text=' 6-', bg = "gray")
scale6.place(x=0,y=(240-6*12))
scale4 = Label(GraphC, text=' 4-', bg = "gray")
scale4.place(x=0,y=(240-4*12))
scale2 = Label(GraphC, text=' 2-', bg = "gray")
scale2.place(x=0,y=(240-2*12))
scale0 = Label(GraphC, text=' 0-', bg = "gray")
scale0.place(x=0,y=(240-0*20))

#setting up GPIO pins
ForwardTankValve = 14
ForwardPump = 15
BackwashPump = 18
ForwardPumpValve = 23
BackwashTankValve = 24
BackwashPumpValve = 25                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
ForwardFlow = 22
BackwashFlow = 17
on = GPIO.LOW
off = GPIO.HIGH
vopen = GPIO.LOW
vclose = GPIO.HIGH
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(ForwardTankValve, GPIO.OUT)
GPIO.setup(ForwardPumpValve, GPIO.OUT)
GPIO.setup(ForwardPump, GPIO.OUT)
GPIO.setup(BackwashTankValve, GPIO.OUT)
GPIO.setup(BackwashPumpValve, GPIO.OUT)
GPIO.setup(BackwashPump, GPIO.OUT)
GPIO.setup(ForwardFlow, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)#Generally reads LOW
GPIO.setup(BackwashFlow, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

#----------------------Function Definitons--------------------------------

def readadc_0(adcnum_0): #this fucntion can be used to find out the ADC value on ADC 0
    if adcnum_0 > 7 or adcnum_0 < 0:
        return -1

    r_0 = spi_0.xfer2([1, 8 + adcnum_0 << 4, 0]) #start bit, Single/Differential mode, Don't care bit OR
    adcout_0 = ((r_0[1] & 3) << 8) + r_0[2]
    return adcout_0

def readadc_0diff(adcnum_0): #this fucntion can be used to find out the differential ADC value between two chanels on ADC 0
    if adcnum_0 > 7 or adcnum_0 < 0:
        return -1
    r_0 = spi_0.xfer2([1, adcnum_0 << 4, 0]) #start bit, Single/Differential mode, Don't care bit OR
    adcout_0 = ((r_0[1] & 3) << 8) + r_0[2]
    return adcout_0

def callback_fflow(ForwardFlow):
    global ForwardFlowCount
    ForwardFlowCount+=1

def callback_bflow(BackwashFlow):
    global BackwashFlowCount
    BackwashFlowCount+=1

#shifts y values down in index in array to represent time moved forward
def shiftCoords(nextValue):

    global y0Coords, xy0Coords
    y0Coords.pop(0)
    y0Coords.append(int(nextValue))
    coordinate()

#updates the GUI based on the new time
def move_time():
    global c0,cl0,ctar,xy0Coords,resolution,baseTime,forwardflow,backwashflow,flowshow,FPshow,Diffshow
    GraphC.delete(c0)
    GraphC.delete(cl0)
    GraphC.delete(ctar)
    c0 = GraphC.create_rectangle(0,0,20,int(backwashflow/1023*250))
    shiftCoords(249-(flowshow*12))
    cl0 = GraphC.create_line(xy0Coords)
    ctar = GraphC.create_line(0,(249-float(FTdisplay.get())*20),450,(249-float(FTdisplay.get())*20), fill='red')
    #print(float(readadc_0(0))/1023*250)
    #title="V= " , str(round(3.3*float(readadc_0(2)-readadc_0(0))/1023,2)) , str(round(3.3*float(readadc_0(2))/1023,2)), str(round(3.3*float(readadc_0(0))/1023,2))
    #root.title(title)
    root.after(baseTime*resolution,move_time)

def checkback():
    global  forwardflow, backwash, Switch, switched, cycles, FlowTarget, flowshow
    if backwash == True:
        backwash = False
        Switch.set('Forward')
        if switched == True:
            cycles = cycles+1
            CY.set(str(cycles))
        switched  = False
        
    if flowshow < float(FTdisplay.get()) and flowshow > .1 and BPshow > 40: 
        backwash = True
        Switch.set('Backwash')
        switched = True
    root.after(minimumtime,checkback)
        
def writeData(): 
    global destination,cycles,Diffshow,switched,samplePeriod,ForwardFlowCount,oldForwardFlowCount,BackwashFlowCount,oldBackwashFlowCount,forwardflow,backwashflow,FlowrateAvg,flowshow

    ##Calibration of sensor: Real Pressure = reading-(-1.06+.1007xreading)
    Reading=(3.3*float(readadc_0(3)-readadc_0(0))/1023)*100
    ForwardPumpActual=round(Reading-(-1.06+.1007*Reading),1)
    FPumpAvg.pop(0)
    FPumpAvg.append(ForwardPumpActual)
    FPshow=np.mean(FPumpAvg)
    FTL.set(str(round(FPshow,1)))
    if ForwardPumpTarget-FPshow > float(PTdisplay.get())/2:
         GPIO.output(ForwardPump,on)
    if FPshow-ForwardPumpTarget > float(PTdisplay.get())/2: #float(PTdisplay.get()):
        GPIO.output(ForwardPump,off)

    Reading=(3.3*float(readadc_0(1)-readadc_0(0))/1023)*100
    BackwashPumpActual=round(Reading-(-1.06+.1007*Reading),1)
    BPumpAvg.pop(0)
    BPumpAvg.append(BackwashPumpActual)
    BPshow=np.mean(BPumpAvg)
    BTL.set(str(round(BPshow,1)))
    if BackwashPumpTarget-BackwashPumpActual > float(PTdisplay.get())/2: #float(PTdisplay.get()):
        GPIO.output(BackwashPump, on)
    if BackwashPumpActual - BackwashPumpTarget > float(PTdisplay.get())/2:
        GPIO.output(BackwashPump, off)

    if BackwashPumpActual > 55 or ForwardPumpActual > 55:
        print 'EMERGENCY SHUT OFF: Pressure too high!'
        callback_end()

    Reading = (3.3*float(readadc_0(2)-readadc_0(0))/1023)*100
    DifferentialPressure=round(Reading-(-1.06+.1007*Reading),1)
    DiffAvg.pop(0)
    DiffAvg.append(DifferentialPressure)
    Diffshow=np.mean(DiffAvg)
    DL.set(str(round(Diffshow,1)))
    
##    if boolvar.get() == 1:
##        Switch2.set('Liters')
##        ConversionFactor = 60 # conversion factor to liters per minute
##        ConversionFactor2 = 1000 # pulses per lieter
##    else:
##        Switch2.set('Gallons')
##        ConversionFactor = 15.7
##        ConversionFactor2 = 3800 # pulses per gallon
 
    if backwash:
        GPIO.output(ForwardPumpValve,vclose)
        GPIO.output(BackwashTankValve, vclose)
        GPIO.output(ForwardTankValve,vopen)
        GPIO.output(BackwashPumpValve, vopen)

    else:
        GPIO.output(ForwardTankValve,vclose)
        GPIO.output(BackwashPumpValve, vclose)
        GPIO.output(BackwashTankValve, vopen)
        GPIO.output(ForwardPumpValve,vopen)
        

        
        
    forwardflow=((ForwardFlowCount-oldForwardFlowCount)/samplePeriod)*60 #60 is a conversion factor to convert the flowrate from pulses per 100miliseconds to liters per minute
    FlowrateAvg.pop(0)
    FlowrateAvg.append(forwardflow)
    flowshow = np.mean(FlowrateAvg)
    FRL.set(str(round(flowshow,1)))
    backwashflow=((BackwashFlowCount-oldBackwashFlowCount)/samplePeriod)*60
    BackflowAvg.pop(0)
    BackflowAvg.append(backwashflow)
    BFL.set(str(round(backwashflow,1)))
    CL.set(str(round(BackwashFlowCount/1000,1)))
    FL.set(str(round(ForwardFlowCount/1000,1)))
    data = str(round(Diffshow,1)) + "\t" + str(round(flowshow,1)) + "\t" +str(round(backwashflow,1)) + "\t" +str(round(FPshow,1))+ "\t" +str(round(BPshow,1))+'\t'+str(cycles)+'\t'+str(backwash) 
    a.write("\n"+ str(datetime.now()) + ", " + str(data))
    oldForwardFlowCount=ForwardFlowCount
    oldBackwashFlowCount=BackwashFlowCount
    root.after(samplePeriod,writeData)

def callback_end(event):
    global FlowCount, StartTime
    GPIO.output(ForwardPump, off)
    GPIO.output(BackwashPump, off)
    GPIO.output(ForwardTankValve, vopen)#lets pressure out into the tank
    GPIO.output(ForwardPumpValve, vclose)#Keeps pressure in the tank
    GPIO.output(BackwashTankValve, vopen)
    GPIO.output(BackwashPumpValve, vclose)
    time.sleep(10)
    GPIO.output(BackwashTankValve, vclose)
    GPIO.output(ForwardTankValve, vclose)
    # GPIO.cleanup()#i think this would get get rid of the draining process
    spi_0.close()
    a.close()
    quit()

#Setting up event detection
GPIO.add_event_detect(ForwardFlow, GPIO.RISING, callback=callback_fflow)
GPIO.add_event_detect(BackwashFlow, GPIO.RISING, callback=callback_bflow)


#----------------------------------Main loop----------------------------------------


C.bind("<End>",callback_end)
C.pack()
GraphC.pack(anchor=CENTER)
root.after(baseTime,move_time)
root.after(samplePeriod,writeData)
root.after(minimumtime,checkback)
m=mainWindow(root)
root.mainloop()
