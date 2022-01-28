#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import configparser
from time import sleep, time, perf_counter
from math import log
from red_diode_clases import MCP, Butt, Relay, VButt
from red_diode_MTQQ_class import MTQQ_client 
from threading import Thread, Event, currentThread, Timer
#


                        #depending on the cycle/change version picking the way binary status is changed 
                        #seq 1 100  010 001 000 cycle
                        #seq 2 100 010 110 001 101 011 111 000 cycle
                        #seq 3 000 100 110 111 000 cycle
                        #seq 4 all on/off - if at least one is on all will be off first, than next push will on all 
                        #seq 5 all off
                        #seq 6 all on
                        #seq 7 do nothing
                        #con_1 for contactrons: was close: open. was open: keeps it open

def seq_1(outputs):     #seq 1 100  010 001 000 cycle
   Led_bit=0                     #set 0 value for start
          #set binary lenght trim (this have to be 0b0111 for 3 elements, 0b01111 for 4 elemnts etc.)   
   n=0
   for output in outputs:        #checking which outputs are on and keep this in Led_bit
      if Relay.relay(output).state:
         Led_bit+=2**n
      n+=1
   Led_bit = ((Led_bit << 1 )  if Led_bit > 0 else 1)
   Led_bit = Led_bit & (2**len(outputs) -1) 
   n=0
#   print('test seq1 {} {:>16b}'.format(outputs, Led_bit))
   for output in outputs:
      if Led_bit & (2**n): Relay.relay(output).on()
      else: Relay.relay(output).off()
      n+=1


def seq_2(outputs):     #seq 2 100 010 110 001 101 011 111 000 cycle
   Led_bit=0                     #set 0 value for start
          #set binary lenght trim (this have to be 0b0111 for 3 elements, 0b01111 for 4 elemnts etc.)   
   n=0
   for output in outputs:
      if Relay.relay(output).state:
         Led_bit+=2**n
      n+=1
#   Led_bit += 1
   Led_bit = (Led_bit+1 ) & (2**len(outputs) -1) 
   n=0
   for output in outputs:
      if Led_bit & (2**n): Relay.relay(output).on()
      else: Relay.relay(output).off()
      n+=1
   
   
def seq_3(outputs):     #seq 3 000 100 110 111 000 cycle
   Led_bit=0                     #set 0 value for start
          #set binary lenght trim (this have to be 0b0111 for 3 elements, 0b01111 for 4 elemnts etc.)   
   n=0
   for output in outputs:
      if Relay.relay(output).state:
         Led_bit+=2**n
      n+=1
   Led_bit = (Led_bit<<1)+1 if ((Led_bit << 1) < (2**len(outputs))) else 0
   Led_bit = Led_bit & (2**len(outputs) -1) 
   n=0
   for output in outputs:
      if Led_bit & (2**n): Relay.relay(output).on()
      else: Relay.relay(output).off()
      n+=1
   
   
def seq_4(outputs):     #seq 4 all on/off 
   Led_bit=0                     #set 0 value for start
          #set binary lenght trim (this have to be 0b0111 for 3 elements, 0b01111 for 4 elemnts etc.)   
   n=0
   for output in outputs:
      if Relay.relay(output).state:
         Led_bit+=2**n
      n+=1
   Led_bit = (2**len(outputs) -1) if Led_bit == 0 else 0
#   Led_bit = Led_bit & (2**len(outputs) -1) 
   n=0
   for output in outputs:
      if Led_bit & (2**n): Relay.relay(output).on()
      else: Relay.relay(output).off()
      n+=1

def seq_5(outputs):     #seq 5 all off
   for output in outputs:
      Relay.relay(output).off()


def seq_6(outputs):     #seq 6 all on
   for output in outputs:
      Relay.relay(output).on()

def seq_7(outputs):  #do exactly nothing
   pass

def seq_8(data):  #delay action, parameters as list: delay time in seconds, action, outputs
   if len(data)> 1:
      delay = data[0]
      outputs = data[1:]
   else: return 0
   sleep(delay)
   v_pres(outputs)

