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
                
def matchFSM(thirdPaymentName, syndicationName):
    
    global all_chose
    all_chose = []
    get_all_chose(0, [])
    
    match_cnt = 0
    if thirdPaymentName == 'alipay':
        for one in all_chose:
            #match first state
            first_extension = [[4,11], [1,7,13,5], [2,6,4,11]]
            first_state = None
            if 4 in one:
                first_state = 0
            if 2 in one and 6 in one and 4 in one:
                first_state = 2
            if 1 in one and 7 in one and 5 in one and 13 in one:
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
                match_cnt = match_cnt + 1
                file = open('../data/tmp/extensionFSM/%s.%s.match.tmp.%d.txt'%(syndicationName, thirdPaymentName, match_cnt), 'w')
                FSM = first_extension[first_state] + [3] + second_extension[second_state]
                
                for id in range(0, len(SyndicationDocumentationEdge.keys())):
                    if one[id] in FSM:
                        file.write('>> edge:%d\n'%id)
                        file.write('%s edge number:%d\n'%(thirdPaymentName, one[id]))
                        file.write('<< end\n\n')
                
    elif thirdPaymentName == 'wechat':
        for one in all_chose:
            #match first state
            first_extension = [[4,15,11,12], [1,8,15,11,14,6], [2,5,4,15,11,12]]
            first_state = None
            if 4 in one:
                first_state = 0
            if 2 in one and 5 in one and 4 in one:
                first_state = 2
            if 1 in one and 8 in one and 14 in one and 6 in one:
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
                match_cnt = match_cnt + 1
                file = open('../data/tmp/extensionFSM/%s.%s.match.tmp.%d.txt'%(syndicationName, thirdPaymentName, match_cnt), 'w')
                FSM = first_extension[first_state] + [3] + second_extension[second_state]
                
                for id in range(0, len(SyndicationDocumentationEdge.keys())):
                    if one[id] in FSM:
                        file.write('>> edge:%d\n'%id)
                        file.write('%s edge number:%d\n'%(thirdPaymentName, one[id]))
                        file.write('<< end\n\n')

#if True!=False:

if __name__ == '__main__':

    #thirdPaymentName = 'wechat'#sys.argv[1]
    #syndicationName = 'umf'#sys.argv[2]

    #thirdPaymentName = sys.argv[1]
    #syndicationName = sys.argv[2]
    thirdPaymentName = 'alipay'
    syndicationName = '1beecloud'

    readThirdPaymentBasicEdge(thirdPaymentName)
    
    #readAllPossibleFSM(thirdPaymentName)

    readSyndicationDocumentationEdge(thirdPaymentName, syndicationName)

    match(thirdPaymentName, syndicationName)
    
