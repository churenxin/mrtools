#!/usr/bin/env pythn3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 15:38:56 2020

@author: Chris MacLellan

Code for reading vendor coil testing files to something useful.
"""

def parseSiemens(fileIn):
    # Reads Siemens exar1 file to a python dictionary
    
    # Example usage
    #readCoilFiles.parseSiemens('/home/cjm/Projects/mrtools/sampleData/siemensCoil.xml')
    
    import xml.etree.ElementTree as ET
    from parse import parse, search
    tree = ET.parse(fileIn)
    root = tree.getroot()
    
    dictOut=dict()
    
    for child in root.iter('Function'):
        parseOut=parse("Coil:{coilName} Mode:Coil SystemSerialNumber:{serialNumber}",child.get('Tags'))
        dictOut.update(parseOut.named)
        
        dictOut["startTime"]=child.get('Start')
        
    parseString="CoilCheck.Evaluation-098{protocolName}-PC{protocolNumber:d}-{coilConfig}-{}.{quantity}"
    
    protocolsDict={}
    
    for number in root.findall('.//Numeric'):
        #print(number.get("ID"))
        parseResults=parse(parseString,number.get("ID"))

        if parseResults["protocolName"] not in protocolsDict:
            protocolsDict.update({parseResults["protocolName"]:{}})
        if parseResults["coilConfig"] not in protocolsDict[parseResults["protocolName"]]:
            protocolsDict[parseResults["protocolName"]].update({parseResults["coilConfig"]:{}})
        if parseResults["quantity"] not in protocolsDict[parseResults["protocolName"]][parseResults["coilConfig"]]:
            protocolsDict[parseResults["protocolName"]][parseResults["coilConfig"]].update({parseResults["quantity"]:{}})
        
        protocolsDict[parseResults["protocolName"]][parseResults["coilConfig"]][parseResults["quantity"]].update({"value":number.find('Value').text})
        if number.find('Range') is not None:
            protocolsDict[parseResults["protocolName"]][parseResults["coilConfig"]][parseResults["quantity"]].update({"min":number.find('Range').get("Min")})
            protocolsDict[parseResults["protocolName"]][parseResults["coilConfig"]][parseResults["quantity"]].update({"max":number.find('Range').get("Max")})
            if (number.find('Value').text>number.find('Range').get("Min")):
                protocolsDict[parseResults["protocolName"]][parseResults["coilConfig"]][parseResults["quantity"]].update({"result":"Pass"})

    dictOut.update(protocolsDict)
            
    return dictOut
    
def parseGE(fileIn):
    # Reads GE mcqa file to a python dictionary
    
    # Example usage
    #readCoilFiles.parseGE('/home/cjm/Projects/mrtools/sampleData/GE/mcqaExample.txt')
    
    dictOut={"test":[]}
    
    with open(fileIn,'r') as file:
        for line in file:
            lineList=line.split(" ")

            if lineList[0]=="#loct":
                dictOut.update({"stationName":lineList[-1].strip("\n")})
            
            if lineList[0]=="#com1":
                dictOut.update({"startTime":lineList[-1].strip("\n")})
                
            if lineList[0]=="#pass_fail":
                dictOut.update({"overallResult":lineList[-1].strip("\n")})
                
            if lineList[0]=="#coil_name":
                dictOut.update({"coilName":lineList[-1].strip("\n")})
 
            if lineList[0]=="#coil_serial":
                dictOut.update({"serialNumber":lineList[-1].strip("\n")})    

            if lineList[0].isnumeric():
                if len(dictOut["test"]) < int(lineList[0]):
                    dictOut["test"].append({"image":[]})
                if len(dictOut["test"][int(lineList[0])-1]) < int(lineList[1]):
                    if float(lineList[7])>float(lineList[3]):
                        tmpResult="Pass"
                    else:
                        tmpResult="Fail"
                    dictOut["test"][int(lineList[0])-1]["image"].append({"SN":{"value":lineList[7],"min":lineList[3],"result":tmpResult}})
    return dictOut

def genCoilReport(inDir,vendorString,**kwargs):
    import os
    if os.path.isdir(inDir):
        files=os.listdir(inDir)
    elif os.path.isfile(inDir):
        files=""
    
    if vendorString=="GE":
        readFun=parseGE
    elif vendorString=="Siemens":
        readFun=parseSiemens
    
    dictOut={}
    
    for coilReport in files:
        tmpDict=readFun(inDir + coilReport)
        #print(tmpDict["coilName"])
        dictOut.update({tmpDict["coilName"]+tmpDict["serialNumber"]:tmpDict})
        
    htmlStr=dict2html(dictOut,vendorString)
    
    if "outFile" in kwargs:
        htmlOut=open(kwargs["outFile"],"w")
        htmlOut.write(htmlStr)
        htmlOut.close()
    
    reportOut={"dict":dictOut,"html":htmlStr}
             
    return reportOut
    
def dict2html(inDict,vendorString):
    from jinja2 import Environment, FileSystemLoader, PackageLoader, select_autoescape
    
    import os.path
    
    env = Environment(
        loader=FileSystemLoader(os.path.join(os.path.dirname(__file__),"templates")),
        autoescape=select_autoescape(['html', 'xml'])
    )
    
    if vendorString=="GE":
        templateFun='mcqaReport.html'
    elif vendorString=="Siemens":
        templateFun='mcqaReport.html'
    
    template = env.get_template(templateFun)
    
    strOut=template.render(coilDict=inDict)
    
    return strOut