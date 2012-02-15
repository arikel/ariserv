#!/usr/bin/env python
######################
#
# Python Mail Bot
# By Christopher Steffen
# (C) Copyright Christopher Steffen April 2009
#		ALL RIGHTS RESERVED
#
# The purpose of this bot is to perform various functions
# in response to emails the bot receives. Only emails that
# are from registered users (or are registrations) are
# allowed through, and they must match certain patterns.
# All other emails are deleted unread.
#
######################

import sys, email, smtplib, poplib, time, socket, cPickle, os
from email.MIMEText import MIMEText

###
# Change these to reflect your email settings
###
pophost = 'pop.server.com'
smtphost = 'smtp.server.com'
username = 'bot@server.com'
password = 'secretpassword'
mailfrom = "Python Bot <%s>" % (username)

wait = 5﻿	#wait time in seconds between checking the mail

welcomemsg = """
Python Mail Bot by Christopher Steffen
(C)Copyright Christopher Steffen April 2009 All Rights Reserved
"""

def sendfortune(mfrom):
﻿	f = os.popen('fortune')
﻿	msg = "Here is your fortune:\n---------------------\n"
﻿	msg += ''.join(f.readlines())
﻿	sendmsg('Your fortune!',msg,mfrom)

def admin(mfrom):
﻿	### Determine if the email address is an admin
﻿	try:
﻿	﻿	f = open("admins.dat","r")
﻿	﻿	p = cPickle.Unpickler(f)
﻿	﻿	admins = p.load()
﻿	﻿	f.close()
﻿	﻿	if mfrom in admins:
﻿	﻿	﻿	return 1
﻿	﻿	else:
﻿	﻿	﻿	return 0
﻿	except:
﻿	﻿	### THERE IS NO ADMINS FILE
﻿	﻿	f = open("admins.dat","w")
﻿	﻿	p = cPickle.Pickler(f)
﻿	﻿	admins = [mfrom,]
﻿	﻿	p.dump(admins)
﻿	﻿	f.close()
﻿	﻿	print "First admin added: %s" % (mfrom)
﻿	﻿	return 1
﻿	return 0

def registered(mfrom):
﻿	### Determine if the email address matches someone we know.
﻿	try:
﻿	﻿	f = open("users.dat","r")
﻿	﻿	p = cPickle.Unpickler(f)
﻿	﻿	users = p.load()
﻿	﻿	f.close()
﻿	﻿	if mfrom in users:
﻿	﻿	﻿	return 1
﻿	﻿	else:
﻿	﻿	﻿	return 0
﻿	except:
﻿	﻿	### THERE IS NO USERS FILE
﻿	﻿	f = open("users.dat","w")
﻿	﻿	p = cPickle.Pickler(f)
﻿	﻿	users = [mfrom,]
﻿	﻿	p.dump(users)
﻿	﻿	f.close()
﻿	﻿	print "First user added: %s" % (mfrom)
﻿	﻿	return 1
﻿	return 0

def listapp(mfrom):
﻿	try:
﻿	﻿	f = open("applicants.dat","r")
﻿	﻿	p = cPickle.Unpickler(f)
﻿	﻿	applicants = p.load()
﻿	﻿	f.close()
﻿	except:
﻿	﻿	### No applicants
﻿	﻿	return 0
﻿	if applicants:
﻿	﻿	msg = "Current applicants:\n-------------------\n"
﻿	﻿	for x in range(0,len(applicants)):
﻿	﻿	﻿	msg += "%s - %s" % (x,applicants[x])
﻿	﻿	msg += "\n-------------------\nReply with *APPROVE* X or *DENY* X to approve or deny applicant X (where X is the number of the applicant)."
﻿	﻿	sendmsg('Current list of applicants',msg,mfrom)
﻿	﻿	return 1
﻿	else:
﻿	﻿	sendmsg('No applicants.','There are currently no applicants awaiting approval.',mfrom)
﻿	﻿	return 1