def v_pres(param):   #setting the outputs for virtual button. Par action: on, off, togle + output list
   if len(param)>0:
      action=param[0]
      outputs=param[1:]
   for out in outputs:
      try:
         {
         'on': Relay.relay(out).on,
         'off': Relay.relay(out).off,
         'togle': Relay.relay(out).togle}[action]()
      except:
         print('v_pres error', out)

def Send_alarm(what,when):
   print('SEND ALARM do passssss only')
   pass
   

#def mov_detected( ts,ev, act1, act2, outputs):   #setting the outputs from virtua button
#   #use as thread:
#   #md=Thread (name='self.name', target=mov_detected, 
#   #                 args=(waitingTime, self.Event, action1, action2, self.call-outputs))
#   #md.setDaemon(True)
#   #md.start()
#   print('did I reach out here?')
#   while True:
#      ev.wait()
#      if ev.isSet(): 
#         print('move isSet '.format())
#         v_pres([act1] + outputs)
#         sleep(ts)
#         if not ev.isSet():
#            v_pres([act2] + outputs)
#            print('move NOT isSet')
#
#   while True:
#      ev.wait()
#      if ev.isSet(): 
#         print('move isSet')
#         v_pres(['on'] + outputs)
#         sleep(ts)
#      else: 
#         v_pres(['off'] + outputs)
#         print('move NOT isSet')
#
#
#def con_1(outputs):     #con_1 for contactrons: 
#   Led_bit=0                     #set 0 value for start
#          #set binary lenght trim (this have to be 0b0111 for 3 elements, 0b01111 for 4 elemnts etc.)   
#   n=0
#   for output in outputs:
#      if Relay.relay(output).state:
#         Led_bit+=2**n
#      n+=1
#   Led_bit = (2**len(outputs) -1) if Led_bit == 0 else 0
#   Led_bit = Led_bit & (2**len(outputs) -1) 
#   n=0
#   for output in outputs:
#      if Led_bit & (2**n): Relay.relay(output).on()
#      else: Relay.relay(output).off()
#      n+=1


def read_config_chip():
   try:
      CfFile = '/home/pi/Python/red_diode.cfg'
      confign_str = configparser.ConfigParser(allow_no_value=True)
      confign_str.read(CfFile)
      print('config read OK')
   except:
      print('something wrong with /home/pi/Python/red_diode.cfg')
      
   #setting chips
   for ch in confign_str['Chips']['MCP'].split('\n'): 
      el=ch.split() 
      #based on cfg file creating MCP objects representing installed chips
      exec(str('MCP("%s", %s, %s )' % (str(el[0]), str(el[1]), str(el[2]))))
   

               #reading config file and setting up chips and (tbd)
