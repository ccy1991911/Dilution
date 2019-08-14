# coding:utf-8
PN=4
test=0
version='0813'
guess_party=0
print_match=0
print_edges=0


import csv
import re
import os
from similarity import *

class State():

    def __init__(self):
        self.edge_id = None

        self.original_sentence = ''
        self.sentence = ''

        self.sender = ''
        self.receiver = ''
        self.content = ''

        self.id_in_kb = None

        self.api_interface = ''
        self.send_parameter = ''
        self.receive_parameter = ''

        self.checkpoint = ''

        self.feature = []
        self.label = -1

# result: [edge number, sender, receiver, [content]]
# results: [result]
def read_edges(filename):
    results=[]
    result=[]
    lines=open(filename,'r').readlines()
    for line in lines:
        line=line.strip('\n\r').replace(' ','')
        if line.startswith('edgenumber'):
            result.append(line.replace('edgenumber:',''))
        if line.startswith('sender'):
            result.append(line.replace('sender:',''))
        if line.startswith('receiver'):
            result.append(line.replace('receiver:',''))
        if line.startswith('content'):
            content=line.replace('content:','')
            if content.count('|')>0:
                result.append(content.split('|'))
            else:
                result.append([content])
            results.append(result)
            result=[]
    return results



def party_id(party):
    if party.count('商户客户端')>0: return 0
    if party.count('商户服务器')>0: return 1
    if party.count('支付渠道')>0: return 2
    if party.count('第四方')>0: return 3
    if party.count('服务器')>0: return 4
    return -1

def id_party(id):
    if id==0: return '商户客户端'
    if id == 1: return '商户服务器'
    if id == 2: return '支付渠道'
    if id==3: return '第四方服务器'
    if id==4: return '服务器'
    if id<0: return 'None'
    return '其他'


def make_thresh(e_content,content):
    if e_content.count('支付') > 0 and content.count('支付') > 0 and len(e_content) == len(content):
        thresh = 0.91
    #elif e_content.count('信息') > 0 and content.count('信息') > 0 :
        #thresh = 0.86
    else: thresh = 0.87
    return thresh
# party id to be found, existed party type,existed party id


def find_party(party,party_type,id,r_content,edges):

    found_party_ids=[]
    max_sim=0
    sim_party=[]
    for e in edges:
        e_sender_id = party_id(e[1])
        e_receiver_id = party_id(e[2])
        e_contents = e[3]
        if party_type=='sender' and id==e_sender_id:
            for e_content in e_contents:
                thresh=make_thresh(e_content,r_content)

                s1 = phrase_to_sequence(e_content)
                s2 = phrase_to_sequence(r_content)
                cos_sim = phrase_similarity(s1, s2)
                #print e_content, content, thresh,cos_sim,max_sim
                if party.count('服务器') > 0:
                    if cos_sim >= max_sim and e[2].count('服务器')>0 and  cos_sim > thresh:
                        max_sim = cos_sim
                        sim_party.append([cos_sim,e_receiver_id])

                elif cos_sim>=max_sim and cos_sim > thresh:
                    max_sim=cos_sim
                    #print max_sim, thresh
                    sim_party.append([cos_sim, e_receiver_id])

        elif party_type=='receiver' and id==e_receiver_id:
            for e_content in e_contents:
                thresh = make_thresh(e_content, r_content)
                s1 = phrase_to_sequence(e_content)
                s2 = phrase_to_sequence(r_content)
                cos_sim = phrase_similarity(s1, s2)
                if party.count('服务器') > 0:
                    if cos_sim >= max_sim and e[1].count('服务器')>0 and  cos_sim > thresh:
                        max_sim = cos_sim
                        sim_party.append([cos_sim, e_sender_id])
                elif cos_sim >= max_sim  and cos_sim > thresh:
                    max_sim = cos_sim
                    sim_party.append([cos_sim, e_sender_id])
   # print sim_party
    for item in sim_party:
        if item[0] == max_sim:
            if item[1] not in found_party_ids:
                found_party_ids.append(item[1])

    return found_party_ids



