# Dilution

Prerequisite
============
Download and install LTP model: [LTP](http://ltp.ai/docs/index.html) which consists of two parts:ltp and ltp_data. Here we make use of ltp_data(in version 3.4.0).

>install the sub module by pip:  `pip install pyltp`
                                 `pip install gensim`

The LIBSVM model(version 3.23): [LIBSVM](https://www.csie.ntu.edu.tw/~cjlin/libsvm/) has already been concluded in _./code_.

Quick Start
===========
Usage : run ./code/main.py [syndicator name] \[_path to ltp_data_\]   

Examples: We put three syndications in '_./data/input_' as examples.


Input & Data format: 
>Three kinds of input are required:
   >> 1. **payment process** : a document with sentences that describe the necessary procedures in payment process.  
   >>2. **API list**: a document where each line stands an API of the syndicator.  
   >>3. **API parameter description**: each API has a document with each line formed by:
   >>>[parameter name]\*\*\*[parameter description].    
   
>Location:  
   >>All the input files are in the folder: _'./data/input'_.  
   >>Put the **payment process** in _'./data/input/payDocument'_, the **API list** in _'./data/input/apiList'_, and the **API parameter description** in _'./data/input/apiDescription'_.  

   
>File Naming:  
>>Name the document of **payment process** and **API list** as  "[Sindicator name].txt".   
>>For  **API parameter description**, build a directory as "[Syndicator name]" in _./data/input/apiDescription_, where each API has a document named as "[API name]-[third payment name]-[post/receive].txt".  

In this project we utilized 'Alipay' and 'Wechat' as the third payment.  

Output:
> The prediction result of logic vulnerability prediction is in _'./data/output/result'_



