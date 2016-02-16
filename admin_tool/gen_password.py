#! /usr/bin/python

import random


elements="abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"

limit = len(elements) - 1

count=0
random_passwd_str=""
while count < 16:
	random_passwd_str += elements[random.randint(0,limit)]
	count += 1

print random_passwd_str

