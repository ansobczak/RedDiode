#!/usr/bin/python3
# -*- coding: UTF-8 -*-


from time import sleep,perf_counter
import smbus
import threading
#from threading import Thread, Event

global i2c 
i2c=tuple((None,smbus.SMBus(1))) #for future adding more i2c buses. Bus 0 is possible (not recomended however) so here is empy.


class MovDetected(threading.Thread):
   
   def __init__(self, ldt, ts, ev, func, act1, act2, outputs):
      self.last_detect_time=ldt  
      self.l_time=ts
      self.event=ev
      self.function=func
      self.action1=act1
      self.action2=act2
      self.outputs=outputs
#      self.lock = threading.RLock()
      super(MovDetected, self).__init__()
      
   #use as thread:
      #thr=MovDetected(p_time, holdtime, detected_ev, self.action1, 'on','off', self.call)
      #thr.setDaemon(True)
      #thr.set_end_time(p_time)
      #thr.start()
      
      
      
   def set_ld_time(self, ldt):
#      print('send end time 1')
#      with self.lock:
      self.last_detect_time=ldt
         
   def run(self):
#      print('did I reach out here?',self.function)
#      self.set_end_time(self.last_detect_time)
      while True:
#         with self.lock:
         self.event.wait(self.l_time)
         if self.event.isSet(): 
#            print('move isSet {:.2f}'.format(self.last_detect_time))
            self.function([self.action1] + self.outputs)
            sleep(self.l_time)
         print('time is now? {:.2f} {}'.format(perf_counter()-self.last_detect_time, self.l_time))
         if ( perf_counter()-self.last_detect_time ) > self.l_time:
            
            if not self.event.isSet():
               self.function([self.action2] + self.outputs)
#               print('move NOT isSet')

#   def run(self):
#      while True:
#         
#         self.event.wait(self.l_time)
#         if self.event.isSet(): 
#            print('move isSet')
#            self.function([self.action1] + self.outputs)
#            sleep(self.l_time)
#            if not self.event.isSet():
#               self.function([self.action2] + self.outputs)
#               print('move NOT isSet')



class VButt:
   
   '''Vbutt is virtual button class to manage action not on physical buttons 
   # Class dictionary dictionary with list of buttons { name:str: button_object:pointer} '''
   
   Butt_instn = {}
   
   def __init__(self, hum_name, b_out, param):
      self.name = hum_name
      self.call=b_out      #calling functions
      self.param=param
      VButt.Butt_instn.update({self.name: self})    #updated Butt Class dictionary
   
   @classmethod
   def butt(butt_cls,hum_str):            #returns VButt object
      try:
         return butt_cls.Butt_instn[hum_str]
      except:
         return 0
         
   def butt_action(self):
      try:
         self.call(self.param)
      except:
         try:
            self.call()
         except:
            print('VButt action failed')
   
   def v_push(self):       #helper function  
      self.butt_action()


