'''
Created on 21.11.2014

@author: smory
'''

# import xbmc
# import xbmcaddon
# import xbmcgui
# import os
import re
# import sys
# import urllib2
# 
# from xml.dom import minidom
# 
# __scriptid__ = "openelec.samba.settings";
# 
# __addon__ = xbmcaddon.Addon(id=__scriptid__);
# __cwd__ = __addon__.getAddonInfo('path');
# #__media__ = '%s/resources/skins/default/media/' % __cwd__
# 
# 
# class smbWindow(xbmcgui.WindowXMLDialog):
# 
#     def __init__(self, *args, **kwargs):
# 
#         self.visible = False
# 
#         self.sectionsList = 1000
#         self.guiList = 1100
#         self.guiNetList = 1200
#         self.guiBtList = 1300
#         self.guiOther = 1900
# 
#         self.guiLists = [1000, 1100]
# 
#         self.buttons = {
#             1: {'id': 1500, 'modul': '', 'action': ''},
#             2: {'id': 1501, 'modul': '', 'action': ''},
#             3: {'id': 1502, 'modul': '', 'action': ''},
#             4: {'id': 1503, 'modul': '', 'action': ''},
#             5: {'id': 1504, 'modul': '', 'action': ''},
#             }
# 
#         self.isChild = False
#         self.lastGuiList = -1
#         self.lastListType = -1
#               
#         if 'isChild' in kwargs:
#             self.isChild = True
# 
#         pass
# 
#     def onInit(self):
#       
#         self.visible = True
#                 
#         try:
# 
#             if self.isChild:
#                 self.setFocusId(self.sectionsList)
#                 self.onFocus(self.sectionsList)
#                 return
# 
#           
#             self.setProperty('DIST_MEDIA', 'default')
#             
#             sections = {"global": "", "test":""}
#             
# 
#             for section in sections.keys():
#                 self.addMenuItem(section, {})
# 
#             self.setFocusId(self.sectionsList)
#             self.onFocus(self.sectionsList)
# 
#         except Exception, e:
#             pass
#             
#     def addMenuItem(self, strName, dictProperties):
# 
#         try:
# 
#             lstItem = xbmcgui.ListItem(label=strName);
# 
#             for strProp in dictProperties:
#                 lstItem.setProperty(strProp, unicode(dictProperties[strProp]))
# 
#             self.getControl(self.sectionsList).addItem(lstItem)
#         except Exception, e:
#             pass

def parseConfFile():
    filePath = "smb.conf"

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
         
    

conf = parseConfFile()
a = {"sdfs": "sdf", "c" : "yes"}
print(conf)
conf["test"] = a
writeConfFile(conf)
#window = xbmcgui.WindowXMLDialog('smbWindow.xml', __cwd__, 'Default');
# window = smbWindow('smbWindow.xml', __cwd__, "Default")
# window.doModal();