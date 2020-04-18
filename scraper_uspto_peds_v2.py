# -*- coding: utf-8 -*-
"""
Created on Sat Apr 11 15:03:05 2020

@author: tomyi
"""

import zipfile

import os
import json

import pandas as pd
import ijson 
import ijson.backends.yajl2_cffi as ijsonc

from yz.util import tic, toc

from contextlib import suppress



file_path = os.path.join(r'C:\Users\tomyi\Downloads', '2014.json')
file_name = '2014.json'

column_map = {1: 'applicationNumberText',
              2: 'applicationStatusCateogry',
              3: 'applicationStatusDate',
              4: 'applicationTypeCategory',
              5: 'filingDate',
              6: 'inventionTitle',
              7: 'applicantEntityName',
              8: 'applicantEntityCountry',
              9: 'inventorNAme',
              10:'inventorCountry',
              11:'classification_ip_office',
              12:'nationalClass',
              13:'nationalSubClass',
              14:'grantedDate',
              15:'grantedPatentNumber',
              16:'publicationDate',
              17:'rejectionNumber',
              18:'assigneeName',
              19:'correspondenceAddress'
              }


zip_dir = r"C:\Users\tomyi\Downloads\2000-2019-pairbulk-full-20200216-json.zip"


i_zipFile= zipfile.ZipFile(zip_dir)

###
# for 1 file ----
###

# step 1: decompress a file 

# with zipfile.ZipFile(zip_dir, 'r') as z:
#      z.extract(file_name, r'C:\Users\tomyi\Downloads')

# step 2: chunk reading json 




iter_items = ijsonc.kvitems(open(file_path, 'r', encoding="UTF-8"), 'PatentBulkData.item')

o_data = []
cnt = 0

tic()

#for item in iter_items:       
while True:
    
    item = next(iter_items)
    
    if item[0] == 'patentCaseMetadata':
        
        # prep var
        r_data = {}
        cnt += 1
        
        if cnt ==2500:
            break
        
        # general
        try:
            r_data[1] = item[1]['applicationNumberText']['value']
        except:
            pass
        try:
            r_data[2] = item[1]['applicationStatusCategory']
        except:
            pass
        try:
            r_data[3] = item[1]['applicationStatusDate']
        except:
            pass
        try:
            r_data[4] = item[1]['applicationTypeCategory']
        except:
            pass
        try:
            r_data[5] = item[1]['filingDate']
        except:
            pass
        try:
            r_data[6] = item[1]['inventionTitle']
        except:
            pass
        # party bag - applicant / inventor
        try:
            for i in range(len(item[1]['partyBag']['applicantBagOrInventorBagOrOwnerBag'])):
                if "{'applicant'" in str(item[1]['partyBag']['applicantBagOrInventorBagOrOwnerBag'][i])[:50]:
                    with suppress(Exception): r_data[7] = str( item[1]['partyBag']['applicantBagOrInventorBagOrOwnerBag'][i]['applicant'][0]['contactOrPublicationContact'][0]['name']['personNameOrOrganizationNameOrEntityName'][0] )
                    with suppress(Exception): r_data[8] = str( item[1]['partyBag']['applicantBagOrInventorBagOrOwnerBag'][i]['applicant'][0]['contactOrPublicationContact'][0]['countryCode'] )
                elif "{'inventorOrDeceasedInventor'" in str(item[1]['partyBag']['applicantBagOrInventorBagOrOwnerBag'][i])[:100]:
                    r_data[9] = str( item[1]['partyBag']['applicantBagOrInventorBagOrOwnerBag'][i]['inventorOrDeceasedInventor'][0]['contactOrPublicationContact'][0]['name']['personNameOrOrganizationNameOrEntityName'][0] )
                    r_data[10] = str( item[1]['partyBag']['applicantBagOrInventorBagOrOwnerBag'][i]['inventorOrDeceasedInventor'][0]['contactOrPublicationContact'][0]['countryCode'] )
        except:
            pass
        # patent classfication        
        try:
            r_data[11] = item[1]['patentClassificationBag']['cpcClassificationBagOrIPCClassificationOrECLAClassificationBag'][0]['ipOfficeCode']
        except:
            pass
        try:
            r_data[12] = item[1]['patentClassificationBag']['cpcClassificationBagOrIPCClassificationOrECLAClassificationBag'][0]['mainNationalClassification']['nationalClass']
        except:
            pass
        try:
            r_data[13] = item[1]['patentClassificationBag']['cpcClassificationBagOrIPCClassificationOrECLAClassificationBag'][0]['mainNationalClassification']['nationalSubclass']
        except:
            pass
        # patent grant
        try:
            r_data[14] = item[1]['patentGrantIdentification']['grantDate']
        except:
            pass
        try:
            r_data[15] = item[1]['patentGrantIdentification']['patentNumber']
        except:
            pass
        # publication
        try:
            r_data[16] = item[1]['patentPublicationIdentification']['publicationDate']
        except:
            pass
        
    
    elif item[0] == 'prosecutionHistoryDataBag':  
        t_pd = pd.DataFrame(item[1]['prosecutionHistoryData'], columns = ['eventDate','eventCode','eventDescriptionText'])        
        r_data[17] = sum(t_pd['eventCode'].str.strip().isin(['CTNF','CTFR'])) # CTNF Non-Final Rejection   CTFR Final Rejection  
    
    elif item[0] == 'patentTermData':
        pass
    
    elif item[0] == 'assignmentDataBag':
        try:
            r_data[18] = item[1]['assignmentData'][0]['assigneeBag']['assignee'][0]['contactOrPublicationContact'][0]['name']['personNameOrOrganizationNameOrEntityName'][0]['value']
        except:
            pass
        try:
            r_data[19] = str( item[1]['assignmentData'][0]['correspondenceAddress']['partyIdentifierOrContact'] )
        except:
            pass
        
    elif item[0] == 'st96Version':
        pass
        
    elif item[0] == 'ipoVersion':
        o_data.append(r_data)
    
    else:
        raise Exception('New info category found.')


toc()

# step 3: save the data to parquet 
# o_pd = pd.DataFrame(o_data).to_parquet(r'C:\Users\tomyi\.spyder-py3\LOGGING\uspto')


# step 4: delete a decompressed file 
# os.remove(file_path)