class Butt:
   
   '''# Butt_instn - Class dictionary dictionary with list of buttons { name:str: button_object:pointer}  
   # to_chip: integer: MCP27017 adress within I2C bus. Can be 8 adreses on one I2C bus.
   # to_pin: integer 0-15: the input pin on MCP27017 that button is connected to
   # pin_b is 2**to_pin !!!!!
   # name: string: human readable name
   # call: string:list of outputs Relays button is servicing
   # is_con > rev_log: bool: is the button open by default or closed - can be usefull for the emergency or fail/safe situation, or for contactrons
   # is_mov - is this motion sensor
   # classmethod butt - returning object pointer, takes str argument with name of the button
   # b_read - method to read button'''
   
   
   '''#         Class dictionary dictionary with list of buttons { name:str: button_object:pointer} '''
   Butt_instn = {}
   
   def __init__(self, hum_name, to_chip, to_pin, b_out, is_con, is_mov):
      self.chip=MCP.chip(to_chip)
      self.pin=to_pin      # to_pin: integer 0-15
      self.pin_b=2**to_pin #binary pin adres
      self.name=hum_name      #human readable name
      self.call=b_out      #calling outputs
      self.is_con = is_con            #True if this is contactron are reverse
      self.is_mov = is_mov             #True if this is motion detector
      Butt.Butt_instn.update({self.name: self})    #updated Butt Class dictionary
      self.chip.set_input(self.pin, self)          #sets physical inputs on the chip
      if self.is_con:                  #if contactron, use reverse logic
         self.chip.op_log(self.pin)
      self.butt_action_iterator=''        #this will be iterator function
      self.action1=''            #short press function 
      self.action2=''            #long press function

         
         
   @classmethod
   def butt(butt_cls,hum_str):            #returns Butt object, parameter str with name
      try:
         return butt_cls.Butt_instn[hum_str]
      except:
         return 0
   
   def __str__(self):
     return self.name
     
   
   def b_read(self):          #helper function reading physical button, true if open
      try:
         return (self.butt(self.name).chip.read_chip('GPIO') & self.pin_b) == self.pin_b
      except:
         print('b_read error')
         
   def short_push(self):      #action when pressed shortly
      try:
         self.action1(self.call)
      except:
         print('short press error', self.name)
   
   def long_push(self):    #action when hold
      try:
       self.action2(self.call)
      except:
         print('long press error', self.name)
         
   def v_push(self):       #helper function to keep unity with vbutton  class
      self.short_push()

                  #motion detector iterator function run from main button reading thread
                  #the iterator is self.butt_action_iterator 
   def motion_action(self,data):
      INTF, GPIO, p_time = data #interup, gpio and time of capture
      my_t=p_time    #keeps the previously given time
      holdtime=5    #set it global or button specific in config
      pressed = False   #true if the action was triggered
      detected=False    #true if the motion is detected
      detected_ev=threading.Event() #event controliing the trigered action
      detected_ev.clear() #closing the event
#      self.thr=threading.Thread(name=self.name, target=self.action1, args=(p_time, holdtime,self.detected_ev,'on','off', self.call))
      thr=MovDetected(p_time, holdtime, detected_ev, self.action1, 'on','off', self.call)
                  #time of capture, hold time, event, procedure to trigger, actions 1, 2 , outputs
      thr.setDaemon(True)
      thr.set_ld_time(p_time)       #setting the last detection time for the MovDetected thread
      thr.start()
      print('motion setup',thr.is_alive(),  threading.enumerate())
      
      while True:
         if not thr.is_alive(): print('motion zdechlo') #test
         
         
#         if ( ( GPIO & self.pin_b ) and (not pressed) ) : 
         if ( ( GPIO & self.pin_b ) ) :  
            #if  GPIO   >>> (motion detected)
            detected=True
#            pressed=True
            my_t=p_time
         elif ((INTF & self.pin_b) and (not ( GPIO & self.pin_b ))):  
            #if INTERUPT and not GPIO           >>>>  (motion stopped) 
            detected=False
            
         if ( detected ) and ( not pressed ): 
            #motion detected but no action taken yet
#            print('1 detected {} and pressed {} p_time {}'.format(detected, pressed, p_time))
            thr.set_ld_time(p_time)
            detected_ev.set()
            pressed=True
         if ( not detected ) and (  pressed ):  
            #motion ended and action to be stoped
#            print('not detected and  pressed')
#            thr.set_ld_time(p_time)
            detected_ev.clear()
            detected, pressed  = False, False
#            print('2 detected {} and pressed {}'.format(detected, pressed))
         (INTF, GPIO, p_time) = yield 
   
                  #iterator contactron function run from main button reading thread
                  #the iterator is self.butt_action_iterator 
   def contactron_action(self, data):
      INTF, GPIO, p_time = data
