import os
import sys
import copy

global ThirdPaymentBasicEdge
global AllPossibleFSM

global SyndicationDocumentationEdge

def readThirdPaymentBasicEdge(thirdPaymentName):

    file = open('../data/configure/standard_edge/edge.%s.txt'%thirdPaymentName)
    fileContent = file.readlines()
    file.close()

    global ThirdPaymentBasicEdge
    ThirdPaymentBasicEdge = {}

    edge_number = None
   
    for line in fileContent:
        if line.startswith('edge number:'):
            edge_number = int(line.split(':')[-1])
            ThirdPaymentBasicEdge[edge_number] = {}
        elif line.startswith('sender:'):
            ThirdPaymentBasicEdge[edge_number]['sender'] = line.split(':')[-1].strip()
        elif line.startswith('receiver:'):
            ThirdPaymentBasicEdge[edge_number]['receiver'] = line.split(':')[-1].strip()
        elif line.startswith('content:'):
            ThirdPaymentBasicEdge[edge_number]['content'] = line.split(':')[-1].strip()
        elif line.startswith('ask for api:'):
            ThirdPaymentBasicEdge[edge_number]['ask for api'] = line.split(':')[-1].strip()


def readAllPossibleFSM(thirdPaymentName):

    file = open('../data/configure/KB.%s.txt'%thirdPaymentName)
    fileContent = file.readlines()
    file.close()

    global AllPossibleFSM
    AllPossibleFSM = []

    oneFSM = []
    for line in fileContent:
        if line.startswith('>>'):
            oneFSM = []
        elif line.startswith('<< end'):
            AllPossibleFSM.append(oneFSM[:])
        elif '->' in line:
            sender = line.split('->')[0].strip()
            receiver = line.split('->')[-1].split(':')[0].strip()
            content = line.split(':')[-1].strip()
            if '@' in content:
                content = content.split('@')[0].strip()
                
            for id in ThirdPaymentBasicEdge.keys():
                if ThirdPaymentBasicEdge[id]['sender'] == sender and ThirdPaymentBasicEdge[id]['receiver'] == receiver and ThirdPaymentBasicEdge[id]['content'] == content:
                    oneFSM.append(id)
                    break
                    
def readSyndicationDocumentationEdge(thirdPaymentName, syndicationName):
    
    file = open('../data/tmp/matchStandardEdge/%s.edge.txt'%syndicationName)
    fileContent = file.readlines()
    file.close()
    
    global SyndicationDocumentationEdge
    SyndicationDocumentationEdge = {}
    
    edge_number = None
   
    for line in fileContent:
        if line.startswith('>> edge:'):
            edge_number = int(line.split(':')[-1])
            SyndicationDocumentationEdge[edge_number] = {}
        elif line.startswith('sender:'):
            SyndicationDocumentationEdge[edge_number]['sender'] = line.split(':')[-1].strip()
        elif line.startswith('receiver:'):
            SyndicationDocumentationEdge[edge_number]['receiver'] = line.split(':')[-1].strip()
        elif line.startswith('content:'):
            SyndicationDocumentationEdge[edge_number]['content'] = line.split(':')[-1].strip()
        elif line.startswith('%s edge number:'%thirdPaymentName):
            SyndicationDocumentationEdge[edge_number]['guess id of third payment basic edge'] = []
            for tmp in line.split(':')[-1].strip().split('|'):
                SyndicationDocumentationEdge[edge_number]['guess id of third payment basic edge'].append(int(tmp))

global all_chose
def get_all_chose(id, path):
    if id == len(SyndicationDocumentationEdge.keys()):
        global all_chose
        all_chose.append(path[:])
        return
    
    for tmp in SyndicationDocumentationEdge[id]['guess id of third payment basic edge']:
        path.append(tmp)
        get_all_chose(id+1, path)
        path.pop()
                
            
