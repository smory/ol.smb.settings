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
import threading
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
 
        self.buttons = {1500: "add share", 1501 : "remove share", 1502 : "parameter info", 1503 : "add parameter", 1504 : "remove parameter"}
 
        self.isChild = False
        self.lastGuiList = -1
        self.lastListType = -1
               
        if 'isChild' in kwargs:
            self.isChild = True
            
        self.sambaDoc = None
        
        thread = threading.Thread(target = self.parseSambaDoc)
        thread.start()
 
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
 
            self.setFocusId(self.sectionsList)
            self.onFocus(self.sectionsList)
            
            for id in self.buttons.keys():
                self.getControl(id).setLabel(self.buttons[id])
             
        except Exception, e:
            print(sys.exc_info())
            print( traceback.format_exc())

    
    def onAction(self, action):
        #print("on action")
        
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

                #self.setProperty('InfoText',
                 #                self.sambaDoc.get(nextItem.getLabel())[1] if self.sambaDoc is not None else "" )

        if focusId == self.sectionsList:
            self.setFocusId(focusId)
        
    def buildParameterMenu(self, sectionId):
        parameters = self.sambaConfig[sectionId]
        items = []
        for param in sorted(parameters.keys()):
            listItem = xbmcgui.ListItem(label = param)
            listItem.setProperty("value", parameters[param])
            listItem.setProperty("sectionId", sectionId)
            
            if(param == "path"):
                listItem.setProperty("typ", "folder")
                items.insert(0, listItem);
                continue;
                
            elif(re.match("yes|no|true|false", parameters[param], re.IGNORECASE)):
                listItem.setProperty("typ", "bool")
                if re.match("yes|true", parameters[param], re.IGNORECASE):
                    listItem.setProperty("value", "1")
                else:
                    listItem.setProperty("value", "0")    
                          
            else:
                listItem.setProperty("typ", "text")
            
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
                    'C:/',
                    )
                if returnValue != '':
                    selectedItem.setProperty('value', unicode(returnValue))
                    
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
                    
            # reflect changes made in gui in config dic    
            if(strTyp == 'bool'):
                self.sambaConfig[selectedItem.getProperty("sectionId")][selectedItem.getLabel()] = \
                    ("yes" if selectedItem.getProperty('value') == "1" else "no")
            else:
                self.sambaConfig[selectedItem.getProperty("sectionId")][selectedItem.getLabel()] = \
                    selectedItem.getProperty('value')
                    
        if(controlID in self.buttons.keys()):
            if(controlID == 1500):
                self.addShare()
                
            elif(controlID == 1501):
                self.removeShare()
                
            elif(controlID == 1502):
                self.showParamInfo()
            
            elif(controlID == 1503):
                self.addParameter()
                
            elif(controlID == 1504):
                self.removeParameter()
                

    
    def addShare(self):
        
        shareName = ""
        sharePath = ""
        
        keyboard = xbmc.Keyboard(heading = "Enter share name")
        keyboard.doModal()        

        if(keyboard.isConfirmed()):
            shareName = keyboard.getText()
            if(not shareName):
                return
            
        xbmcDialog = xbmcgui.Dialog()
        sharePath = xbmcDialog.browse(
                    0,
                    'OpenELEC.tv',
                    'files',
                    '',
                    False,
                    False,
                    'C:/',
                    )
        
        if(not sharePath):
            return
        
        globalConfig = self.sambaConfig["global"]
        
        params = {"path" : sharePath, "available" : "yes"}
        # take into account global settings with its synonyms in parameters
        params["browsable"] = globalConfig["browsable"] if globalConfig.get("browsable") is not None \
            else globalConfig["browseable"]if globalConfig.get("browseable") is not None else "yes"
        params["writable"] = globalConfig["writable"] if globalConfig.get("writable") is not None \
            else globalConfig["writeable"]if globalConfig.get("writeable") is not None else "yes"
        params["public"] = globalConfig["public"] if globalConfig.get("public") is not None \
            else globalConfig["guest ok"]if globalConfig.get("guest ok") is not None else "yes"
        
        self.addMenuItem(shareName, params)
        self.sambaConfig[shareName] = params

    def removeShare(self):
        shares = self.sambaConfig.keys()
        #shares = []
        shares.remove("global") # don't allow to remove global settings
        shares.sort()
               
        selected = xbmcgui.Dialog().select("Choose share", shares)
        if(selected is None or selected == -1):
            return
        
        shareToDelete = shares[selected]
        
        selectedInMenu = False
        for i in range(0, self.getControl(self.sectionsList).size()):
            listItem = self.getControl(self.sectionsList).getListItem(i)
            if(listItem.getLabel() == shareToDelete):
                selectedInMenu = True if self.getControl(self.sectionsList).getSelectedItem().getLabel() == shareToDelete \
                    else False
                self.getControl(self.sectionsList).removeItem(i)
                print("item removed")
                break
            
        del self.sambaConfig[shareToDelete]
        
        # select first item in the menu if removed share was focused
        if(selectedInMenu):
            self.getControl(self.sectionsList).selectItem(0)
            self.buildParameterMenu(self.getControl(self.sectionsList).getListItem(0).getLabel())                        
        
    def showParamInfo(self):
        paramName = self.getControl(self.paramList).getSelectedItem().getLabel()
        text = self.sambaDoc.get(paramName)[1] if self.sambaDoc is not None else "" 
        window = xbmcgui.WindowXMLDialog("DialogTextViewer.xml", __cwd__, 'Default')
        window.show()
        window.getControl(1).setLabel(paramName)
        window.getControl(5).setText(text)
        window.doModal()
        
        
        del window;
        
    def addParameter(self):
        parameter = ""
        value = ""
        
        keyboard = xbmc.Keyboard()
        keyboard.setHeading("Enter parameter")
        keyboard.doModal()        

        if(keyboard.isConfirmed()):
            parameter = keyboard.getText()
            if(not parameter):
                return
        
        cont = True    
        if(self.sambaDoc is not None):
            found = self.sambaDoc.get(parameter)
            if(found is None):
                xbmcgui.Dialog().ok("OpenELEC", "Parameter is mistyped")
                cont = False
                self.addParameter()
        else:
            cont = xbmcgui.Dialog().yesno("OpenELEC", "Unable to verify parameter for misspelling.", "Continue?")
        
        if(not cont):
            return
            
        keyboard = xbmc.Keyboard()
        keyboard.setHeading("Enter value")
        keyboard.doModal()        

        if(keyboard.isConfirmed()):
            value = keyboard.getText()
            if(not value):
                return
        section = self.getControl(self.paramList).getSelectedItem().getProperty("sectionId")
        self.sambaConfig[section][parameter] = value
        self.buildParameterMenu(section)        
        
    def removeParameter(self):
        section = self.getControl(self.paramList).getSelectedItem().getProperty("sectionId")
        params = self.sambaConfig[section].keys()
        
        try:
            params.remove("path")  # prevent user from deleting path parameter
        except:
            pass  # no need to handle as only global section could throw
        
        params.sort()
        
        selected = xbmcgui.Dialog().select("Choose parameter", params)
        if(selected is None or selected == -1):
            return
        
        paramToDelete = params[selected]
        print("param to delete> " + paramToDelete)
        
        dialog = xbmcgui.Dialog() 
        confirmed = dialog.yesno("Confirmation", "Are you sure?")
        
        if(confirmed):
            del self.sambaConfig[section][paramToDelete]
            self.buildParameterMenu(section)
        
        
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
        
         
    def addMenuItem(self, strName, dictProperties):
 
        try:
 
            listItem = xbmcgui.ListItem(label=strName)
            listItem.setProperty("listTyp", "1100")
 
            for strProp in dictProperties:
                listItem.setProperty(strProp, unicode(dictProperties[strProp]))
 
            self.getControl(self.sectionsList).addItem(listItem)
        except Exception, e:
            pass
        
    def onFocus(self, controlID):
        
        #print("on fokus")
        
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
                #print("Not the same " + str(lastMenu))
                #print("Label:" + selectedMenuItem.getLabel())
                self.buildParameterMenu(selectedMenuItem.getLabel())          
                
              
                #li = self.getControl(controlID).getListItem(lastMenu)
                #print("Sel mem item:" + selectedMenuItem.getLabel())
                #print("Sel last menu item:" + li.getLabel())
                objList = self.getControl(int(selectedMenuItem.getProperty('listTyp')))
                self.getControl(controlID).controlRight(objList)
                         
    def addConfigItem(self, strName, dictProperties, strType ):

        try:

            lstItem = xbmcgui.ListItem(label=strName)
            lstItem.setProperty("listTyp", "1100")

            for strProp in dictProperties:
                lstItem.setProperty(strProp,
                                    unicode(dictProperties[strProp]))

            self.getControl(int(strType)).addItem(lstItem)
            return lstItem
        
        except Exception, e:
            print(e)
            print("exception in adding to list")
            pass;
        
    
    def parseSambaDoc(self):
    
        regexParamName = "<h3.*?</a>\s*([\w\s]+?)\s?(\((G|S)\))?\s*</h3>"
        regexParamPart = "<div\sclass=\"section\"(.*?</dd>)</dl></div></div>"
        regexParamDesc = "<dd>.*?</dd>"
        
        data = urllib2.urlopen("http://www.samba.org/samba/docs/man/manpages/smb.conf.5.html")
        source = data.read()
        
        sourceEntries = re.findall(regexParamPart, source, re.MULTILINE | re.DOTALL)
        del source, data
        
        dic = {}
        for entry in sourceEntries:
            
            paramNameMatch = re.search(regexParamName, entry, re.MULTILINE | re.DOTALL)
            
            if(paramNameMatch):
                paramName = paramNameMatch.group(1)
                paramSection = paramNameMatch.group(3)            
                
                decsHtml = re.search(regexParamDesc, entry, re.MULTILINE | re.DOTALL)          
                description  = ""
                description = re.sub("<.*?>", "", decsHtml.group(0), flags = re.MULTILINE | re.DOTALL)
                description = re.sub("\s{2,}", " ", description, flags = re.MULTILINE | re.DOTALL)
                description = description.strip()
                    
                dic[paramName]= [paramSection, description]
                del paramNameMatch, paramName, paramSection, description, decsHtml
                
        del sourceEntries
        print("samba doc done")
        self.sambaDoc = dic
        return(dic)


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
         

window = smbWindow('mainWindow.xml', __cwd__, "Default", isChild=True)
window.doModal();