#      my_t=p_time
#      holdtime=0.5    #set it global or button specific in config
#      pressed = False
      hold = False
      cont_open = False
      
                     #this part iterates
      while True:
      
         if ((not (INTF & self.pin_b)) and ( GPIO & self.pin_b ) and (not cont_open)):  
               #if not INTERUPT and GPIO  >>> (hold)
            cont_open=True
            self.long_push() 
         elif ((INTF & self.pin_b) and (not ( GPIO & self.pin_b ))):  
               #if INTERUPT and not GPIO           >>>>  (released)
            if cont_open: self.short_push() #for buttons
            cont_open=False
         (INTF, GPIO, p_time) = yield 
               
                  #iterator function run from main button reading thread
                  #the iterator is self.butt_action_iterator 
   def butt_action(self, data):
      INTF, GPIO, p_time = data
      my_t=p_time
      holdtime=0.5    #set it global or button specific in config
      pressed = False
      hold = False
      
                     #this part iterates
      while True:
         (INTF, GPIO, p_time) = yield
#         print('butt_action {} INTF {:>4x} GPIO {:>4x} pin {:>16b} time {}'.format(self.name, INTF, GPIO, self.pin_b,p_time - my_t))
      
         if ((not (INTF & self.pin_b)) and ( GPIO & self.pin_b )):  
            #if not INTERUPT and GPIO    >>> (hold)
            if ( p_time - my_t ) > holdtime:
               self.long_push()
               my_t=p_time
               hold = True
               
         elif ((INTF & self.pin_b) and ( GPIO & self.pin_b )):  
            #if INTERUPT and  GPIO    >>> ( pressed )
            pressed = True
            hold = False
            my_t = p_time
         
         elif ((INTF & self.pin_b) and (not ( GPIO & self.pin_b ))):  
            #if INTERUPT and not GPIO           >>>>  (released)
            if pressed and (not hold): self.short_push() #for buttons
            pressed = False
            hold = False
            cont_open=False
#         (INTF, GPIO, p_time) = yield 
         
   
   
   

class Relay:
   
   
   '''
   # light is connected to realy, and relay is connected to MCP27017, so MCP chip I2C adres is needed: 
   #   Relay_instn               - instances of relay, dictionary with string name and object pointer
   #                             example {name:str: <object pointer>}
   #  self.chip=MCP.chip(to_chip)  - address to chip object connected with relay
   #  self.pin=ch_pin             - pin on chip connected with relay 0-15
   #  self.relay=to_relay        - human readble number of the relay, so one can figure out phisical/electrical connection
   #  self.name=hum_name         - human readable name of the output/receiver connected to relay
   #  self.is_PWM=PWM               - bool defining if the receiver is a PWM device. 
   #  self.REV                   -bool - define if the relay works in reverse logic - usefull for failsafe lights.'''
   
   Relay_instn = {}
   
   def __init__(self, to_chip, ch_pin, to_relay, hum_name, is_PWM, is_rev):
      self.chip = MCP.chip(to_chip) 
      self.pin = int(ch_pin) #0-15
      self.relay = to_relay
      self.name = hum_name
      self.is_PWM = is_PWM
      self.REV = is_rev
         #adding the object to the list of relay objects
      Relay.Relay_instn.update({self.name: self})       
      try:
         self.chip.set_output(self.pin)
         self.off()
         self.state=False    #parameter saying off when False, on when True
      except:
         print('output setup error', self.name)
         
         
   @classmethod
   def relay(cls,hum_str):            #returns relay object by the human readable str name 
      try:
         return cls.Relay_instn[hum_str]
      except:
         return 0
         
   def __str__(self):
     return self.name
     
   '''#           on and off methods are turning on and off devices connected to realay
   #           if REV is True, the device is on if the relay is off. It is the physical connection of relay that do the negative logic.'''
   
   def on(self):
      
      if self.REV: self.chip.set_output_off(self.pin)
      else: self.chip.set_output_on(self.pin)
      self.state=True
    
   def off(self):
      if self.REV: self.chip.set_output_on(self.pin)
      else: self.chip.set_output_off(self.pin)
      self.state=False
   
      
   def togle(self):
      self.chip.togle_output(self.pin)
      self.state = not self.state
   
   def is_on(self):        #helper function returning true if the relay is open - it check hardware. not parameter
      st=self.chip.is_output_on(self.pin)
      if self.REV: return (not st)
      else: return st