def edge_matching(edges,sender_id,receiver_id,content):
    e_ns, sim_edge, can_edges, can_ens, = [],[], [], []
    ens=''
    max_sim=0

    for edge in edges:
        edge_number = edge[0]
        edge_sender_id, edge_receiver_id, edge_contents = party_id(edge[1]), party_id(edge[2]), edge[3]
        if edge_sender_id == sender_id and edge_receiver_id == receiver_id:

            for edge_content in edge_contents:  # 一条边上的所有content
                can_edges.append([edge_number,edge_content])
                if edge_number not in can_ens:
                    can_ens.append(edge_number)
    if len(can_ens)==1:
        en=can_edges[0][0]
        e_content=can_edges[0][1]
        sim_thresh = make_thresh(e_content, content)
        for i in range(len(can_edges)):
            e_content=can_edges[i][1]
            cos_sim= similarity(e_content,content)
            if print_match:
                print "single:", en, ' ', e_content, ' ', content, ' ', cos_sim, ' ', sim_thresh

            if cos_sim>sim_thresh:

                return en
    elif len(can_ens)>1:
        for en in can_ens:

            for i in range(len(can_edges)):
                if can_edges[i][0]==en:
                    e_content=can_edges[i][1]
                    sim_thresh = make_thresh(e_content, content)
                    cos_sim=similarity(e_content,content)
                    if print_match:
                        print "multi", en, ' ', e_content, ' ', content, ' ', cos_sim
                    if cos_sim>=max_sim and cos_sim>sim_thresh:

                        sim_edge.append([cos_sim,en])
                        max_sim=cos_sim
        for i in range(len(sim_edge)):
            if sim_edge[i][0]==max_sim:
                if sim_edge[i][1] not in e_ns:
                    e_ns.append(sim_edge[i][1])
        for i in range(len(e_ns)):

            ens += e_ns[i]
            if i < len(e_ns)-1:
                ens += '|'
        return ens

def print_edge(edges):
    for edge in edges:
        edge_number = edge[0]
        edge_sender_id, edge_receiver_id, edge_contents = party_id(edge[1]), party_id(edge[2]), edge[3]
        print '[',edge_number,']',edge_sender_id,':',edge_receiver_id,
        for content in edge_contents:
            print content,
        print '\r'



def writeFileMatchStandardEdge(f,edge_id,o_sentence,sentence,sender,receiver,content,sender_type,receiver_type,a_en,we_en,platform,api_name):

    w=csv.writer(f)
    w.writerow(['>> edge:' + str(edge_id)])
    w.writerow(['original sentence:' + o_sentence])
    w.writerow(['sentence:' + sentence])
    w.writerow(['sender:' + sender_type])
    w.writerow(['receiver:' + receiver_type])
    #w.writerow(['sender:' + sender.replace('NotFound', '')])
    #w.writerow(['receiver:' + receiver.replace('NotFound', '')])
    w.writerow(['content:' + content])
    w.writerow(['api:'+api_name])
    w.writerow(['alipay edge number:' + a_en])
   # w.writerow(['alipay parameter send:'])
    w.writerow(['alipay parameter receive:'])
    w.writerow(['wechat edge number:' + we_en])
   # w.writerow(['wechat parameter send:'])
    w.writerow(['wechat parameter receive:'])
    w.writerow(['<< end'])
    f.write('\n')

def edge_assign(edge,edge_id,o_sentence,sentence,content,sender_type,receiver_type,a_en,we_en,api_name):
    edge.edge_id = edge_id

    edge.original_sentence = o_sentence
    edge.sentence = sentence

    edge.sender = sender_type
    edge.receiver = receiver_type
    edge.content = content
    edge.api_name = api_name

    edge.alipay_en = a_en
    edge.wechat_en = we_en


def readFromFSM(filename):
    ek = em = sender = receiver = contents_k = content = api = ''
    results=[]
    lines=open(filename,'r').readlines()
    for line in lines:
        line=line.strip('\r\n')
        if line.startswith('edge number in knowledgebase:'):
            ek=line.replace('edge number in knowledgebase:','')
        if line.startswith('edge number in lib4:'):
            em=line.replace('edge number in lib4:','')
        if line.startswith('sender:'):
            sender=line.replace('sender:','')
        if line.startswith('receiver:'):
            receiver=line.replace('receiver:','')
        if line.startswith('content in knowledgebase:'):
            contents_k = line.replace('content in knowledgebase:', '')
        if line.startswith('content in lib4:'):
            content = line.replace('content in lib4:', '')
        if line.startswith('api in lib4:'):
            api = line.replace('api in lib4:', '')
        if line.startswith('ask for api:'):
            ask= line.replace('ask for api:', '')
            results.append([ek,em,sender,receiver,contents_k,content,api,ask])
    return results

def readApiList(platform):
    data=[]
    filename='../data/input/apiList/'+platform+'.txt'
    lines = open(filename, 'r').readlines()
    for line in lines:
        line = line.strip('\n\r')
        if line.count('|')>0:
            line=line.split('|')
            for item in line:
                data.append(item)
        elif line != '':
            data.append(line)
    return data


