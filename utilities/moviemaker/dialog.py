#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import sys
import time

from PyQt4 import QtCore, QtGui

# Command arguments:

from optparse import OptionParser
Parser = OptionParser(usage="%prog [options]\ntype \"%prog -h\" for help", version="%prog 1.0")
Parser.add_option('-s', '--slate',           dest='slate',           type  ='string',     default='dailies_slate',help='Slate frame template')
Parser.add_option('-t', '--template',        dest='template',        type  ='string',     default='dailies',      help='Frame paint template')
Parser.add_option('--company',               dest='company',         type  ='string',     default='Company',      help='Company name')
Parser.add_option('--project',               dest='project',         type  ='string',     default='',             help='Project name')
Parser.add_option('-A', '--afanasy',         dest='afanasy',         action='store_true', default=False,          help='Send Afanasy job')
Parser.add_option(      '--afpriority',      dest='afpriority',      type  ='int',        default=-1,             help='Afanasy job priority')
Parser.add_option(      '--afmaxhosts',      dest='afmaxhosts',      type  ='int',        default=-1,             help='Afanasy job maximum hosts')
Parser.add_option(      '--afhostsmask',     dest='afhostsmask',     type  ='string',     default='',             help='Afanasy job hosts mask')
Parser.add_option(      '--afhostsmaskex',   dest='afhostsmaskex',   type  ='string',     default='',             help='Afanasy job exclude hosts mask')
Parser.add_option(      '--afdependmask',    dest='afdependmask',    type  ='string',     default='',             help='Afanasy job depend mask')
Parser.add_option(      '--afdependmaskgl',  dest='afdependmaskgl',  type  ='string',     default='',             help='Afanasy job global depend mask')
Parser.add_option(      '--afcapacity',      dest='afcapacity',      type  ='int',        default=-1,             help='Afanasy job tasks capacity')
Parser.add_option(      '--afpause',         dest='afpause',         action='store_true', default=False,          help='Start Afanasy job paused')
Parser.add_option('-D', '--debug',           dest='debug',           action='store_true', default=False,          help='Debug mode')

(Options, args) = Parser.parse_args()

# Initializations:

UserName = os.getenv('USER', os.getenv('USERNAME', 'user'))
# cut DOMAIN from username:
dpos = UserName.rfind('/')
if dpos == -1: dpos = UserName.rfind('\\')
if dpos != -1: UserName = UserName[dpos+1:]
UserName = UserName.capitalize()

DialogPath = os.path.dirname(os.path.abspath(sys.argv[0]))
TemplatesPath = os.path.join( DialogPath, 'templates')
LogosPath = os.path.join( DialogPath, 'logos')
CodecsPath = DialogPath
FontsList = ['','Arial','Courier-New','Impact','Tahoma','Times-New-Roman','Verdana']
Encoders = ['ffmpeg', 'mencoder']
Gravity = ['SouthEast','South','SouthWest','West','NorthWest','North','NorthEast','East','Center']

# Process templates:
Templates = ['']
TemplateF = 0
TemplateS = 0
if os.path.isdir(TemplatesPath):
   files = os.listdir(TemplatesPath)
   files.sort()
   index = 0
   for afile in files:
      if afile[0] == '.': continue
      index += 1
      Templates.append(afile)
      if afile == Options.slate:    TemplateS = index
      if afile == Options.template: TemplateF = index


# Process codecs:
CodecNames = []
CodecFiles = []
allFiles = os.listdir( CodecsPath)
for afile in allFiles:
   afile = os.path.join( CodecsPath, afile)
   if os.path.isfile( afile):
      parts = afile.split('.')
      if len(parts):
         if parts[len(parts)-1] in Encoders:
            CodecFiles.append( afile)
CodecFiles.sort()
for afile in CodecFiles:
   file = open( afile)
   name = file.readline().strip()
   file.close()
   CodecNames.append( name)