class MCP:
   
   '''
                 to manipulate MCP270017 chips on board. 
   
   name: str: chip human readable name of the chip, example c_B1_20 - for chip on BUS 1 with adres 0x20
   bus: int: I2C bus number, default 1, but it is possible to set up multiple i2c busses or use another bus,
   
                     DO NOT USE BUS 0 (ZERO)!!!!
           unlesss you are absolutely sure what are you doing
           
           
   i2c_addres : hex: chip adres on the bus, can be 8 different addresses from 0x20 to 0x27
   MCP_instnc : Class dictionary: list of  MCP objects (instances). They are created automaticaly as there is no ident
   ConReg_dic : Class dictionary: dictionary of adreses of COntrol Registers.
   Pin adresing:
         The MCP class here is using word read/write, meaning there is no side A and B pins (see below  comment on GpioAdr_dic)
         Register adreses are taken from  ConReg_dic dictionary and Pin adressing is simply 2**0 - 2**15 or 
         from '0b0000000000000001' to '0b1000000000000000' - alwas only one bit on(1).
   
   self.inputs={}                #inputs dictionary, key: pin, value: butt pointer
   self.inputs_b              #binary representation of inputs
   
   @classmethod    def chip(mcp_cls,name_str):            #returns Object pointer, argument is name string
   def read_chip(self, ConRe):      read from chip, to be used to read input pins or get the chip status
   def write_chip(self, ConRe, val):      write to chip, 
   def pin_adr(self, pin):       return pin hex adres,argument
   def set_input(self,pin, input_dev_pointer):     setting inputs pin
   def set_output(self,*pin):    clear inputs pin - if no argument provided all inputs will be cleared    
   def togle_output(self,*pin):     togle output status for pins or for all
   def op_log(self,pin):   set up oposit logic for pin, usefull for contactrons or reverse logic inputs
   def norm_log(self,pin):    set up normal logic for pin
   def set_output_on(self,*pin):    set outpin pin ON
   def set_output_off(self,*pin):      set outpin pin OFF
   def is_output(self, *pin):  check if PIN is IN or OUT, for single pin in argument returns True if pin is OUTPUT
#                   return string with the whole list if more pins or no pins in argument, 
   def is_input(self, *pin):  check if PIN is IN or OUT, for single pin in argument returns True if pin is INPUT
                    return string with the whole list if more pins or no pins in argument, 
   
   def is_output_on(self,pin):    returning status of and if Output. reverse logic handled in Relay classs
   

   '''
   
#              MCP_instnc : Class dictionary: list of  MCP objects (instances). 
#              MCP objects are created automaticaly as there is no ident
   MCP_instnc = {}
   
#              ConReg_dic - PIO_Control Registers: same names, values and function as described in 
#              MCP27017 dosc https://ww1.microchip.com/downloads/en/DeviceDoc/20001952C.pdf 
#              The MCP is using word read/write, meaning there is no side A and B pins
   ConReg_dic={
         'GPPU':   0x0C,
         'IODIR':  0x00,
         'OLAT':   0x14,
         'GPIO':   0x12,
         'IPOL':   0x02,
         'GPINTEN':0x04,
         'INTCON': 0x08,
         'DEFVAL': 0x06,
         'INTF':   0x0E,
         'INTCAP': 0x10
          }
          
