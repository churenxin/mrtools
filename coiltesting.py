#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 15:38:56 2020

@author: Chris MacLellan

Code for reading vendor coil testing files to something useful.
"""
from tkinter import filedialog as fd
import re
import pprint

pp = pprint.PrettyPrinter(indent=2)

def parseSiemens(fileIn):
    # Reads Siemens xml file to a python dictionary
    
    # Example usage
    #mrtools.coiltesting.parseSiemens('/home/cjm/Projects/mrtools/sampleData/siemensCoil.xml')
    
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
    
    passFail="Pass"
    
    for number in root.findall('.//Numeric'):
        #print(number.get("ID"))
        parseResults=parse(parseString,number.get("ID"))

        if parseResults["protocolName"] not in protocolsDict:
            protocolsDict.update({parseResults["protocolName"]:{"config":{}}})
        if parseResults["coilConfig"] not in protocolsDict[parseResults["protocolName"]]["config"]:
            protocolsDict[parseResults["protocolName"]]["config"].update({parseResults["coilConfig"]:{}})
        if parseResults["quantity"] not in protocolsDict[parseResults["protocolName"]]["config"][parseResults["coilConfig"]]:
            protocolsDict[parseResults["protocolName"]]["config"][parseResults["coilConfig"]].update({parseResults["quantity"]:{}})
        
        protocolsDict[parseResults["protocolName"]]["config"][parseResults["coilConfig"]][parseResults["quantity"]].update({"value":number.find('Value').text})
        if number.find('Range') is not None:
            protocolsDict[parseResults["protocolName"]]["config"][parseResults["coilConfig"]][parseResults["quantity"]].update({"min":number.find('Range').get("Min")})
            protocolsDict[parseResults["protocolName"]]["config"][parseResults["coilConfig"]][parseResults["quantity"]].update({"max":number.find('Range').get("Max")})
            if (number.find('Value').text>number.find('Range').get("Min")):
                protocolsDict[parseResults["protocolName"]]["config"][parseResults["coilConfig"]][parseResults["quantity"]].update({"result":"Pass"})
            else:
                protocolsDict[parseResults["protocolName"]]["config"][parseResults["coilConfig"]][parseResults["quantity"]].update({"result":"Fail"})
                passFail="Fail"

    dictOut.update({"protocols":protocolsDict})
    
    dictOut.update({"overallResult":passFail})
    
    #pp.pprint(dictOut)        
    return dictOut
    
def parseGE(fileIn):
    # Reads GE mcqa file to a python dictionary
    
    # Example usage
    #mrtools.coiltesting.parseGE('/home/cjm/Projects/mrtools/sampleData/GE/mcqaExample.txt')
    
    import datetime

    dictOut={"test":[]}
    
    with open(fileIn,'r') as file:
        for line in file:
            lineList=line.split(" ")

            if lineList[0]=="#loct":
                dictOut.update({"stationName":lineList[-1].strip("\n").capitalize()})
            
            if lineList[0]=="#com1":
                #dictOut.update({"startTime":lineList[-1].strip("\n")})
                dictOut.update({"startTime":datetime.datetime.strptime(lineList[-1].strip("\n"),'%Y_%m_%d_%H_%M_%S')})

            if lineList[0]=="#pass_fail":
                dictOut.update({"overallResult":lineList[-1].strip("\n").capitalize()})
                
            if lineList[0]=="#coil_name":
                dictOut.update({"coilName":lineList[-1].strip("\n")[:-4]})
 
            if lineList[0]=="#coil_serial":
                dictOut.update({"serialNumber":lineList[-1].strip("\n")})    

            if lineList[0].isnumeric():
                if len(dictOut["test"]) < int(lineList[0]):
                    dictOut["test"].append({"image":[]})
                if len(dictOut["test"][int(lineList[0])-1]) <= int(lineList[1]):
                    if float(lineList[7])>float(lineList[3]):
                        tmpResult="Pass"
                    else:
                        tmpResult="Fail"
                    dictOut["test"][int(lineList[0])-1]["image"].append({"SN":{"value":lineList[7],"min":lineList[3],"result":tmpResult}})
    #print(dictOut)
    return dictOut

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
        templateFun='siemensCoilReport.html'
    
    template = env.get_template(templateFun)
    
    strOut=template.render(coilDict=inDict)
    
    return strOut

def genCoilReport(inDir,**kwargs):
    # Create a coil testing report in html and or pdf format

    # Example usage
    # mrtools.coiltesting.genCoilReport('/media/cjm/WESTPREMIER/coils/',"GE",outFile="/media/cjm/WESTPREMIER/PremierAcceptanceCoils.html")
    # kwargs: outfile=full path to output file

    import pathlib #,pdfkit
    
    inDirPath=pathlib.Path(inDir)

    if inDirPath.is_dir():
        #files=os.listdir(inDir)
        files=inDirPath.iterdir()
    elif inDirPath.is_file():
        files=""
    
    #if vendorString=="GE":
    #    readFun=parseGE
    #elif vendorString=="Siemens":
    #    readFun=parseSiemens
    
    dictOut={}
    
    for coilReport in files:    
        with open(coilReport,encoding='utf-8-sig') as f:
            first_line = f.readline()
            f.close()
                    
        if isinstance(re.match("^<\?xml",first_line),re.Match):
            vendorString="Siemens"
            readFun=parseSiemens
        else:
            vendorString="GE"
            readFun=parseGE
        print(vendorString)
            
        tmpDict=readFun(inDirPath / coilReport)
        dictOut.update({tmpDict["coilName"]+tmpDict["serialNumber"]:tmpDict})
    
    #pp.pprint(dictOut)        
        
    htmlStr=dict2html(dictOut,vendorString)
    
    if "outFile" in kwargs:
        #FIXME path needs to have html extensions and automatically makes pdf; should change to have no extension and add kwarg to specify output file type
        htmlOut=open(kwargs["outFile"],"w")
        htmlOut.write(htmlStr)
        htmlOut.close()
        #pdfkit.from_file(kwargs["outFile"], kwargs["outFile"][:-5] + '.pdf')
    
    reportOut={"dict":dictOut,"html":htmlStr}
             
    return reportOut

###
def main():
    print("Hello!")
    inputFile = fd.askdirectory()
    outputFile = fd.asksaveasfilename()
    
    genCoilReport(inputFile,outFile=outputFile)

if __name__ == "__main__":
    main()