class Dialog( QtGui.QWidget):
   def __init__( self):
      QtGui.QWidget.__init__( self)
      self.evaluated = False

      self.setWindowTitle('Mavishky')
      self.mainLayout = QtGui.QVBoxLayout( self)
      self.tabwidget = QtGui.QTabWidget( self)
      self.mainLayout.addWidget( self.tabwidget)

      self.generalwidget = QtGui.QWidget( self)
      self.tabwidget.addTab( self.generalwidget,'General')
      self.generallayout = QtGui.QVBoxLayout( self.generalwidget)

      self.parameterswidget = QtGui.QWidget( self)
      self.tabwidget.addTab( self.parameterswidget,'Parameters')
      self.parameterslayout = QtGui.QVBoxLayout( self.parameterswidget)

      self.stereowidget = QtGui.QWidget( self)
      self.tabwidget.addTab( self.stereowidget,'Stereo')
      self.stereolayout = QtGui.QVBoxLayout( self.stereowidget)

      self.afanasywidget = QtGui.QWidget( self)
      self.tabwidget.addTab( self.afanasywidget,'Afanasy')
      self.afanasylayout = QtGui.QVBoxLayout( self.afanasywidget)


      # General:

      self.lFormat = QtGui.QHBoxLayout()
      self.tFormat = QtGui.QLabel('Format:', self)
      self.cbFormat = QtGui.QComboBox( self)
      self.cbFormat.addItem('Encode "as is" only')
      self.cbFormat.addItem('PAL (720x576)', QtCore.QVariant('720x576'))
      self.cbFormat.addItem('PAL Square (768x576)', QtCore.QVariant('768x576'))
      self.cbFormat.addItem('HD 720p (1280x720)', QtCore.QVariant('1280x720'))
      self.cbFormat.addItem('HD 1080p (1920x1080)', QtCore.QVariant('1920x1080'))
      self.cbFormat.setCurrentIndex( 1)
      QtCore.QObject.connect( self.cbFormat, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      self.tCodec = QtGui.QLabel('Codec:', self)
      self.cbCodec = QtGui.QComboBox( self)
      i = 0
      for name in CodecNames:
         self.cbCodec.addItem( name, QtCore.QVariant( CodecFiles[i]))
         i = i + 1
      QtCore.QObject.connect( self.cbCodec, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      self.tFPS = QtGui.QLabel('FPS:', self)
      self.cbFPS = QtGui.QComboBox( self)
      self.cbFPS.addItem('24')
      self.cbFPS.addItem('25')
      self.cbFPS.addItem('30')
      self.cbFPS.setCurrentIndex( 1)
      QtCore.QObject.connect( self.cbFPS, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      self.lFormat.addWidget( self.tFormat)
      self.lFormat.addWidget( self.cbFormat)
      self.lFormat.addWidget( self.tFPS)
      self.lFormat.addWidget( self.cbFPS)
      self.lFormat.addWidget( self.tCodec)
      self.lFormat.addWidget( self.cbCodec)
      self.generallayout.addLayout( self.lFormat)


      self.gInformation = QtGui.QGroupBox('Information')
      self.lInformation = QtGui.QVBoxLayout()
      self.gInformation.setLayout( self.lInformation)

      self.lTitles = QtGui.QHBoxLayout()
      self.tCompany = QtGui.QLabel('Company:', self)
      self.editCompany = QtGui.QLineEdit( Options.company, self)
      QtCore.QObject.connect( self.editCompany, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      self.tProject = QtGui.QLabel('Project:', self)
      self.editProject = QtGui.QLineEdit( Options.project, self)
      QtCore.QObject.connect( self.editProject, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      self.tShot = QtGui.QLabel('Shot:', self)
      self.editShot = QtGui.QLineEdit('', self)
      QtCore.QObject.connect( self.editShot, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      self.tVersion = QtGui.QLabel('Version:', self)
      self.editVersion = QtGui.QLineEdit('', self)
      QtCore.QObject.connect( self.editVersion, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      self.cAutoTitles = QtGui.QCheckBox('Auto', self)
      self.cAutoTitles.setChecked( True)
      QtCore.QObject.connect( self.cAutoTitles, QtCore.SIGNAL('stateChanged(int)'), self.autoTitles)
      self.lTitles.addWidget( self.tCompany)
      self.lTitles.addWidget( self.editCompany)
      self.lTitles.addWidget( self.tProject)
      self.lTitles.addWidget( self.editProject)
      self.lTitles.addWidget( self.tShot)
      self.lTitles.addWidget( self.editShot)
      self.lTitles.addWidget( self.tVersion)
      self.lTitles.addWidget( self.editVersion)
      self.lTitles.addWidget( self.cAutoTitles)
      self.lInformation.addLayout( self.lTitles)

      self.lUser = QtGui.QHBoxLayout()
      self.lArtist = QtGui.QLabel('Artist:', self)
      self.lUser.addWidget( self.lArtist)
      self.editArtist = QtGui.QLineEdit( UserName, self)
      self.lUser.addWidget( self.editArtist)
      QtCore.QObject.connect( self.editArtist, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      self.lActivity = QtGui.QLabel('Activity:', self)
      self.lUser.addWidget( self.lActivity)
      self.editActivity = QtGui.QLineEdit('', self)
      self.lUser.addWidget( self.editActivity)
      QtCore.QObject.connect( self.editActivity, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      self.cbActivity = QtGui.QComboBox( self)
      self.cbActivity.addItem('comp')
      self.cbActivity.addItem('render')
      self.cbActivity.addItem('anim')
      self.cbActivity.addItem('sim')
      self.cbActivity.addItem('clnup')
      self.cbActivity.addItem('mtpnt')
      self.lUser.addWidget( self.cbActivity)
      QtCore.QObject.connect( self.cbActivity, QtCore.SIGNAL('currentIndexChanged(int)'), self.activityChanged)
      self.lInformation.addLayout( self.lUser)

      self.lComments = QtGui.QHBoxLayout()
      self.tComments = QtGui.QLabel('Comments:', self)
      self.editComments = QtGui.QLineEdit( self)
      QtCore.QObject.connect( self.editComments, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      self.lComments.addWidget( self.tComments)
      self.lComments.addWidget( self.editComments)
      self.lInformation.addLayout( self.lComments)

      self.generallayout.addWidget( self.gInformation)

      self.gInputSettings = QtGui.QGroupBox('Input Sequence Pattern')
      self.lInputSettings = QtGui.QVBoxLayout()
      self.gInputSettings.setLayout( self.lInputSettings)

      self.editInputFile = QtGui.QLineEdit( self)
      QtCore.QObject.connect( self.editInputFile, QtCore.SIGNAL('textEdited(QString)'), self.inputFileChanged)
      self.lInputSettings.addWidget( self.editInputFile)

      self.lBrowseInput = QtGui.QHBoxLayout()
      self.lFilesCount = QtGui.QLabel('Files count:', self)
      self.editInputFilesCount = QtGui.QLineEdit( self)
      self.editInputFilesCount.setEnabled( False)
      self.lPattern = QtGui.QLabel('Pattern:', self)
      self.editInputFilesPattern = QtGui.QLineEdit( self)
      self.editInputFilesPattern.setEnabled( False)
      self.btnBrowseInput = QtGui.QPushButton('Browse sequence file', self)
      QtCore.QObject.connect( self.btnBrowseInput, QtCore.SIGNAL('pressed()'), self.browseInput)
      self.lBrowseInput.addWidget( self.lFilesCount)
      self.lBrowseInput.addWidget( self.editInputFilesCount)
      self.lBrowseInput.addWidget( self.lPattern)
      self.lBrowseInput.addWidget( self.editInputFilesPattern)
      self.lBrowseInput.addWidget( self.btnBrowseInput)
      self.lInputSettings.addLayout( self.lBrowseInput)

      self.lIdentify = QtGui.QHBoxLayout()
      self.tIdentify = QtGui.QLabel('Identify:', self)
      self.editIdentify = QtGui.QLineEdit( self)
      self.editIdentify.setEnabled( False)
      self.btnIdentify = QtGui.QPushButton('Refresh', self)
      QtCore.QObject.connect( self.btnIdentify, QtCore.SIGNAL('pressed()'), self.inputFileChanged)
      self.lIdentify.addWidget( self.tIdentify)
      self.lIdentify.addWidget( self.editIdentify)
      self.lIdentify.addWidget( self.btnIdentify)
      self.lInputSettings.addLayout( self.lIdentify)

      self.generallayout.addWidget( self.gInputSettings)


      self.gOutputSettings = QtGui.QGroupBox('Output File')
      self.lOutputSettings = QtGui.QVBoxLayout()
      self.gOutputSettings.setLayout( self.lOutputSettings)

      self.lOutputName = QtGui.QHBoxLayout()
      self.tOutputName = QtGui.QLabel('Output file name:', self)
      self.lOutputName.addWidget( self.tOutputName)
      self.editOutputName = QtGui.QLineEdit( self)
      self.lOutputName.addWidget( self.editOutputName)
      QtCore.QObject.connect( self.editOutputName, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      self.btnBrowseOutput = QtGui.QPushButton('Browse', self)
      self.lOutputName.addWidget( self.btnBrowseOutput)
      QtCore.QObject.connect( self.btnBrowseOutput, QtCore.SIGNAL('pressed()'), self.browseOutput)
      self.cAutoOutput = QtGui.QCheckBox('Auto', self)
      self.cAutoOutput.setChecked( True)
      self.lOutputName.addWidget( self.cAutoOutput)
      QtCore.QObject.connect( self.cAutoOutput, QtCore.SIGNAL('stateChanged(int)'), self.autoOutput)
      self.lOutputSettings.addLayout( self.lOutputName)

      self.lOutputDir = QtGui.QHBoxLayout()
      self.tOutputDir = QtGui.QLabel('Output folder:', self)
      self.editOutputDir = QtGui.QLineEdit( self)
      QtCore.QObject.connect( self.editOutputDir, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      self.lOutputDir.addWidget( self.tOutputDir)
      self.lOutputDir.addWidget( self.editOutputDir)
      self.lOutputSettings.addLayout( self.lOutputDir)

      self.generallayout.addWidget( self.gOutputSettings)


      self.cmdField = QtGui.QTextEdit( self)
      self.cmdField.setReadOnly( True)
      self.mainLayout.addWidget( self.cmdField)

      self.lProcess = QtGui.QHBoxLayout()
      self.btnRefresh = QtGui.QPushButton('Refresh', self)
      QtCore.QObject.connect( self.btnRefresh, QtCore.SIGNAL('pressed()'), self.evaluate)
      self.btnStart = QtGui.QPushButton('Start', self)
      self.btnStart.setEnabled( False)
      QtCore.QObject.connect( self.btnStart, QtCore.SIGNAL('pressed()'), self.execute)
      self.btnStop = QtGui.QPushButton('Stop', self)
      self.btnStop.setEnabled( False)
      QtCore.QObject.connect( self.btnStop, QtCore.SIGNAL('pressed()'), self.processStop)
      self.lProcess.addWidget( self.btnRefresh)
      self.lProcess.addWidget( self.btnStart)
      self.lProcess.addWidget( self.btnStop)
      self.mainLayout.addLayout( self.lProcess)


      # Parameters:

      self.lTemplates = QtGui.QHBoxLayout()
      self.tTemplateS = QtGui.QLabel('Slate Template:', self)
      self.tTemplateF = QtGui.QLabel('Frame Template:', self)
      self.cbTemplateS = QtGui.QComboBox( self)
      self.cbTemplateF = QtGui.QComboBox( self)
      for template in Templates:
         self.cbTemplateS.addItem(template)
         self.cbTemplateF.addItem(template)
      self.cbTemplateS.setCurrentIndex( TemplateS)
      self.cbTemplateF.setCurrentIndex( TemplateF)
      QtCore.QObject.connect( self.cbTemplateS, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      QtCore.QObject.connect( self.cbTemplateF, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      self.lTemplates.addWidget( self.tTemplateS)
      self.lTemplates.addWidget( self.cbTemplateS)
      self.lTemplates.addWidget( self.tTemplateF)
      self.lTemplates.addWidget( self.cbTemplateF)
      self.parameterslayout.addLayout( self.lTemplates)

      self.gDrawing = QtGui.QGroupBox('Drawing')
      self.lDrawing = QtGui.QVBoxLayout()
      self.gDrawing.setLayout( self.lDrawing)

      self.cTime = QtGui.QCheckBox('Add Time To Date', self)
      self.cTime.setChecked( False)
      QtCore.QObject.connect( self.cTime, QtCore.SIGNAL('stateChanged(int)'), self.evaluate)
      self.lDrawing.addWidget( self.cTime)

      self.lCacher = QtGui.QHBoxLayout()
      self.tCacherH = QtGui.QLabel('16:9 Cacher', self)
      self.cbCacherH = QtGui.QComboBox( self)
      self.cbCacherH.addItem('None')
      self.cbCacherH.addItem('25%', QtCore.QVariant('25'))
      self.cbCacherH.addItem('50%', QtCore.QVariant('50'))
      self.cbCacherH.addItem('75%', QtCore.QVariant('75'))
      self.cbCacherH.addItem('100%', QtCore.QVariant('100'))
      self.cbCacherH.setCurrentIndex( 1)
      QtCore.QObject.connect( self.cbCacherH, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      self.tCacherC = QtGui.QLabel('2.35 Cacher', self)
      self.cbCacherC = QtGui.QComboBox( self)
      self.cbCacherC.addItem('None')
      self.cbCacherC.addItem('25%', QtCore.QVariant('25'))
      self.cbCacherC.addItem('50%', QtCore.QVariant('50'))
      self.cbCacherC.addItem('75%', QtCore.QVariant('75'))
      self.cbCacherC.addItem('100%', QtCore.QVariant('100'))
      self.cbCacherC.setCurrentIndex( 1)
      QtCore.QObject.connect( self.cbCacherC, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      self.lCacher.addWidget( self.tCacherH)
      self.lCacher.addWidget( self.cbCacherH)
      self.lCacher.addWidget( self.tCacherC)
      self.lCacher.addWidget( self.cbCacherC)
      self.lDrawing.addLayout( self.lCacher)

      self.lLogo = QtGui.QHBoxLayout()
      self.cLogo = QtGui.QCheckBox('Logo', self)
      QtCore.QObject.connect( self.cLogo, QtCore.SIGNAL('stateChanged(int)'), self.drawLogo)
      self.tLogoPath = QtGui.QLabel('Path:', self)
      self.editLogoPath = QtGui.QLineEdit( os.path.join( LogosPath, 'logo.png'), self)
      QtCore.QObject.connect( self.editLogoPath, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      self.tLogoSize = QtGui.QLabel('Size:', self)
      self.sbLogoSizeX = QtGui.QSpinBox( self)
      self.sbLogoSizeX.setRange( 1, 1000)
      self.sbLogoSizeX.setValue( 200)
      QtCore.QObject.connect( self.sbLogoSizeX, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      self.sbLogoSizeY = QtGui.QSpinBox( self)
      self.sbLogoSizeY.setRange( 1, 1000)
      self.sbLogoSizeY.setValue( 100)
      QtCore.QObject.connect( self.sbLogoSizeY, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      self.btnBrowseLogo = QtGui.QPushButton('Browse', self)
      QtCore.QObject.connect( self.btnBrowseLogo, QtCore.SIGNAL('pressed()'), self.browseLogo)
      self.tLogoGravity = QtGui.QLabel('Position:', self)
      self.cbLogoGravity = QtGui.QComboBox( self)
      for pos in Gravity: self.cbLogoGravity.addItem( pos)
      QtCore.QObject.connect( self.cbLogoGravity, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      self.editLogoPath.setEnabled( False)
      self.btnBrowseLogo.setEnabled( False)
      self.sbLogoSizeX.setEnabled( False)
      self.sbLogoSizeY.setEnabled( False)
      self.cbLogoGravity.setEnabled( False)
      self.lLogo.addWidget( self.cLogo)
      self.lLogo.addWidget( self.tLogoPath)
      self.lLogo.addWidget( self.editLogoPath)
      self.lLogo.addWidget( self.btnBrowseLogo)
      self.lLogo.addWidget( self.tLogoSize)
      self.lLogo.addWidget( self.sbLogoSizeX)
      self.lLogo.addWidget( self.sbLogoSizeY)
      self.lLogo.addWidget( self.tLogoGravity)
      self.lLogo.addWidget( self.cbLogoGravity)
      self.lDrawing.addLayout( self.lLogo)

      self.lFont = QtGui.QHBoxLayout()
      self.tFont = QtGui.QLabel('Annotations Text Font:', self)
      self.lFont.addWidget( self.tFont)
      self.editFont = QtGui.QLineEdit('', self)
      self.lFont.addWidget( self.editFont)
      QtCore.QObject.connect( self.editFont, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      self.cbFont = QtGui.QComboBox( self)
      for font in FontsList: self.cbFont.addItem( font)
      self.lFont.addWidget( self.cbFont)
      QtCore.QObject.connect( self.cbFont, QtCore.SIGNAL('currentIndexChanged(int)'), self.fontChanged)
      self.lDrawing.addLayout( self.lFont)

      self.parameterslayout.addWidget( self.gDrawing)

      self.gCorrectionSettings = QtGui.QGroupBox('Image Correction')
      self.lCorr = QtGui.QHBoxLayout()
      self.gCorrectionSettings.setLayout( self.lCorr)
      self.tGamma = QtGui.QLabel('Gamma:', self)
      self.dsbGamma = QtGui.QDoubleSpinBox( self)
      self.dsbGamma.setRange( 0.1, 10.0)
      self.dsbGamma.setDecimals( 1)
      self.dsbGamma.setSingleStep( 0.1)
      self.dsbGamma.setValue( 1.0)
      QtCore.QObject.connect( self.dsbGamma, QtCore.SIGNAL('valueChanged(double)'), self.evaluate)
      self.lCorr.addWidget( self.tGamma)
      self.lCorr.addWidget( self.dsbGamma)
      self.parameterslayout.addWidget( self.gCorrectionSettings)

      self.dateTimeLayout = QtGui.QHBoxLayout()
      self.cDateOutput = QtGui.QCheckBox('Append Name With Date', self)
      self.cDateOutput.setChecked( False)
      self.dateTimeLayout.addWidget( self.cDateOutput)
      QtCore.QObject.connect( self.cDateOutput, QtCore.SIGNAL('stateChanged(int)'), self.evaluate)
      self.cTimeOutput = QtGui.QCheckBox('Append Name With Time', self)
      self.cTimeOutput.setChecked( False)
      self.dateTimeLayout.addWidget( self.cTimeOutput)
      self.parameterslayout.addLayout( self.dateTimeLayout)
      QtCore.QObject.connect( self.cTimeOutput, QtCore.SIGNAL('stateChanged(int)'), self.evaluate)


      self.cStereoMode = QtGui.QCheckBox('Turn On Stereo Mode', self)
      self.cStereoMode.setChecked( False)
      QtCore.QObject.connect( self.cStereoMode, QtCore.SIGNAL('stateChanged(int)'), self.evaluate)
      self.stereolayout.addWidget( self.cStereoMode)


      # Afanasy:

      self.cAfanasy = QtGui.QCheckBox('Enable', self)
      self.cAfanasy.setChecked( Options.afanasy)
      QtCore.QObject.connect( self.cAfanasy, QtCore.SIGNAL('stateChanged(int)'), self.evaluate)
      self.afanasylayout.addWidget( self.cAfanasy)

      # Priority
      self.lAfPriority = QtGui.QHBoxLayout()
      self.tAfPriority = QtGui.QLabel('Priority:', self)
      self.lAfPriority.addWidget( self.tAfPriority)
      self.sbAfPriority = QtGui.QSpinBox( self)
      self.sbAfPriority.setRange( -1, 1000000)
      self.sbAfPriority.setValue( Options.afpriority)
      QtCore.QObject.connect( self.sbAfPriority, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      self.lAfPriority.addWidget( self.sbAfPriority)
      self.tAfPriorityDef = QtGui.QLabel('"-1" Means default value.', self)
      self.lAfPriority.addWidget( self.tAfPriorityDef)
      self.afanasylayout.addLayout( self.lAfPriority)

      # Hosts
      self.gAfHosts = QtGui.QGroupBox('Hosts')
      self.afanasylayout.addWidget( self.gAfHosts)
      self.lAfHosts = QtGui.QVBoxLayout()
      self.gAfHosts.setLayout( self.lAfHosts)

      self.lAfMaxHosts = QtGui.QHBoxLayout()
      self.lAfHosts.addLayout( self.lAfMaxHosts)
      self.tAfMaxHosts = QtGui.QLabel('Maximum Number:', self)
      self.lAfMaxHosts.addWidget( self.tAfMaxHosts)
      self.sbAfMaxHosts = QtGui.QSpinBox( self)
      self.sbAfMaxHosts.setRange( -1, 1000000)
      self.sbAfMaxHosts.setValue( Options.afmaxhosts)
      QtCore.QObject.connect( self.sbAfMaxHosts, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      self.lAfMaxHosts.addWidget( self.sbAfMaxHosts)
      self.tAfMaxHostsDef = QtGui.QLabel('"-1" Means no hosts count limit.', self)
      self.lAfMaxHosts.addWidget( self.tAfMaxHostsDef)

      self.lAfHostsMask = QtGui.QHBoxLayout()
      self.lAfHosts.addLayout( self.lAfHostsMask)
      self.tAfHostsMask = QtGui.QLabel('Hosts Names Mask:', self)
      self.lAfHostsMask.addWidget( self.tAfHostsMask)
      self.editAfHostsMask = QtGui.QLineEdit( Options.afhostsmask, self)
      QtCore.QObject.connect( self.editAfHostsMask, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      self.lAfHostsMask.addWidget( self.editAfHostsMask)
      self.tAfHostsMaskDef = QtGui.QLabel('Leave empty to run on any host.', self)
      self.lAfHostsMask.addWidget( self.tAfHostsMaskDef)

      self.lAfHostsMaskExclude = QtGui.QHBoxLayout()
      self.lAfHosts.addLayout( self.lAfHostsMaskExclude)
      self.tAfHostsMaskExclude = QtGui.QLabel('Exclude Hosts Names Mask:', self)
      self.lAfHostsMaskExclude.addWidget( self.tAfHostsMaskExclude)
      self.editAfHostsMaskExclude = QtGui.QLineEdit( Options.afhostsmaskex, self)
      QtCore.QObject.connect( self.editAfHostsMaskExclude, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      self.lAfHostsMaskExclude.addWidget( self.editAfHostsMaskExclude)
      self.tAfHostsMaskExcludeDef = QtGui.QLabel('Leave empty not to exclude any host.', self)
      self.lAfHostsMaskExclude.addWidget( self.tAfHostsMaskExcludeDef)

      # Depends
      self.gAfDepends = QtGui.QGroupBox('Depends')
      self.afanasylayout.addWidget( self.gAfDepends)
      self.lAfDepends = QtGui.QVBoxLayout()
      self.gAfDepends.setLayout( self.lAfDepends)

      self.lAfDependMask = QtGui.QHBoxLayout()
      self.lAfDepends.addLayout( self.lAfDependMask)
      self.tAfDependMask = QtGui.QLabel('Depend Jobs Mask:', self)
      self.lAfDependMask.addWidget( self.tAfDependMask)
      self.editAfDependMask = QtGui.QLineEdit( Options.afdependmask, self)
      QtCore.QObject.connect( self.editAfDependMask, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      self.lAfDependMask.addWidget( self.editAfDependMask)
      self.tAfDependMaskDef = QtGui.QLabel('Leave empty not to wait any jobs.', self)
      self.lAfDependMask.addWidget( self.tAfDependMaskDef)

      self.lAfDependMaskGlobal = QtGui.QHBoxLayout()
      self.lAfDepends.addLayout( self.lAfDependMaskGlobal)
      self.tAfDependMaskGlobal = QtGui.QLabel('Global Depend Jobs Mask:', self)
      self.lAfDependMaskGlobal.addWidget( self.tAfDependMaskGlobal)
      self.editAfDependMaskGlobal = QtGui.QLineEdit( Options.afdependmaskgl, self)
      QtCore.QObject.connect( self.editAfDependMaskGlobal, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      self.lAfDependMaskGlobal.addWidget( self.editAfDependMaskGlobal)
      self.tAfDependMaskGlobalDef = QtGui.QLabel('Set mask to wait any user jobs.', self)
      self.lAfDependMaskGlobal.addWidget( self.tAfDependMaskGlobalDef)

      # Capacity
      self.gAfCapacity = QtGui.QGroupBox('Capacity')
      self.lAfCapacity = QtGui.QHBoxLayout()
      self.gAfCapacity.setLayout( self.lAfCapacity)

      self.cAfOneTask = QtGui.QCheckBox('One Task', self)
      self.cAfOneTask.setChecked( True)
      QtCore.QObject.connect( self.cAfOneTask, QtCore.SIGNAL('stateChanged(int)'), self.evaluate)

      self.tAfCapacity = QtGui.QLabel('Capacity:', self)
      self.sbAfCapacity = QtGui.QSpinBox( self)
      self.sbAfCapacity.setRange( -1, 1000000)
      self.sbAfCapacity.setValue( Options.afcapacity)
      QtCore.QObject.connect( self.sbAfCapacity, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)

      self.tAfCapConvert = QtGui.QLabel('Convert:', self)
      self.sbAfCapConvert = QtGui.QSpinBox( self)
      self.sbAfCapConvert.setRange( -1, 1000000)
      self.sbAfCapConvert.setValue( Options.afcapacity)
      QtCore.QObject.connect( self.sbAfCapConvert, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)

      self.tAfCapEncode = QtGui.QLabel('Encode:', self)
      self.sbAfCapEncode = QtGui.QSpinBox( self)
      self.sbAfCapEncode.setRange( -1, 1000000)
      self.sbAfCapEncode.setValue( Options.afcapacity)
      QtCore.QObject.connect( self.sbAfCapEncode, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)

      self.lAfCapacity.addWidget( self.cAfOneTask)
      self.lAfCapacity.addWidget( self.tAfCapacity)
      self.lAfCapacity.addWidget( self.sbAfCapacity)
      self.lAfCapacity.addWidget( self.tAfCapConvert)
      self.lAfCapacity.addWidget( self.sbAfCapConvert)
      self.lAfCapacity.addWidget( self.tAfCapEncode)
      self.lAfCapacity.addWidget( self.sbAfCapEncode)
      self.afanasylayout.addWidget( self.gAfCapacity)

      # Pause
      self.lAfPause = QtGui.QHBoxLayout()
      self.afanasylayout.addLayout( self.lAfPause)

      self.cAfPause = QtGui.QCheckBox('Start Job Paused', self)
      self.cAfPause.setChecked( Options.afpause)
      QtCore.QObject.connect( self.cAfPause, QtCore.SIGNAL('stateChanged(int)'), self.evaluate)
      self.lAfPause.addWidget( self.cAfPause)

      self.tAfTime = QtGui.QLabel('Start At Time:', self)
      self.lAfPause.addWidget( self.tAfTime)
      self.editAfTime = QtGui.QDateTimeEdit( QtCore.QDateTime.currentDateTime(), self)
      self.editAfTime.setDisplayFormat('dddd d MMMM yyyy, h:mm')
      QtCore.QObject.connect( self.editAfTime, QtCore.SIGNAL('dateTimeChanged()'), self.evaluate)
      self.lAfPause.addWidget( self.editAfTime)


      self.inputEvaluated = False
      self.autoTitles()
      self.activityChanged()
      self.autoOutput()
      self.inputFileChanged()
      self.evaluate()

   def autoOutput( self):
      enable = not self.cAutoOutput.isChecked()
      self.editOutputName.setEnabled( enable)
      self.btnBrowseOutput.setEnabled( enable)
      self.editOutputDir.setEnabled( enable)

   def autoTitles( self):
      enable = not self.cAutoTitles.isChecked()
      self.editProject.setEnabled( enable)
      self.editShot.setEnabled( enable)
      self.editVersion.setEnabled( enable)

   def drawLogo( self):
      enable = self.cLogo.isChecked()
      self.btnBrowseLogo.setEnabled( enable)
      self.editLogoPath.setEnabled( enable)
      self.sbLogoSizeX.setEnabled( enable)
      self.sbLogoSizeY.setEnabled( enable)
      self.cbLogoGravity.setEnabled(enable)
      self.evaluate()

   def activityChanged( self):
      self.editActivity.setText( self.cbActivity.currentText())
      self.evaluate()

   def fontChanged( self):
      self.editFont.setText( self.cbFont.currentText())
      self.evaluate()

   def browseLogo( self):
      afile = QtGui.QFileDialog.getOpenFileName( self,'Choose a file', LogosPath)
      if afile.isEmpty(): return
      self.editLogoPath.setText( '%s' % afile)
      self.evaluate()

   def browseOutput( self):
      afile = QtGui.QFileDialog.getOpenFileName( self,'Choose a file')
      if afile.isEmpty(): return
      afile = '%s' % afile
      self.editOutputDir.setText( os.path.dirname( afile))
      afile = os.path.basename( afile)
      pos = afile.rfind('.')
      if pos > 0: afile = afile[ 0 : pos]
      self.editOutputName.setText( afile)
      self.evaluate()

   def browseInput( self):
      afile = QtGui.QFileDialog.getOpenFileName( self,'Choose a file', self.editInputFile.text())
      if afile.isEmpty(): return
      self.editInputFile.setText( afile)
      self.inputFileChanged()

   def inputFileChanged( self):
      self.inputEvaluated = False
      self.editInputFilesCount.clear()
      self.editInputFilesPattern.clear()
      self.editIdentify.clear()
      inputfile = '%s' % self.editInputFile.text()
      if sys.platform.find('win') == 0: inputfile = inputfile.replace('/','\\')

      if len(inputfile) == 0:
         self.cmdField.setText('Choose one file from sequence')
         return

      pos = inputfile.rfind('file://')
      if pos >= 0:
         inputfile = inputfile[ pos+7 : len(inputfile)]
         self.editInputFile.setText( inputfile)

      inputfile = inputfile.strip()
      inputfile = inputfile.strip('\n')
      self.inputDir = os.path.dirname( inputfile)
      if not os.path.isdir( self.inputDir):
         self.cmdField.setText('Can\'t find input directory')
         return
      filename = os.path.basename( inputfile)
      digitsall = re.findall( r'(#{1,})', filename)
      if len(digitsall) == 0: digitsall = re.findall( r'([0-9]{1,})', filename)
      if len(digitsall):
         digits = digitsall[len(digitsall)-1]
         pos = filename.rfind(digits)
         self.inputPrefix = filename[0 : pos]
         self.inputPadding = len(digits)
         self.inputSuffix = filename[pos+self.inputPadding : len(filename)]
         padstr = ''
         for d in range(self.inputPadding): padstr += '#'
         pattern = self.inputPrefix + padstr + self.inputSuffix
      else:
         self.cmdField.setText('Can\'t find digits in input file name')
         return
      self.editInputFilesPattern.setText( pattern)
      self.inputPattern = os.path.join( self.inputDir, pattern)

      eprefix = str( self.inputPrefix)
      esuffix = str( self.inputSuffix)
      epad = self.inputPadding
      expr = re.compile( r'%(eprefix)s([0-9]{%(epad)d,%(epad)d})%(esuffix)s' % vars())
      filescount = 0
      allItems = os.listdir(self.inputDir)
      for item in allItems:
         if not os.path.isfile( os.path.join( self.inputDir, item)): continue
         if not expr.match( item): continue
         if filescount == 0: afile = item
         filescount += 1
      self.editInputFilesCount.setText(str(filescount))
      if filescount == 0:
         self.cmdField.setText('No files founded matching pattern.')
         return
      if filescount == 1:
         self.cmdField.setText('Founded only 1 file matching pattern.')
         return
      if sys.platform.find('win') == 0: afile = afile.replace('/','\\')
      afile = os.path.join( self.inputDir, afile)
      pipe = subprocess.Popen( 'identify "%s"' % afile, shell=True, bufsize=100000, stdout=subprocess.PIPE).stdout
      output = pipe.read()
      if len(output) < len(afile):
         self.cmdField.setText('Invalid image.\n%s' % afile)
         return
      output = output.replace( afile, '')
      self.editIdentify.setText( output)

      self.inputEvaluated = True
      self.evaluate()

   def evaluate( self):
      self.evaluated = False
      if not self.inputEvaluated: return

      self.StereoMode = self.cStereoMode.isChecked()

      if self.cAutoTitles.isChecked(): self.editShot.clear()
      if self.cAutoOutput.isChecked():
         self.editOutputName.clear()
         self.editOutputDir.clear()

      project = '%s' % self.editProject.text()
      if Options.project == '':
         if self.cAutoTitles.isChecked() or project == '':
            if sys.platform.find('win') == 0:
               pat_split = self.inputPattern.upper().split('\\')
               if len(pat_split) > 4: project = pat_split[4]
               else: project = pat_split[len(pat_split)-1]
            else:
               pat_split = self.inputPattern.upper().split('/')
               if len(pat_split) > 3: project = pat_split[3]
               else: project = pat_split[len(pat_split)-1]
            self.editProject.setText( project)

      shot = '%s' % self.editShot.text()
      if self.cAutoTitles.isChecked() or shot == '':
         shot = self.inputPrefix.strip('.')
         self.editShot.setText( shot)

      version = '%s' % self.editVersion.text()
      if self.cAutoTitles.isChecked() or version == '':
         version = os.path.basename( os.path.dirname(self.inputPattern))
         self.editVersion.setText( version)

      company  = '%s' % self.editCompany.text()
      artist   = '%s' % self.editArtist.text()
      activity = '%s' % self.editActivity.text()
      comments = '%s' % self.editComments.text()
      font     = '%s' % self.editFont.text()

      outdir = '%s' % self.editOutputDir.text()
      if self.cAutoOutput.isChecked() or outdir == None or outdir == '':
         outdir = os.path.dirname( self.inputDir)
         self.editOutputDir.setText( outdir)

      outname = '%s' % self.editOutputName.text()
      if self.cAutoOutput.isChecked() or outname == None or outname == '':
         outname = shot
         if activity != '': outname += '_' + activity
         if version  != '': outname += '_' + version
         outname += time.strftime('_%y%m%d')
         self.editOutputName.setText( outname)

      logodraw = self.cLogo.isChecked()
      logopath = self.editLogoPath.text()
      if logodraw:
         if not os.path.isfile( logopath):
            self.cmdField.setText('No logo file founded')
            return

      cmd = 'mavishky.py'
      cmd = 'python ' + os.path.join( os.path.dirname( os.path.abspath( sys.argv[0])), cmd)
      cmd += ' -c %s' % self.cbCodec.itemData( self.cbCodec.currentIndex()).toString()
      cmd += ' -f %s' % self.cbFPS.currentText()
      format = self.cbFormat.itemData( self.cbFormat.currentIndex()).toString()
      if not format.isEmpty():
         ts = self.cbTemplateS.currentText()
         tf = self.cbTemplateF.currentText()
         cmd += ' -r %s' % format
         cmd += ' -g %.2f' % self.dsbGamma.value()
         if ts != '': cmd += ' -s "%s"' % ts
         if tf != '': cmd += ' -t "%s"' % tf
         if project  != '': cmd += ' --project "%s"'  % project
         if shot     != '': cmd += ' --shot "%s"'     % shot
         if version  != '': cmd += ' --ver "%s"'      % version
         if company  != '': cmd += ' --company "%s"'  % company
         if artist   != '': cmd += ' --artist "%s"'   % artist
         if activity != '': cmd += ' --activity "%s"' % activity
         if comments != '': cmd += ' --comments "%s"' % comments
         if font     != '': cmd += ' --font "%s"'     % font
         if self.cTime.isChecked(): cmd += ' --addtime'
         cacher = self.cbCacherH.itemData( self.cbCacherH.currentIndex()).toString()
         if not cacher.isEmpty(): cmd += ' --draw169 %s' % cacher
         cacher = self.cbCacherC.itemData( self.cbCacherC.currentIndex()).toString()
         if not cacher.isEmpty(): cmd += ' --draw235 %s' % cacher
         if self.cLogo.isChecked():
            cmd += ' --logopath "%s"' % logopath
            logosize  = str( self.sbLogoSizeX.value())
            logosize += 'x'
            logosize += str( self.sbLogoSizeY.value())
            cmd += ' --logosize %s' % logosize
            cmd += ' --logograv %s' % self.cbLogoGravity.currentText()
      if self.cDateOutput.isChecked(): cmd += ' --datesuffix'
      if self.cTimeOutput.isChecked(): cmd += ' --timesuffix'
      if self.StereoMode:
         cmd += ' --stereo'
      if self.cAfanasy.isChecked() and not self.cAfOneTask.isChecked():
         cmd += ' -A'
         if self.sbAfCapConvert.value() != -1: cmd += ' --afconvcap %d' % self.sbAfCapConvert.value()
         if self.sbAfCapEncode.value()  != -1: cmd += ' --afenccap %d' % self.sbAfCapEncode.value()
      if Options.debug: cmd += ' --debug'

      cmd += ' "%s"' % self.inputPattern
      cmd += ' "%s"' % os.path.join( outdir, outname)

      self.cmdField.setText( cmd)
      self.evaluated = True
      self.btnStart.setEnabled( True)

   def execute( self):
      if not self.evaluated: return
      self.command = '%s' % self.cmdField.toPlainText()
      if len( self.command) == 0: return

      if self.cAfanasy.isChecked() and self.cAfOneTask.isChecked():
         af = __import__('af', globals(), locals(), [])
         job = af.Job( '%s' % self.editOutputName.text() + ' mavishka')
         block = af.Block('mavishky')
         if self.sbAfPriority.value()  != -1: job.setPriority(    self.sbAfPriority.value())
         if self.sbAfMaxHosts.value()  != -1: job.setMaxHosts(    self.sbAfMaxHosts.value())
         if self.sbAfCapacity.value()  != -1: block.setCapacity(  self.sbAfCapacity.value())
         hostsmask         = '%s' % self.editAfHostsMask.text()
         hostsmaskexclude  = '%s' % self.editAfHostsMaskExclude.text()
         dependmask        = '%s' % self.editAfDependMask.text()
         dependmaskglobal  = '%s' % self.editAfDependMaskGlobal.text()
         if hostsmask        != '': job.setHostsMask(        hostsmask        )
         if hostsmaskexclude != '': job.setHostsMaskExclude( hostsmaskexclude )
         if dependmask       != '': job.setDependMask(       dependmask       )
         if dependmaskglobal != '': job.setDependMaskGlobal( dependmaskglobal )
         datetime = self.editAfTime.dateTime()
         if datetime > QtCore.QDateTime.currentDateTime(): job.setWaitTime( datetime.toTime_t())
         if self.cAfPause.isChecked(): job.pause()
         job.setNeedOS('')
         job.blocks.append( block)
         task = af.Task( '%s' % self.editOutputName.text())
         task.setCommand( self.command)
         block.tasks.append( task)
         job.send()
      else:
         self.btnStart.setEnabled( False)
         self.btnStop.setEnabled( True)
         self.cmdField.clear()
         self.process = QtCore.QProcess( self)
         self.process.setProcessChannelMode( QtCore.QProcess.MergedChannels)
         QtCore.QObject.connect( self.process, QtCore.SIGNAL('finished( int)'), self.processfinished)
         QtCore.QObject.connect( self.process, QtCore.SIGNAL('readyRead()'), self.processoutput)
         self.process.start( self.command)

   def processfinished( self, exitCode):
      print 'Exit code = %d' % exitCode
      self.btnStop.setEnabled( False)
      if exitCode != 0: return
      self.cmdField.setText( self.command)
      self.btnStart.setEnabled( True)

   def processoutput( self):
      output = str( self.process.readAll())
      print output,
      self.cmdField.insertPlainText( output)
      self.cmdField.moveCursor( QtGui.QTextCursor.End)

   def processStop( self):
      self.process.terminate()
      if sys.platform.find('win') == 0:
         self.process.kill()
      self.cmdField.setText('Stopped.')

app = QtGui.QApplication( sys.argv)
icon = QtGui.QIcon( os.path.join( os.path.join (DialogPath, 'icons'), 'icon.png'))
app.setWindowIcon( icon)
dialog = Dialog()
dialog.show()
app.exec_()