def read_config():
   try:
      CfFile = '/home/pi/Python/red_diode.cfg'
      confign_str = configparser.ConfigParser(allow_no_value=True)
      confign_str.read(CfFile)
      print('config read OK')
   except:
      print('something wrong with /home/pi/Python/red_diode.cfg')
      
   #setting chips
   for ch in confign_str['Chips']['MCP'].split('\n'): 
      el=ch.split() 
      #based on cfg file creating MCP objects representing installed chips
      exec(str('MCP("%s", %s, %s )' % (str(el[0]), str(el[1]), str(el[2]))))
   
   #setting RELAY OUTPUTS
   for ch in confign_str['Relay']['Pins_relay'].split('\n'): 
      el=ch.split() 
      pwm, rev = False, False 
      for ell in el:
         if ell=='PWM': pwm=True
         if ell=='REV': rev=True
      #based on cfg file creating Relay objects representing output devices and they connection to physical relay
      print('Relay("%s", %s, "%s", "%s", %s, %s)' % (str(el[0]), str(el[1]), str(el[2]), str(el[3]), pwm, rev))
      exec(str('Relay("%s", %s, "%s", "%s", %s, %s)' % (str(el[0]), str(el[1]), str(el[2]), str(el[3]), pwm, rev)))
   
   #setting button, contactron INPUTS
   for ch in confign_str['Buttons']['butt'].split('\n'):
      el=ch.split() 
      CON_s = True if el[-1] == 'CON' else False
      MOV_s = True if el[-1] == 'MOV' else False
      l = len(el)-1 if ( CON_s or MOV_s ) else len(el)
      out_s=[]
      for s in el[3:l]: out_s.append(s)
         #based on cfg file creating Butt objects representing inputs and in devices and they connection to MCP chips
      print('Butt("%s", "%s", %s, %s, %s, %s)' % (el[0], el[1], el[2], out_s, CON_s, MOV_s))
      exec(str('Butt("%s", "%s", %s, %s, %s, %s)' % (el[0], el[1], el[2], out_s, CON_s, MOV_s)))
      
   #setting button action sequence
   for ch in confign_str['Buttons']['sequence'].split('\n'):
      el=ch.split()
      try:           #assigning function or actions to buttons
         Butt.Butt_instn[el[0]].action1={
               's1':seq_1,
               's2':seq_2,
               's3':seq_3,
               's4':seq_4,
               's5':seq_5,
               's6':seq_6,
               's7':seq_7,
               's8':seq_8,
               'v1':v_pres #mov_detected
               }[el[1]]
         print('button sequence {} {}'.format(Butt.Butt_instn[el[0]].name, el[1] ), Butt.Butt_instn[el[0]].action1 )
         
         Butt.Butt_instn[el[0]].action2={
               's1':seq_1,
               's2':seq_2,
               's3':seq_3,
               's4':seq_4,
               's5':seq_5,
               's6':seq_6,
               's7':seq_7,
               's8':seq_8,
               'v1':seq_7
               }[el[2]]
         print('button sequence {} {}'.format(Butt.Butt_instn[el[0]].name, el[2] ), Butt.Butt_instn[el[0]].action2 )
            
      except:
         print('fail sequence setup for {} {}'.format(el[0],el[1],el[2] ))
         
   #setting vbutt (virtual button) action sequence
   # v_button:name, procedure , optional parameters for procedure
   #parameters for procedure v_press: 1st par: on, off , togle. following parameters are outputs name's
   for ch in confign_str['Buttons']['vbutt'].split('\n'):
      par=[]
      el=ch.split()
      l = len(el)
      if l > 2: 
         for e in el[2:l]: par.append(e)
         
      print('VButt("%s", %s , %s)' % (str(el[0]), str(el[1]),par))
      exec(str('VButt("%s", %s, %s)' % (str(el[0]), str(el[1]),par)))
      



def Out_map():     #help mapping chip pins to relay channels and physical outputs/receivers
   print('\n\n')
   conf_str=''
   for key in MCP.MCP_instnc.keys():
      c=MCP.MCP_instnc[key]
#      for i in range(0,16):print(c.set_output_off(i), c, i),sleep(0.1)
      for i in range(0,16):
#         if c.is_output(i):
         c.set_output_off(i)
         c.set_output_on(i)
         print('\033[Achip %s pin %d enter relay number and name:' % (c.name, i),end="")
         con=input(' ')
         if con not in ('','0'): 
            print("\033[Achip %s pin %d relay %s                             \n" % (c.name,i,con))
            conf_str+=str(c.name)+' '+str(i)+' '+str(con)+' \n'
         c.set_output_off(i)
   print('\n\n')
   print(conf_str)


def In_map():     #help mapping chip pins to buttons and inputs
   print('push the button or close the contactron and type name')
   conf_str=''
   con=''
   while con!='END':
      for key in MCP.MCP_instnc.keys():
         c=MCP.MCP_instnc[key]
         read=c.read_chip('GPIO')
         if read != 0:
            print('\rchip {} pin {} pinadr {},           enter name'.format(c, round(log(read,2)),read ) ,end=" ")
            con=input(' ')
            if con not in ('','0','END'): 
               print('\033[Achip {} pin {} pinadr {}, name {}                     '.format(c, round(log(read,2)),read, con ))
               conf_str+=str(con)+' '+str(c.name)+' '+str(round(log(read,2)))+' '+' \n'
               print('push the button or close the contactron and type name\r', end=' ')
   print('\n\n')
   print(conf_str)


