'''
Created on 27.11.2014

@author: psmorada
'''

import urllib2
import re

def parseSambaDoc():
    
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
    return(dic)

doc = parseSambaDoc()
print(doc["writable"])