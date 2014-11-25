'''
Created on 21.11.2014

@author: smory
'''

import xbmc
import xbmcaddon
import xbmcgui
import os
import re
import sys
import urllib2
import traceback
#import oe
 
from xml.dom import minidom
 
__scriptid__ = "openelec.samba.settings";
 
__addon__ = xbmcaddon.Addon(id=__scriptid__);
__cwd__ = __addon__.getAddonInfo('path');
#__media__ = '%s/resources/skins/default/media/' % __cwd__

CANCEL = (
    9,
    10,
    216,
    247,
    257,
    275,
    61467,
    92,
    61448,
    )
 
 
class smbWindow(xbmcgui.WindowXMLDialog):
 
    def __init__(self, *args, **kwargs):
 
        self.visible = False
        self.lastMenu = -1
        self.lastEntry = -1
 
        self.sectionsList = 1000
        self.paramList = 1100
 
        self.guiLists = [1000, 1100]
 
        self.buttons = {1500: "add share", 1501 : "disable share", 1502 : "remove share", 1503 : "add parameter", 1504 : "remove parameter"}
 
        self.isChild = False
        self.lastGuiList = -1
        self.lastListType = -1
               
        if 'isChild' in kwargs:
            self.isChild = True
 
        pass
 
    def onInit(self):
       
        self.visible = True
                 
        try:
 