def tog(): # function changing outputs on/off - convenient for checking the configuration
   st=perf_counter()
   for key in Relay.Relay_instn.keys():
      Relay.Relay_instn[key].togle()
#      sleep(1)
   return (perf_counter() - st)

def r():    #function displaying inputs status
   for key in MCP.MCP_instnc.keys():
      c=MCP.MCP_instnc[key]
      print(c)
      print(c.read_chip('IODIR'),       c.read_chip('IPOL'),       c.read_chip('GPIO'))
      print(end='\n')

def all_off():
   for key in Relay.Relay_instn.keys():
      Relay.Relay_instn[key].off()


         
#INTFLAG	GPIO	INTCAP


##################################################################
#threads to manage buttons

##################################################################


                  #Bitwise bit removal ((~0b101 & 0b11111111) & 0b10101110) > '0b10101010'

def MCP_reading_thread(chips,):      #MCP chips thread that scans inputs
   t=perf_counter()           #previous time, to calculate time difference between events
   slpt=0.001               #0.01 byłosleeping time - experiment with values if events are mising, typically values 0.01-0.04, but....
   
   for c in chips.values():                   #loop initiate input iterators
      for b in c.inputs.values():
         if b.is_mov: 
            b.butt_action_iterator = b.motion_action((0,0,0))
         elif b.is_con:
            b.butt_action_iterator = b.contactron_action((0,0,0))
         else: 
            b.butt_action_iterator = b.butt_action((0,0,0))
         b.butt_action_iterator.send(None)
      
      #do testów jest for i, docelowo powinno być while True.
      # dla slpt = 0.01
      # 1000 000 (milion) to ponad doba
      # 1000 to 102s na PiZero
      # 600 to 64 sekundy
      # 3600 godzina 
      # dla slpt = 0.0001
      # 3000 to minuta 180 000 godzina 
   for i in range (0,2000):
      for c in chips.values():      #for every chip
         INTF, GPIO, INTCAP = c.read_chip('INTF'), c.read_chip('GPIO'),c.read_chip('INTCAP')
#         if  ( INTF & c.inputs_b)  or  ( GPIO & c.inputs_b ) or ( INTCAP & c.inputs_b ):
         if  ( INTF & c.inputs_b)  or  ( GPIO & c.inputs_b ) : #if inputs are active
#            print ('chip: {} INTFlag: {:>4x} GPIO: {:>16b} INCAP: {:>4x} IODIR: {:>4x} in: {} time: {:0.3f}'.format(c, INTF, GPIO, INTCAP, c.inputs_b, (c.inputs_b & GPIO), perf_counter()-t))
            
            try: 
#               print('test 1 {} {:>16b}'.format(c.inputs[INTF].name, INTF))
               c.inputs[INTF].butt_action_iterator.send( (INTF,GPIO,perf_counter()) )      #try engage iterator (if there is one active input on INTF, interupt registered)
            except:
                  for ip in c.inputs.values():  #for every active input
                     if ip.pin_b & GPIO:
                        try:
#                           print('test 2 {} {:>16b}'.format(ip.name, GPIO))
                           ip.butt_action_iterator.send( (INTF,GPIO,perf_counter()) )  #engage iterator
                        except:
                           pass
#                           print('test 3 {}'.format(ip.name))
         sleep(slpt)       #sleeps to slow down, can be change if events are missing. Rather make it bigger, even up to 0.3 but be carefull
   print(perf_counter()-t)



def main():
   
   read_config()   
   all_off()
   tog()
   sleep(1)
   tog()
   
   print("Setup ready")
   
   th_MCP1 = Thread (name='MCP1', target=MCP_reading_thread, args=( MCP.MCP_instnc ,) )
   th_MCP1.setDaemon(True)
   th_MCP1.start() 
   
   
   mqtt_obj=MTQQ_client({**Butt.Butt_instn, **VButt.Butt_instn})
   
   print('threads started')   
   th_MCP1.join()

   
   print("OK this is the end")
   all_off()
   print('threads ended')
   for key in MCP.MCP_instnc:                   #clean MCP's chips'
      MCP.MCP_instnc[key].clean()


      
if __name__ == "__main__":
   print("START")
   main()
   print("END")