#     The MCP is using word read/write, meaning there is no side A and B pins. the below is for refernece only
#     Register adreses are taken from  ConReg_dic dictionary and Pin adressing is from 2**0 to 2**15 or 
#      from '0b0000000000000001' to '0b1000000000000000'
# GPIO_Adres number: GPIO,  adres, 
#   GpioAdr_dic={
#   0:  ('A0', 0x01),
#   1:  ('A1', 0x02),
#   2:  ('A2', 0x04),
#   3:  ('A3', 0x08),
#   4:  ('A4', 0x10),
#   5:  ('A5', 0x20),
#   6:  ('A6', 0x40),
#   7:  ('A7', 0x80),
#   8:  ('B0', 0x01),
#   9:  ('B1', 0x02),
#   10: ('B2', 0x04),
#   11: ('B3', 0x08),
#   12: ('B4', 0x10),
#   13: ('B5', 0x20),
#   14: ('B6', 0x40),
#   15: ('B7', 0x80)
#   }
   
   def __init__(self, name, i2cbus, i2c_addres):
      self.name=name
      self.bus=i2cbus
      self.bus_adrs=i2c_addres
      MCP.MCP_instnc.update({self.name: self})
      self.clean()
   
   def __str__(self):
        return self.name
   
   @classmethod
   def chip(mcp_cls,name_str):            #returns Object pointer, argument is name string
      try:
         return mcp_cls.MCP_instnc[name_str]
      except:
         return 0 
         
   
   def clean(self):                 #cleaning the MCP chip setup. 
      self.write_chip('GPPU',  0b0) #no pull ups for inputs
      self.write_chip('IODIR', 0b0) #define all as output
      self.write_chip('OLAT',  0b0) #close for outputs
      self.inputs_b=0               #binary representation of inputs
      self.inputs={}                #inputs dictionary, key: pin, value: butt pointer
   
#                                read from chip, to be used to read input pins
   def read_chip(self, ConRe):
      try:
         global i2c
#         r=i2c[self.bus].read_word_data( self.bus_adrs, self.ConReg_dic[ConRe])
#         print('read i2c %d  chip %s adres %s result %d %s' % (self.bus, hex(self.bus_adrs), hex(self.ConReg_dic[ConRe]),r, bin(r)))
#         return r
         return i2c[self.bus].read_word_data( self.bus_adrs, self.ConReg_dic[ConRe])
      except:
         print('read_chip ERROR {}  {}'.format(ConRe, self.name))
         return 0
   
#                             return pin bin value adres,argument 0..15
   def pin_adr(self, pin):
      if pin in range(0,16): 
         return 2**pin         
      else:
         print ('error pin adres', self, pin)
         return 0
         
#                                   write to chip, 
   def write_chip(self, ConRe, val):
      try:
         global i2c
#         print('write i2c %d  chip  %s adres %s vbin %s vhex %s' % (self.bus, hex(self.bus_adrs), hex(self.ConReg_dic[ConRe]), hex(val), bin(val)))  #test
         i2c[self.bus].write_word_data( self.bus_adrs, self.ConReg_dic[ConRe], val)
         return 1
      except:
         print('write_chip ERROR')
         return 0
      
#                       setting inputs pin: 0-15, input_dev_pointer - pointer to button
   def set_input(self,pin, input_dev_pointer):
      try:
         pin_b = self.pin_adr(pin)
         self.write_chip('IODIR',  ( pin_b |  self.read_chip('IODIR') )) #define as input
         self.write_chip('GPPU', ( pin_b |  self.read_chip('GPPU') ) ) #add pull ups for inputs
         self.write_chip('GPINTEN', ( pin_b |  self.read_chip('GPINTEN') ) ) #add to INTERUPS pins
         self.write_chip('INTCON', ( (~(pin_b) & 0xffff) &  self.read_chip('INTCON') ) ) #add to INTERUPS on-change (not DEFAULT)
         self.inputs.update({pin_b:input_dev_pointer})                      #update input list for referencing inputs
         self.inputs_b |= pin_b
      except:
         print('set_input ERROR {}')
         
#                       clear inputs pin
#                       if no argument provided all inputs will be cleared        
   def set_output(self,*pin):
      try:
         if not len(pin):            #if no pin passed as parameters, all pins will be outputs
            pin=range(0,16)
         for p in pin:
   #         print('set output controller', p)
            self.write_chip('IODIR',  ((~(self.pin_adr(p)) & 0xffff) & self.read_chip('IODIR'))) 
            self.write_chip('GPPU',  ((~(self.pin_adr(p)) & 0xffff) & self.read_chip('GPPU'))) 
                    #Bitwise bit removal ((~0b101 & 0b11111111) & 0b10101110) > '0b10101010'
            self.norm_log(p) 
                     #forcing norm logic
            try:
               del self.inputs[self.pin_adr(p)]  #removes from input list 
            except:
               pass 
      except:
         print('set_output ERROR {} {}'.format(pin, self.name))
          