#             if self.isChild:
#                 self.setFocusId(self.sectionsList)
#                 self.onFocus(self.sectionsList)
#                 return 
           
            self.setProperty('DIST_MEDIA', 'default')
            self.sambaConfig = parseConfFile()

            self.addMenuItems(self.sambaConfig.keys())
            
            #self.getControl(1100).setVisible(True)
            #self.getControl(1000).getSelectedItem().setProperty("listTyp", "1100")
            self.buildParameterMenu("global")
 
            self.setFocusId(self.sectionsList)
            self.onFocus(self.sectionsList)
            
            for id in self.buttons.keys():
                self.getControl(id).setLabel(self.buttons[id])
 
        except Exception, e:
            print(sys.exc_info())
            print( traceback.format_exc())
            print("exception on init")
            pass;
    
    def onAction(self, action):
        print("on action")
        
        focusId = self.getFocusId()
        actionId = int(action.getId())

        if focusId == 2222:
            if actionId == 61453:
                return

        if actionId in CANCEL:
            self.visible = False
            self.close()

        if focusId == self.paramList:

            curPos = self.getControl(focusId).getSelectedPosition()
            listSize = self.getControl(focusId).size()
            newPos = curPos
            nextItem = self.getControl(focusId).getListItem(newPos)

            if (curPos != self.lastGuiList
                or nextItem.getProperty('typ') == 'separator') \
                and actionId in [2, 3, 4]:

                while nextItem.getProperty('typ') == 'separator':

                    if actionId == 2:
                        newPos = newPos + 1

                    if actionId == 3:
                        newPos = newPos - 1

                    if actionId == 4:
                        newPos = newPos + 1

                    if newPos <= 0:
                        newPos = listSize - 1

                    if newPos >= listSize:
                        newPos = 0

                    nextItem = \
                        self.getControl(focusId).getListItem(newPos)

                self.lastGuiList = newPos
                self.getControl(focusId).selectItem(newPos)

                self.setProperty('InfoText',
                        nextItem.getProperty('InfoText'))

        if focusId == self.sectionsList:
            self.setFocusId(focusId)
        
    def buildParameterMenu(self, sectionString):
        parameters = self.sambaConfig[sectionString]
        items = []
        for param in sorted(parameters.keys()):
            listItem = xbmcgui.ListItem(label = param)
            listItem.setProperty("value", parameters[param])
            listItem.setProperty("typ", "text")
            
            if(param == "path"):
                items.insert(0, listItem)
            else:
                items.append(listItem)
        
        self.getControl(1100).reset()
        self.getControl(1100).addItems(items = items)
            
        
        
    def onClick(self, controlID):
        
        print("onClick " + str(controlID))
        
        if controlID in self.guiLists:
            selectedPosition = self.getControl(controlID).getSelectedPosition()
            selectedMenuItem = self.getControl(self.sectionsList).getSelectedItem()
            selectedItem = self.getControl(controlID).getSelectedItem()
            strTyp = selectedItem.getProperty('typ')
            strValue = selectedItem.getProperty('value')
            
            print("prop types: " + strTyp + " and " + strValue)

            if strTyp == 'multivalue':
                select_window = selectWindow('selectWindow.xml',
                        self.oe.__cwd__, 'Default', oeMain=self.oe)
                select_window.defaultValue = strValue
                select_window.availValues = \
                    selectedItem.getProperty('values')
                select_window.doModal()
                selectedItem.setProperty('value',
                        select_window.result)
                del select_window
            elif strTyp == 'text':

                xbmcKeyboard = xbmc.Keyboard(strValue)
                result_is_valid = False
                while not result_is_valid:
                    xbmcKeyboard.doModal()

                    if xbmcKeyboard.isConfirmed():
                        result_is_valid = True
                        validate_string = \
                            selectedItem.getProperty('validate')
                        if validate_string != '':
                            if not re.search(validate_string,
                                    xbmcKeyboard.getText()):
                                result_is_valid = False
                    else:
                        result_is_valid = True

                if xbmcKeyboard.isConfirmed():
                    selectedItem.setProperty('value',
                            xbmcKeyboard.getText())
                    
            elif strTyp == 'folder':

                xbmcDialog = xbmcgui.Dialog()
                returnValue = xbmcDialog.browse(
                    0,
                    'OpenELEC.tv',
                    'files',
                    '',
                    False,
                    False,
                    '/storage',
                    )
                if returnValue != '' and returnValue != '/':
                    selectedItem.setProperty('value',
                            unicode(returnValue))
                    
            elif strTyp == 'ip':

                xbmcDialog = xbmcgui.Dialog()
                returnValue = xbmcDialog.numeric(3, 'OpenELEC.tv',
                        strValue)
                if returnValue != '':
                    if returnValue == '0.0.0.0':
                        selectedItem.setProperty('value', '')
                    else:
                        selectedItem.setProperty('value',
                                returnValue)
            elif strTyp == 'num':

                if strValue == 'None' or strValue == '':
                    strValue = '0'

                xbmcDialog = xbmcgui.Dialog()
                returnValue = xbmcDialog.numeric(0, 'OpenELEC.tv',
                        strValue)
                if returnValue == '':
                    returnValue = -1

                if returnValue > -1:
                    selectedItem.setProperty('value',
                            unicode(returnValue))
            elif strTyp == 'bool':

                strValue = strValue.lower()
                
                if strValue == '0':
                    selectedItem.setProperty('value', '1')
                elif strValue == '1':
                    selectedItem.setProperty('value', '0')
                elif strValue == 'true':
                    selectedItem.setProperty('value', 'false')
                elif strValue == 'false':
                    selectedItem.setProperty('value', 'true')
                else:
                    selectedItem.setProperty('value', '1')

            
        
    def addMenuItems(self, sections):
        print(sections)
        listItems = [];
        
        for section in sorted(sections):
            listItem = xbmcgui.ListItem(label = section)
            listItem.setProperty("listTyp", "1100")
            
            if section == "global":                
                listItems.insert(0, listItem)
            else:
                listItems.append(listItem)
            print("added section: " + section)
                
        self.getControl(self.sectionsList).addItems(items = listItems)
        
