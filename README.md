# Dilution

We will release the tool and source code of Dilution by the start of the 28th USENIX Security Symposium, 2019.

Expect our release!


Prerequisite
============
Download and install LTP model: [LTP](http://ltp.ai/docs/index.html)

Quick Start
===========
Usage : run ./code/main.py [syndicator name] [path to LTP model]

Input file: 
>Three kinds of input are required:
   >> 1. **payment process** : a document with sentences that describe the necessary procedures in payment process.  
   >>2. **API list**: a document where each line stands an API of the syndicator.  
   >>3. **API parameter description**: each API has a document with each line formed by:
   >>>[parameter name]\*\*\*[parameter description].   
   
   >All the input files are in the folder: _'./data/input'_.
   >Put the **payment process** in _'./data/input/payDocument'_, the **API list** in _'./data/input/apiList'_, and the **API parameter description** in _'./data/input/apiDescription'_.

Data format: 
>The required data format is shown in the sample of "Beecloud": 
>>Name the document of **payment process** and **API list** as  "[Sindicator name].txt".   
>>For  **API parameter description**, build a directory as "[Syndicator name]" in _./data/input/apiDescription_, where each API has a document named as "[API name]-[third payment name]-[post/receive].txt".  

In this project we utilized 'alipay' and 'wechat' as the third payment.  