def delapp(user):
﻿	## delete an applicant from the list
﻿	try:
﻿	﻿	f = open("applicants.dat","r")
﻿	﻿	p = cPickle.Unpickler(f)
﻿	﻿	applicants = p.load()
﻿	﻿	f.close()
﻿	except:
﻿	﻿	print "Error reading applicants file!"
﻿	﻿	return 0
﻿	if user in applicants:
﻿	﻿	# delete user from applicants list
﻿	﻿	applicants.remove(user)
﻿	else:
﻿	﻿	print "User %s not in applicants list." % (user)
﻿	﻿	return 1
﻿	try:
﻿	﻿	f = open("applicants.dat","w")
﻿	﻿	p = cPickle.Pickler(f)
﻿	﻿	p.dump(applicants)
﻿	﻿	f.close()
﻿	﻿	print "User %s removed from applicants list." % (user)
﻿	﻿	return 1
﻿	except:
﻿	﻿	print "Unable to remove user %s from applicants list!" % (user)
﻿	﻿	return 0

def adduser(user):
﻿	try:
﻿	﻿	f = open("users.dat","r")
﻿	﻿	p = cPickle.Unpickler(f)
﻿	﻿	users = p.load()
﻿	﻿	f.close()
﻿	except:
﻿	﻿	print "Error reading userfile!"
﻿	﻿	return 0
﻿	if user in users:
﻿	﻿	print "User %s already exists." % (user)
﻿	﻿	return 1
﻿	else:
﻿	﻿	users.append(user)
﻿	﻿	f = open("users.dat","w")
﻿	﻿	p = cPickle.Pickler(f)
﻿	﻿	p.dump(users)
﻿	﻿	f.close()
﻿	﻿	return 1

def denyapp(mfrom,subj):
﻿	print "Admin %s attempting to deny an applicant." % (mfrom)
﻿	subj = subj.replace("*DENY*",'')
﻿	subj = subj.replace(' ','')
﻿	try:
﻿	﻿	f = open("applicants.dat","r")
﻿	﻿	p = cPickle.Unpickler(f)
﻿	﻿	applicants = p.load()
﻿	﻿	f.close()
﻿	except:
﻿	﻿	sendmsg('No applicants!','There are no applicants to deny!',mfrom)
﻿	﻿	print "Applicants file doesn't exist. No applicants to deny."
﻿	if int(subj) > (len(applicants) - 1):
﻿	﻿	print "Applicant number out of range."
﻿	﻿	sendmsg('Applicant nonexistant.','That applicant does not exist.',mfrom)
﻿	elif applicants[int(subj)]:
﻿	﻿	if delapp(applicants[int(subj)]):
﻿	﻿	﻿	print "Applicant %s denied." % (applicants[int(subj)])
﻿	﻿	﻿	sendmsg('Applicant denied.','The applicant you specified has been denied registration.',mfrom)
﻿	﻿	﻿	sendmsg('Registration denied.','Your registration has been denied.',applicants[int(subj)])
﻿	﻿	else:
﻿	﻿	﻿	print "Error denying applicant %s." % (applicants[int(subj)])
﻿	﻿	﻿	sendmsg('Error denying applicant.','There was an error denying the applicant.',mfrom)
﻿	else:
﻿	﻿	print "Applicant %s does not exist." % (applicants[int(subj)])
﻿	﻿	sendmsg('Error denying applicant.','Applicant does not exist.',mfrom)

def approveapp(mfrom,subj):
﻿	print "Admin %s attempting to approve an applicant." % (mfrom)
﻿	subj = subj.replace("*APPROVE*",'')
﻿	subj = subj.replace(' ','')
﻿	try:
﻿	﻿	f = open("applicants.dat","r")
﻿	﻿	p = cPickle.Unpickler(f)
﻿	﻿	applicants = p.load()
﻿	﻿	f.close()
﻿	except:
﻿	﻿	sendmsg('No applicants!','There are no applicants to approve!',mfrom)
﻿	﻿	print "Applicants file doesn't exist. No applicants to approve."
﻿	if int(subj) > (len(applicants) - 1):
﻿	﻿	print "Applicant number out of range."
﻿	﻿	sendmsg('Applicant nonexistant.','That applicant does not exist.',mfrom)
﻿	elif applicants[int(subj)]:
﻿	﻿	## they exist, add 'em
﻿	﻿	if adduser(applicants[int(subj)]):
﻿	﻿	﻿	if delapp(applicants[int(subj)]):
﻿	﻿	﻿	﻿	print "Applicant %s approved." % (applicants[int(subj)])
﻿	﻿	﻿	﻿	sendmsg('Applicant approved!','The applicant you specified is now a registered member.',mfrom)
﻿	﻿	﻿	﻿	sendmsg('Your account is now active!','Your registration has been approved by an admin.',applicants[int(subj)])
﻿	﻿	﻿	else:
﻿	﻿	﻿	﻿	print "Error approving applicant %s." % (applicants[int(subj)])
﻿	﻿	﻿	﻿	sendmsg('Error approving applicant.','There was an error approving the applicant.',mfrom)
﻿	﻿	else:
﻿	﻿	﻿	print "Error approving applicant."
﻿	﻿	﻿	sendmsg('Error approving applicant.','There was an error approving the applicant.',mfrom)
﻿	else:
﻿	﻿	print "Applicant does not exist."
﻿	﻿	sendmsg('Applicant nonexistant!','Applicant does not exist!',mfrom)

