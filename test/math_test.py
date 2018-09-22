#!/usr/bin/env python

import math, time

maxlevel = 255

lights = [26,27,28,29,30,31,3,2,1,4,5,6,10,9,11,12,13,14,15,16,19,18,17,20,21,22,24,23,25]

for j in range((len(lights))):
   for i in lights:
      l = (maxlevel/2)*math.sin(time.time()*(j+maxlevel))+maxlevel/2
      print(l),
   print()

