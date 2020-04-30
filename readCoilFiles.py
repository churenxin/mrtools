#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 15:38:56 2020

@author: cjm
"""

import json

#pyip.readCoilFiles.parseSiemens('./testData/16chbreast.xml.txt')

def parseSiemens(fileIn):
    import xml.etree.ElementTree as ET
    from parse import parse, search
    tree = ET.parse(fileIn)
    root = tree.getroot()
    
    dictOut=dict()
    
    for child in root.iter('Function'):
        parseOut=parse("Coil:{coilName} Mode:Coil SystemSerialNumber:{serialNumber}",child.get('Tags'))
        dictOut.update(parseOut.named)
        
        dictOut["startTime"]=child.get('Start')
        
        protocolCounter=0
        dictOut["Protocol"]=[]
        for heading in root.iter('Heading'):
            print(heading.get("Label"))
            if search("Protocol: ", heading.get("Label")):
                dictOut["Protocol"].append(heading.get("Label"))
                print(">>>" + heading.get("Label"))
           #dictOut["Protocol"][protocolCounter][]
        # print(child.tag)
        # if child.findall('IDREF'):
        #     print(child.get('IDREF'))
        
    return dictOut
    
    