def addapplicant(mfrom):
﻿	### Add an applicant to the applicants list
﻿	try:
﻿	﻿	f = open("applicants.dat","r")
﻿	﻿	p = cPickle.Unpickler(f)
﻿	﻿	applicants = p.load()
﻿	﻿	f.close()
﻿	﻿	if mfrom in applicants:
﻿	﻿	﻿	print "Applicant already exists!"
﻿	﻿	﻿	sendmsg('You already applied!','Please be patient, our admins will see to your application as soon as possible. Do not attempt to register again.',mfrom)
﻿	﻿	else:
﻿	﻿	﻿	applicants.append(mfrom)
﻿	﻿	﻿	f = open("applicants.dat","w")
﻿	﻿	﻿	p = cPickle.Pickler(f)
﻿	﻿	﻿	p.dump(applicants)
﻿	﻿	﻿	f.close()
﻿	﻿	﻿	print "New applicant: %s" % (mfrom)
﻿	﻿	﻿	sendmsg('Your application has been received.','In order to become a member, your application must be accepted by an admin. Please be patient!',mfrom)
﻿	except:
﻿	﻿	### FILE DOESN'T EXIST
﻿	﻿	f = open("applicants.dat","w")
﻿	﻿	p = cPickle.Pickler(f)
﻿	﻿	applicants = [mfrom,]
﻿	﻿	p.dump(applicants)
﻿	﻿	f.close()
﻿	﻿	print "New applicant: %s" % (mfrom)
﻿	﻿	sendmsg('Your application has been received.','In order to become a member, your application must be accepted by an admin. Please be patient!',mfrom)

def sendmsg(subject,body,to):
﻿	message = """To: %s
From: %s
Subject: %s

%s
""" % (to, mailfrom, subject, body)
﻿	try:
﻿	﻿	s = smtplib.SMTP(smtphost)
﻿	﻿	try:
﻿	﻿	﻿	s.login(username, password)
﻿	﻿	except smtplib.SMTPException, e:
﻿	﻿	﻿	print "Authentication failure (SMTP)."
﻿	﻿	﻿	print e
﻿	﻿	else:
﻿	﻿	﻿	s.sendmail(mailfrom, to, message)
﻿	except (socket.gaierror, socket.error, socket.herror, smtplib.SMTPException), e:
﻿	﻿	print "!!! ERROR SENDING MAIL !!!"
﻿	﻿	print e
﻿	else:
﻿	﻿	print "Mail response sent successfully."


