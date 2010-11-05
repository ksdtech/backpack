#!/usr/bin/env python
#----------------------------------------------------------------------------
# Name:         backpack.py
# Purpose:      An AFP network share front-end
#
# Author:       Andrew Korff
#----------------------------------------------------------------------------

# NOTE: this sample requires wxPython 2.6 or newer

# import the wxPython GUI package
import wx
import subprocess #Not available in 10.4
import os
import plistlib
import base64
import sys


class MyFrame(wx.Frame):
	""" We simply derive a new class of Frame. """
	def __init__(self, parent, title):

		self.cachedPlistLoc = os.path.expanduser("~/Library/Caches/org.kentfieldschools.cache.plist")

		wx.Frame.__init__(self, parent, title=title, size=(400,200), style=wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN)
		self.Centre(wx.BOTH)

		# First, before we even do any windowing at all, we'll check to see if the user has already mounted their backpack.
		# If they have, then we should just open that window and exit.
		if os.path.exists(self.cachedPlistLoc):
			try:
				cachedPlist = plistlib.readPlist(self.cachedPlistLoc)
			except TypeError as err:
				print "Unable to read Cached Plist: {0}".format(err)
			else:
				mntPoint = '/Volumes/%s' % base64.b64decode(cachedPlist["cachedA"])
				if os.path.isdir(mntPoint): # Check whether mountpoint already exists, in case student is running it again.
					if os.path.ismount(mntPoint): # Check it it's actually a mountpoint.
						subprocess.check_call(['open', mntPoint]) # If so, then why don't we just open that thing up?
						self.closeApp(None)


		panel = wx.Panel(self, -1)
		self.labelName = wx.StaticText(panel, -1, "Name:")
		self.labelPassword = wx.StaticText(panel, -1, "Password:", style=wx.ALIGN_RIGHT)
		self.nameCtrl = wx.TextCtrl(panel, -1, "", size=(200, -1))
		self.passCtrl = wx.TextCtrl(panel, -1, "", size=(200, -1), style=wx.TE_PASSWORD)
		self.panel = panel
		connectButton = wx.Button(self, label="Connect")
		connectButton.SetDefault()
		cancelButton = wx.Button(self, label="Cancel")
		self.labelInstructions = wx.StaticText(self, -1, "Enter your name and password for your Backpack.", style=wx.ALIGN_LEFT)
		self.labelInstructions.Wrap(300)



		# A sizer for the instructions
		instructionSizer = wx.FlexGridSizer(1, 1, 15, 8)
		instructionSizer.Add(self.labelInstructions, flag=wx.ALIGN_RIGHT)
		# A sizer for layout of the inputs
		inputSizer = wx.FlexGridSizer(2, 2, 15, 8)
		inputSizer.Add(self.labelName, flag=wx.ALIGN_RIGHT)
		inputSizer.Add(self.nameCtrl)
		inputSizer.Add(self.labelPassword, flag=wx.ALIGN_RIGHT)
		inputSizer.Add(self.passCtrl)
		# A sizer for the buttons
		buttonSizer = wx.FlexGridSizer(1, 2, 15, 8)
		buttonSizer.Add(cancelButton)
		buttonSizer.Add(connectButton)
		# A sizer to hold everything together.
		border = wx.BoxSizer(wx.VERTICAL)
		border.Add(instructionSizer, 0, wx.ALL, 15)
		border.Add(inputSizer, 0, wx.ALL, 15)
		border.Add(buttonSizer, 0, wx.BOTTOM | wx.LEFT | wx.RIGHT | wx.ALIGN_RIGHT, 15)
		panel.SetSizerAndFit(border)
		self.Fit()

		self.Bind(wx.EVT_BUTTON, self.connectToShare, connectButton)
		self.Bind(wx.EVT_BUTTON, self.closeApp, cancelButton)

		self.Show(True)


	def closeApp(self, event):
		self.Close(True)


	def postMessage(self, messageTuple):