#                             togle output status for pins or for all
   def togle_output(self,*pin):
      if not len(pin):            #if no pin passed as parameters, 
         pin=range(0,16)
      for p in pin:
         self.write_chip('OLAT', (self.read_chip('OLAT') ^ self.pin_adr(p))) #togle with bin XOR
   
#                    set up oposit logic for pin, usefull for contactrons or reverse logic inputs
   def op_log(self,pin):
      self.write_chip('IPOL',  (self.read_chip('IPOL') | self.pin_adr(pin)))
                  #in/out logic are ConRegs 02 and 03. value 1 is oposit 0 is normal
                  #Bitwise OR bin(0b110101 | 0b001000) > '0b111101'
   
   
#                    set up normal logic for pin
   def norm_log(self,pin):
      self.write_chip('IPOL',  ((~(self.pin_adr(pin)) & 0xffff) & self.read_chip('IPOL')))
                  #in/out logic are ConRegs 02 and 03. value 1 is oposit 0 is normal
                  #Bitwise bit removal ((~0b101 & 0b11111111) & 0b10101110) > '0b10101010'
   
#                             set outpin pin ON
   def set_output_on(self,*pin):
      if not len(pin):            #if no pin passed as parameters, 
         pin=range(0,16)
      for p in pin:
         self.write_chip('OLAT',  (self.read_chip('OLAT') | self.pin_adr(p))) #add open output by binary OR
   
#                             set outpin pin OFF
   def set_output_off(self,*pin):
      if not len(pin):            #if no pin passed as parameters, 
         pin=range(0,16)
      for p in pin:
         self.write_chip('OLAT', ((~(self.pin_adr(p)) & 0xffff) & self.read_chip('OLAT')))
                  #Bitwise bit removal ((~0b101 & 0b11111111) & 0b10101110) > '0b10101010'
   
#                    check if PIN is IN or OUT, for single pin in argument returns True if pin is OUTPUT
#                    return string with the whole list if more pins or no pins in argument, 
   def is_output(self, *pin):
      try:
         if len(pin)==1: 
            for p in pin:
               return  (self.read_chip('IODIR') & self.pin_adr(p)) == 0
         if not len(pin):            #if no pin passed as parameters, 
            pin=range(0,16)
         out_str=''
         for p in pin:
            out_str+=str('\nPin %d chip GPIO %s or %d output %s ' % (p, bin(self.pin_adr(p)), self.pin_adr(p), ((self.read_chip('IODIR') & self.pin_adr(p)) == 0 )))
         return out_str
      except:
         return str('is_output error', pin)
   
#                    check if PIN is IN or OUT, for single pin in argument returns True if pin is INPUT
#                    return string with the whole list if more pins or no pins in argument, 
   def is_input(self, *pin):
      try:
         if len(pin)==1: 
            for p in pin:
               return  (self.read_chip('IODIR') & self.pin_adr(p)) == self.pin_adr(p)
         if not len(pin):            #if no pin passed as parameters, 
            pin=range(0,16)
         out_str=''  
         for p in pin:
            out_str+=str('\nPin %d chip GPIO %s or %d output %s ' % (p, bin(self.pin_adr(p)), self.pin_adr(p), ((self.read_chip('IODIR') & self.pin_adr(p)) == self.pin_adr(p) )))
         return out_str
      except:
         return str('is_input error', pin)  
   
   
#                    check if PIN is IN, returns True if pin is INPUT and is active
   def is_input_active(self, pin):
      try:
         if (self.read_chip('IODIR') & self.pin_adr(pin)) == self.pin_adr(pin):
            return (self.read_chip('GPIO') & self.pin_adr(pin)) == self.pin_adr(pin)
         else:
            return False
      except:
         return str(' is_input_active error', str(pin))  
      
               
                           # returning status of and if Output. reverse logic handled in Relay classs
   def is_output_on(self,pin):
      if self.is_output(pin):
         return (( self.read_chip('OLAT') & self.pin_adr(pin) ) == self.pin_adr(pin))




######################################################################################
#end of Class def
######################################################################################