##############
# THE MEAT OF THE PROCESSOR
##############
def process(msg):
﻿	subject = "untitled"
﻿	body = "empty"
﻿	if msg.is_multipart():
﻿	﻿	for item in msg.get_payload():
﻿	﻿	﻿	if 'content-type' in msg:
﻿	﻿	﻿	﻿	if 'text/plain' in msg['content-type']:
﻿	﻿	﻿	﻿	﻿	body = msg.get_payload(item)
﻿	else:
﻿	﻿	body = msg.get_payload()
﻿	if 'subject' in msg:
﻿	﻿	subject = msg['subject']
﻿	if 'from' in msg:
﻿	﻿	emailfrom = msg['from']
﻿	
﻿	###
﻿	# This is where we figure out what kind of message it is and
﻿	# process it accordingly
﻿	###
﻿	if registered(emailfrom):
﻿	﻿	### NON-ADMIN FUNCTIONS
﻿	﻿	if "*FORT*" in subject:
﻿	﻿	﻿	#fortune
﻿	﻿	﻿	print "Requesting fortune for %s..." % (emailfrom)
﻿	﻿	﻿	### send 'em a fortune
﻿	﻿	﻿	sendfortune(emailfrom)
﻿	﻿	elif "*REG*" in subject:
﻿	﻿	﻿	### USER TRYING TO REGISTER AGAIN
﻿	﻿	﻿	print "Re-Registration attempt by %s..." % (emailfrom)
﻿	﻿	﻿	sendmsg('You already registered!','This email has already been registered with the system.',emailfrom)
﻿	﻿	
﻿	﻿	### ADMIN FUNCTIONS
﻿	﻿	elif admin(emailfrom):
﻿	﻿	﻿	if "*Q*" in subject:
﻿	﻿	﻿	﻿	#quit
﻿	﻿	﻿	﻿	print "Shutdown command received from %s..." % (emailfrom)
﻿	﻿	﻿	﻿	sendmsg('PyBot Terminated','Python Email Bot shut down successfully. No further communications will be made.',emailfrom)
﻿	﻿	﻿	﻿	print "System shutdown..."
﻿	﻿	﻿	﻿	sys.exit(0)
﻿	﻿	﻿	elif "*LSAPP*" in subject:
﻿	﻿	﻿	﻿	# list applicants
﻿	﻿	﻿	﻿	if listapp(emailfrom):
﻿	﻿	﻿	﻿	﻿	print "Applicant list sent to %s" % (emailfrom)
﻿	﻿	﻿	﻿	else:
﻿	﻿	﻿	﻿	﻿	print "Applicant list empty, %s informed." % (emailfrom)
﻿	﻿	﻿	﻿	﻿	sendmsg('No Applicants','There are no applicants at this time.',emailfrom)
﻿	﻿	﻿	elif "*APPROVE*" in subject:
﻿	﻿	﻿	﻿	#approve applicant
﻿	﻿	﻿	﻿	approveapp(emailfrom,subject)
﻿	﻿	﻿	elif "*DENY*" in subject:
﻿	﻿	﻿	﻿	#deny applicant
﻿	﻿	﻿	﻿	denyapp(emailfrom,subject)

﻿	﻿	else:
﻿	﻿	﻿	# unwanted mail, delete
﻿	﻿	﻿	print "Unsolicited mail from %s, deleting..." % (emailfrom)
﻿	﻿	
﻿	﻿	
﻿	else:
﻿	﻿	### NON-REGISTERED FUNCTIONS
﻿	﻿	if "*REG*" in subject:
﻿	﻿	﻿	### REGISTERING
﻿	﻿	﻿	print "Registration request by %s..." % (emailfrom)
﻿	﻿	﻿	addapplicant(emailfrom)
﻿	﻿	else:
﻿	﻿	﻿	# unwanted mail, delete
﻿	﻿	﻿	print "Unsolicited mail from %s, deleting..." % (emailfrom)


###
# BEGIN MAIN LOOP
###
print "-"*72
print welcomemsg
print "-"*72
print "\nStarting main loop..."

while 1:
﻿	p = poplib.POP3(pophost)
﻿	try:
﻿	﻿	p.user(username)
﻿	﻿	p.pass_(password)
﻿	﻿	status = p.stat()
﻿	except poplib.error_proto, e:
﻿	﻿	print "Login failed: ",e
﻿	﻿	sys.exit(1)
﻿	
﻿	if status[0]:
﻿	﻿	for item in p.list()[1]:
﻿	﻿	﻿	number,octets = item.split(' ')
﻿	﻿	﻿	print "Downloading message (%s bytes)..." % (octets)
﻿	﻿	﻿	lines = p.retr(number)[1]
﻿	﻿	﻿	msg = email.message_from_string("\n".join(lines))
﻿	﻿	﻿	p.dele(number)
﻿	﻿	﻿	process(msg)
﻿	p.quit()
﻿	time.sleep(wait)