#     def onControl(self, controlID):
#         print("oncontori")
#         if controlID == self.sectionsList:
#           item = self.getControl(self.sectionsList).getSelectedItem()
#           print('You selected : ' + item.getLabel())           
         
    # not used          
    def addMenuItem(self, strName, dictProperties):
 
        try:
 
            lstItem = xbmcgui.ListItem(label=strName)
 
            for strProp in dictProperties:
                lstItem.setProperty(strProp, unicode(dictProperties[strProp]))
 
            self.getControl(self.sectionsList).addItem(lstItem)
        except Exception, e:
            pass
        
    def onFocus(self, controlID):
        
        print("on fokus")
        
        if controlID in self.guiLists:

            currentEntry = self.getControl(controlID).getSelectedPosition()

            selectedEntry = self.getControl(controlID).getSelectedItem()
            if controlID == self.paramList:
                self.setProperty('InfoText',
                        selectedEntry.getProperty('InfoText'))

            if currentEntry != self.lastGuiList:
                self.lastGuiList = currentEntry
        
        if(controlID == self.sectionsList):
            selectedMenuItem = self.getControl(controlID).getSelectedItem()
            lastMenu = self.getControl(controlID).getSelectedPosition()
            if(selectedMenuItem != self.lastMenu):
                self.lastMenu = selectedMenuItem
                print("Not the same " + str(lastMenu))
                print("Label:" + selectedMenuItem.getLabel())
                self.buildParameterMenu(selectedMenuItem.getLabel())          
                
              
                li = self.getControl(controlID).getListItem(lastMenu)
                print("Sel mem item:" + selectedMenuItem.getLabel())
                print("Sel last menu item:" + li.getLabel())
                objList = self.getControl(int(selectedMenuItem.getProperty('listTyp')))
                self.getControl(controlID).controlRight(objList)
                #self.setFocusId(1100)
                #self.setFocusId(self.sectionsList)
                
                
        return
        
           
    def test(self):
        #self.getControl(1100).reset()
        dictProperties = {
                                'value': "test value",
                                'typ': "text",
                                'entry': "samba",
                                'category': "samba 2",
                                'action': 'set_value',
                                'order': 1
                                }
        print(str(self.getControl(1000).getSelectedItem().getProperty("listTyp")) + " listTyp")
        self.addConfigItem("test label", dictProperties, 1100)
        #self.getControl(1000).getSelectedItem().setProperty("listTyp", "1100")
        print(str(self.getControl(1000).getSelectedItem().getProperty("listTyp")) + " listTyp")
        self.getControl(1100).setVisible(True)
        
                    
    def addConfigItem(self, strName, dictProperties, strType ):

        try:

            lstItem = xbmcgui.ListItem(label=strName)
            lstItem.setProperty("listTyp", "1100")

            for strProp in dictProperties:
                lstItem.setProperty(strProp,
                                    unicode(dictProperties[strProp]))

            self.getControl(int(strType)).addItem(lstItem)
            
            print("addConfigItem")

            return lstItem
        except Exception, e:
            print(e)
            print("exception in adding to list")
            pass;
            

        

def parseConfFile():
    filePath = "%s/smb.conf" % __cwd__
    filePath = __cwd__ + "/smb.conf"

    text = ""

    with open(filePath) as cf:
        for line in cf:
            text = text + line.strip() + "\n"

    sections = re.findall("\[(.*?)\](.*?)(?=^\w*\[|\Z)", text, re.MULTILINE | re.DOTALL)
    
    parsedDic = {}
    for section in sections:
        print(section)
        paramsDic  = {}
        
        for paramWithValue in section[1].splitlines():
            
            if paramWithValue == "" or paramWithValue.startswith("#") \
                or paramWithValue.startswith("#"):
                continue;
            
            param, value = paramWithValue.split("=", 1)
            paramsDic[param.strip()] = value.strip()
        parsedDic[section[0]] = paramsDic;
        
    return parsedDic

def writeConfFile(config):
    text = ""

    for section in config.keys():
        t = "[" + section + "]\n"
        #print(section)
        params = config[section];
        for param, value in config[section].items():
            t = t + "\t" + param + " = " + value + "\n"
        text = ((t + text) if section == "global" else (text + t)) 
    print(text)
         
    

#conf = parseConfFile()
#a = {"sdfs": "sdf", "c" : "yes"}
#print(conf)
#conf["test"] = a
#writeConfFile(conf)
#window = xbmcgui.WindowXMLDialog('smbWindow.xml', __cwd__, 'Default');
window = smbWindow('mainWindow.xml', __cwd__, "Default", isChild=True)
window.doModal();