def output_result(syndicationName, thirdPaymentName, FSM, one):
    
    #print('debug:', FSM)
    
    file = open('../data/tmp/extensionFSM/%s.%s.txt'%(syndicationName, thirdPaymentName), 'w')
                
    cnt = 0
    for id in FSM:
        cnt = cnt + 1
        file.write('>> edge:%d\n'%cnt)
        file.write('edge number in knowledgebase:%d\n'%id)
                    
        lib4 = None
        try:
            lib4 = one.index(id)
        except Exception:
            lib4 = ''
        file.write('edge number in lib4:%s\n'%lib4)
                    
        file.write('sender:%s\n'%ThirdPaymentBasicEdge[id]['sender'])
        file.write('receiver:%s\n'%ThirdPaymentBasicEdge[id]['receiver'])

        file.write('content in knowledgebase:%s\n'%ThirdPaymentBasicEdge[id]['content'])

        lib4_content = None
        try:
            lib4 = one.index(id)
            lib4_content = SyndicationDocumentationEdge[lib4]['content']
        except Exception:
            lib4_content = ''
        file.write('content in lib4:%s\n'%lib4_content)
                    
        file.write('api in lib4:\n')
                    
        file.write('ask for api:%s\n'%ThirdPaymentBasicEdge[id]['ask for api'])
                        
        file.write('<< end\n\n')
                    
    file.close() 
            
            
def matchFSM(thirdPaymentName, syndicationName):
    
    global all_chose
    all_chose = []
    get_all_chose(0, [])
    
    #print('all:', all_chose)
    
    match_cnt = 0
    if thirdPaymentName == 'alipay':
        last_out_cnt = -1
        for one in all_chose:
            #match first state
            first_extension = [[4,11], [1,7,13,5], [2,6,4,11]]
            first_state = None
            if 4 in one:
                first_state = 0
            if 2 in one and 6 in one and 4 in one:
                first_state = 2
            if 1 in one and 7 in one:
                first_state = 1     
            if 13 in one and 5 in one:
                first_state = 1
    
            #match second state
            #possibleExtension([10,12], [9,8,12])
            second_extension=[[10,12], [9,8,12]]
            second_state = None
            if 12 in one:
                second_state = 0
            if 8 in one:
                second_state = 1
            
            if first_state == None or second_state == None:
                continue
            else:
                
                FSM = first_extension[first_state] + [3] + second_extension[second_state]
                outEdge = []
                for i in one:
                    if i not in FSM:
                        if i not in outEdge:
                            outEdge.append(i)
                
                if last_out_cnt != -1 and len(outEdge) > last_out_cnt:
                    continue
                    
                last_out_cnt = len(outEdge)
                            
                output_result(syndicationName, thirdPaymentName, FSM, one)               
                
    elif thirdPaymentName == 'wechat':
        last_out_cnt = -1
        for one in all_chose:
            #match first state
            first_extension = [[4,15,11,12], [1,8,15,11,14,6], [2,5,4,15,11,12]]
            first_state = None
            if 4 in one:
                first_state = 0
            if 2 in one and 5 in one and 4 in one:
                first_state = 2
            if 1 in one and 8 in one:
                first_state = 1                    
            if 14 in one and 6 in one:
                first_state = 1
    
            #match second state
            second_extension=[[10,13], [9,7,13]]
            second_state = None
            if 13 in one:
                second_state = 0
            if 7 in one:
                second_state = 1
            
            if first_state == None or second_state == None:
                continue
            else:    
                FSM = first_extension[first_state] + [3] + second_extension[second_state]
                outEdge = []
                for i in one:
                    if i not in FSM:
                        if i not in outEdge:
                            outEdge.append(i)
                
                if last_out_cnt != -1 and len(outEdge) > last_out_cnt:
                    continue
                    
                last_out_cnt = len(outEdge)
                            
                output_result(syndicationName, thirdPaymentName, FSM, one)
"""

if __name__ == '__main__':

    thirdPaymentName = sys.argv[1]
    syndicationName = sys.argv[2]

    readThirdPaymentBasicEdge(thirdPaymentName)
    
    #readAllPossibleFSM(thirdPaymentName)

    readSyndicationDocumentationEdge(thirdPaymentName, syndicationName)

    match(thirdPaymentName, syndicationName)
"""