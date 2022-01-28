#!/usr/bin/python3
# -*- coding: UTF-8 -*-


import paho.mqtt.client as mqtt 

class MTQQ_client:
   
   #Class parameters
   broker_address = "localhost" 
   broker_port = 1883
   broker_keepalive = 60
   mtqqUname="rediode"
   mtqqPwd="rediode"
                        #all above to be in config file <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
   topic_list = []   #list of topics, from config file Buttons and Outputs
   
   
   def __init__(self, But):
#  But - buttons dictionary Butt.Butt_instn 
#, Reley dopisac do parametrów za self 
#      self.topic_list = htqq_topics_add(Butt)
#      self.topic_list = htqq_topics_add(Reley)
      self.butt = But
      MTQQ_client.broker_address = "localhost"  # to be from config file <<<<<<<<<<<<<<<
      MTQQ_client.broker_port = 1883            # to be from config file <<<<<<<<<<<<<<<
      MTQQ_client.broker_keepalive = 60         # to be from config file <<<<<<<<<<<<<<<
      self.client = mqtt.Client("red_diode") #create new instance  # check this MTQQ_name <<<<<
      self.client.username_pw_set(username="rediode",password="rediode")
      self.client.on_message=self.on_message_
      self.client.connect(MTQQ_client.broker_address, port=MTQQ_client.broker_port, keepalive=  MTQQ_client.broker_keepalive, bind_address="" )
      self.client.loop_start()
      self.client.subscribe("red")
#      self.subscribe()
   
   def __str__(self):
     return self.name
   
   def  htqq_topics_add(self, dic):
      for el in dic:
         if isinstance(dic[0],str):
            MTQQ_client.topic_list.append()
   
   def on_message_(self, client, userdata, message):
      self.messg=str(message.payload.decode("utf-8")) #message received 
      self.topic=message.topic #message topic
      self.qos=message.qos  #message qos
      self.retain=message.retain #message retain flag
      print("messg topic ", self.messg,self.topic)
      try:
         self.butt[self.messg].v_push()
      except:
         pass
      
      
      