#		print self.nameCtrl.GetLineText(0)
		dlg = wx.MessageDialog(self, messageTuple[1], messageTuple[0], style=wx.OK | wx.ICON_INFORMATION)
		dlg.ShowModal() # Show it
		dlg.Destroy()

	def obtainHomeServer(self, uid): 
		try:
			ldapResult = subprocess.Popen(['ldapsearch', '-h', '10.4.51.70', '-x', '-b', "cn=users,dc=yp,dc=kentfieldschools,dc=org", 'uid=%s' % uid, 'apple-user-homeurl'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		except OSError as (errno, strerror):
			print "OS Error! ({0}): {1}".format(errno, strerror) # This doesn't normally seem to get called.
		except subprocess.CalledProcessError as err:
			print "CalledProcessError! {0}".format(err)
		else:
			# "bfs.kentfieldschools." in base64: YmZzLmtlbnRmaWVsZHNjaG9vbHMub
			# "kfs.kentfieldschools." in base64: a2ZzLmtlbnRmaWVsZHNjaG9vbHMub
			ldapString = ldapResult.communicate()[0]
			if (ldapString.find("YmZzLmtlbnRmaWVsZHNjaG9vbHMub") >= 0):
				return "bfs"
			elif (ldapString.find("a2ZzLmtlbnRmaWVsZHNjaG9vbHMub") >= 0):
				return "kfs"
			else:
				return False


	def connectToShare(self, event):
		userName = self.nameCtrl.GetLineText(0)
		password = self.passCtrl.GetLineText(0)
		if (len(userName) == 0) or (len(password) == 0):
			self.postMessage(("You entered an invalid username or password.", "Please try again."))
		else:
			mntPoint = '/Volumes/%s' % userName
			if os.path.isdir(mntPoint): # Check whether mountpoint already exists, in case student is running it again.
				if os.path.ismount(mntPoint): # Check if it's actually a mountpoint.
					subprocess.check_call(['open', mntPoint]) # If so, then why don't we just open that thing up?
					self.closeApp(None)
				else: # Otherwise, perhaps we didn't clean up after the last attempt.  Shouldn't be possible.
					self.postMessage(("Empty Backpack Mountpoint.", "Please contact the System Administrator."))
					# This might be a bad idea.  Should probably consider consequences first.
# 					try:
# 						subprocess.check_call(["rm", "-df", mntPoint])
# 					except OSError as (errno, strerror):
# 						print "OS Error! ({0}): {1}".format(errno, strerror)
# 					except subprocess.CalledProcessError as err:
# 						print "CalledProcessError! {0}".format(err.returncode)
# 					else: # Go on about the rest of the business.
			else: # The mountpoint doesn't exist yet!  Hurray!  All is going according to plan.
				homeServer = self.obtainHomeServer(userName) # Figure out if account is hosted on bfs or kfs.
				if homeServer:
					try:
						subprocess.check_call(['mkdir', mntPoint]) # Create the Mountpoint
						subprocess.check_call(['/sbin/mount_afp', 'afp://%s:%s@%s/%s' % (userName, password, homeServer, userName), mntPoint])
					except OSError as (errno, strerror):
						print "OS Error! ({0}): {1}".format(errno, strerror) # This doesn't normally seem to get called.
					except subprocess.CalledProcessError as err:
						print "CalledProcessError! {0}".format(err)
						if err.returncode > 1: # We should clean up the mountpoint before the student tries to mount again. (Assuming only mkdir will raise 1...)
							try:
								subprocess.check_call(['rm', '-df', mntPoint])
							except OSError as (errno, strerror):
								print "OS Error removing {2}! ({0}): {1}".format(errno, strerror, mntPoint) # This doesn't normally seem to get called.
							except subprocess.CalledProcessError as err:
								print "CalledProcessError! {0}".format(err.returncode)
						if err.returncode == 1: # Could be because the home already exists, somehow.
							self.postMessage(("Unable to create Backpack Mountpoint.", "Please contact the System Administrator."))
						elif err.returncode == 2:
							self.postMessage(("Unable to mount Backpack at %s." % mntPoint, "Please contact the System Administrator."))
						elif err.returncode == 97:
							self.postMessage(("You entered an invalid username or password.", "Please try again."))
						elif err.returncode == 120:
							self.postMessage(("You entered an invalid username or password.", "Please try again."))
						elif err.returncode == 211:
							self.postMessage(("Unable to contact server.", "Please verify your network connection and try again."))
						else:
							self.postMessage(("There was an error mounting your Backpack.", "Please contact the System Administrator."))
					else: # We were successfully able to create the mountpoint and mount the share!
						# We should store the username and password into a plist in the ~/Library/Caches folder.
						# Should we check to see if it already exists?  No, should probably have done that earlier.
						credDict = dict(cachedA = base64.b64encode(userName), cachedB = base64.b64encode(password), cachedC = base64.b64encode(homeServer))
						credentialsPlist = open(self.cachedPlistLoc, "w")
						plistlib.writePlist(credDict, credentialsPlist)
						credentialsPlist.close()
						# This is where we should quit!
						subprocess.check_call(['open', mntPoint])
						self.closeApp(None)
				else:
					self.postMessage(("You entered an invalid username or password.", "Please try again."))

	
	
	

app = wx.App(False)
frame = MyFrame(None, 'Backpack')
app.MainLoop()