def writeFileAPI(edge_id,f,result,api):
    #alipay_parameter_send = findParameterOfApi(api, result[0])
    f.write('>> edge: '+str(edge_id)+'\n')
    f.write('edge number in knowledgebase:'+result[0]+'\n')
    f.write('edge number in lib4:'+result[1]+'\n')
    f.write('sender:'+result[2]+'\n')
    f.write('receiver:'+result[3]+'\n')
    f.write('content in knowledgebase:'+result[4]+'\n')
    f.write('content:'+result[5]+'\n')
    f.write('api name:'+result[6]+'\n')
    f.write('api interface:'+api+'\n')
    f.write('ask for api:'+result[7]+'\n')
    f.write('<< end\n\n')



def makeThreshAPI(c1,c2):
    if c1.count('支付')>0 and c2.count('支付')>0 and len(c1)==len(c2):
        thresh=0.91
    else:
        thresh=0.87

    return thresh


def extract_api(string):
    api=''
    if len(string)>0:
        api=string
        if string.count('的')>1:
            pattern=re.compile('的.*的',re.S)

            api=re.findall(pattern,string)
        api=api[0].replace('的','')
    return api


def makeThreshForParameter(c1,c2):
    payment_specific = filetolist('../data/configure/payment_specific')
    thresh = 0.96
    for p in payment_specific:
        if c1.count(p)>0 and c2.count(p)>0 and c1.count('预')==0:
            thresh=0.97
    return thresh


def get_first_phrase(p):
    marks=[',','，',':','：','.','。']
    for mark in marks:
        if p.count(mark)>0:
            p=p.split(mark)
            for m in marks:
                if p[0].count(m)>0:
                    new_p=p[0].split(m)
                    return new_p[0]
            return p[0]
    return p


def checkParameterInAllApis(platform):
    resultdir = "../data/tmp/parameter/"
    all_parameter = file_to_matrix('../data/configure/parameter', ',')
    makedir(resultdir + platform)
    for parent, dirs, filenames in os.walk("../data/input/apiDescription/"+platform):
        for filename in filenames:
            if filename.startswith('.'): continue
            parameter_result = []
            p_list = filetolist("../data/input/apiDescription/"+platform+"/"+filename)
            for p in p_list:
                max_sim, max_parameter = 0, -1
                max_item, max_phrase= '',''
                phrase = get_first_phrase(p)
                phrase = phrase.replace(' ', '')

                for i in range(len(all_parameter)):
                    for item in all_parameter[i]:
                        sim = similarity(phrase, item)

                        thresh = makeThreshForParameter(phrase, item)
                        if sim > thresh and sim > max_sim:
                            max_sim, max_item, max_phrase, max_parameter = sim, item, phrase, i
                thresh = makeThreshForParameter(max_phrase, max_item)
                if max_sim > thresh : parameter_result.append(max_parameter)

            if len(parameter_result) > 0:

                with open(resultdir + platform + '/' + filename, 'w') as f:
                    # 支付状态|订单金额|实付金额|签名|支付凭据|收款人
                    if 0 in parameter_result: f.write('支付状态')
                    f.write('|')
                    if 1 in parameter_result: f.write('订单金额')
                    f.write('|')
                    if 2 in parameter_result: f.write('实付金额')
                    f.write('|')
                    if 3 in parameter_result: f.write('签名')
                    f.write('|')
                    if 4 in parameter_result: f.write('支付凭据')
                    f.write('|')
                    if 5 in parameter_result: f.write('收款人')


def readResponse(thirdparty):
    lines = open("../data/configure/standard_edge/edge."+thirdparty+".txt").readlines()
    response = dict()
    en = -1
    for line in lines:
        line = line.strip('\r\n').split(':')
        if line[0] == "edge number":
            en = line[1].strip(' ')
        if line[0] == "response":
            response[en] = line[1].strip(' ')

    return response




def  writeFSMwithParameter(FSMwApis, f):
    for edge_id,fsm in enumerate(FSMwApis):
        f.write('>> edge: ' + str(edge_id) + '\n')
        f.write('edge number in knowledgebase:' + fsm.id_in_kb + '\n')
        f.write('sender:' + fsm.sender + '\n')
        f.write('receiver:' + fsm.receiver + '\n')
        f.write('content:' + fsm.content + '\n')
        f.write('api interface:' + fsm.api_interface + '\n')
        f.write('send parameter:' + fsm.send_parameter + '\n')
        f.write('receive parameter:' + fsm.receive_parameter + '\n')
        f.write('<< end\n\n')


