# -*-coding:utf-8 -*-
import csv

from pattern import *
import os
import sys

reload(sys)
sys.setdefaultencoding('utf8')



modifier=filetolist('../data/configure/modifier.txt')


def role_predict(verb_id):

    if not verb_id < 0:
        record = Record()
        record.original_sentence = o_sentence
        record.sentence = sentence
        record.verb_id = verb_id
        record.verb = words[verb_id]

        subject, subject_id = find_subject(verb_id, words, rely_id, relation)
        indirect_object, indirect_object_id = find_object(verb_id, words, rely_id, relation)
        object, object_id = find_content(verb_id, words, rely_id, relation)

        if not subject_id < 0:
            feature = order_feature+[verb_type(words[verb_id])]+[0]
            feature = svm_dataformat(feature)
            assign_role_id(feature, record, subject_id)
            #write_file(sentence, order_feature, verb_type(words[s_i]), '0', subject)

        if not indirect_object_id < 0:
            feature = order_feature + [verb_type(words[verb_id])] + [1]
            feature = svm_dataformat(feature)
            assign_role_id(feature, record, indirect_object_id)
            #write_file(sentence, order_feature, verb_type(words[s_i]), '1', indirect_object)

        if not object_id < 0:
            feature = order_feature + [verb_type(words[verb_id])] + [2]
            feature = svm_dataformat(feature)
            assign_role_id(feature, record, object_id)
            #write_file(sentence, order_feature, verb_type(words[s_i]), '2', object)

        assign_api_name(record)
        records.append(record)
def preprocess(filename,content):
    r = ''
    contents = []
    lines = open(filename, 'r').readlines()
    for line in lines:
        line = line.replace('\n\r', '')
        if line.startswith('content:'): contents = line.strip('content:').split(',')
        if line.startswith('replace'): r = line.strip('replace:').strip('\n\r')
        if line.startswith('-'):
            for c in contents:
                c = c.strip('\n\r')
                if content.count(c) > 0: content = content.replace(c, r)
    for word in modifier: content = content.replace(word, '')

    return content


# process senteces of payment process and security requirement
def parse_sentence(require):

    sentence = preprocess('../data/configure/content_replace', o_sentence)
    sentence = sentence.replace(platform, "第四方")

    words = list(segmentor.segment(sentence))
    postags = postagger.postag(words)
    arcs = parser.parse(words, postags)
    rely_id = [arc.head - 1 for arc in arcs]  # extract head id
    relation = [arc.relation for arc in arcs]  # extract relation
    #heads = ['Root' if id == -1 else words[id] for id in rely_id]  # head word

    # extract sender, receiver, content in a payment process sentence
    send_ids,receive_ids, call_id, invoke_id = [], [], -1 , -1
    for i in range(len(words)):
        if postags[i] == 'v':
            if verb_type(words[i]) == 0: send_ids.append(i)
            elif verb_type(words[i]) == 1: receive_ids.append(i)
            elif verb_type(words[i]) == 2:  call_id = i
            elif verb_type(words[i]) == 3:   invoke_id = i
    if len(send_ids) == 0: send_ids.append(-1)
    if len(receive_ids) == 0: receive_ids.append(-1)

    #extract security requirement


    verbs = [words[i] for i in range(len(words)) if postags[i] == 'v']

    types=['金额','签名']
    if o_sentence.count('验签')>0: require[o_sentence] = '签名'
    verify_p = list(set([x for x in verify_verbs if x in verbs]))
    if_match = [x for x in consistent if x in words]
    if len(verify_p) > 0:
        end = 0
        for m in if_match:
            if words.index(m) > end:
                end = words.index(m)
        for p in verify_p:
            begin = words.index(p)
            for i in range(begin, end):
                for j in range(len(check_contents)):
                    if words[i] in check_contents[j] :
                        if sentence not in require.keys():

                            require[o_sentence] = types[j]
                        elif types[j] != require[o_sentence]:
                            require[o_sentence] += ('|'+types[j])

    return sentence, words, rely_id, relation, send_ids, receive_ids, call_id, invoke_id


def assign_api_name(record):
    if call_id > 0 and invoke_id > 0: record.api_name = find_api(call_id, invoke_id, words)
    elif call_id > 0 and s_id > call_id: record.api_name = find_api(call_id, s_id, words)
    elif r_id > 0 and call_id > r_id: record.api_name = find_api(call_id, len(words), words)

def assign_role(record):
    result = extend_conponent(record.sender_id, record.receiver_id, record.content_id, words, rely_id, relation,
                              record.api_name)
    record.sender_name = result[0]
    record.receiver_name = result[1]
    record.content = result[2]
    record.sender = result[3]
    record.receiver = result[4]


def matchStandardEdge(r,f):
    global edge_id
    # global Edges
    o_sentence = r.original_sentence
    sentence = r.sentence
    sender = r.sender_name
    sender_type = r.sender
    receiver = r.receiver_name
    receiver_type = r.receiver
    content = preprocess('../data/configure/content_replace', r.content)
    api_name = r.api_name

    if len(content) > 0:

        sender_type_id = party_id(sender_type)
        receiver_type_id = party_id(receiver_type)

        if 0 <= sender_type_id < 4 and (receiver_type_id < 0 or receiver_type_id == 4):
            g_receiver_ids = find_party(receiver_type, 'sender', sender_type_id, content, alipay_edges)
            for g_receiver_id in g_receiver_ids:
                if 4 > g_receiver_id > 0 or g_receiver_id == 0 and sender_type_id != 2:
                    alipay_en = edge_matching(alipay_edges, sender_type_id, g_receiver_id, content)
                    wechat_en = edge_matching(wechat_edges, sender_type_id, g_receiver_id, content)
                    if alipay_en and wechat_en:

                        edge = State()
                        edge_assign(edge,edge_id, o_sentence, sentence,content,
                                     id_party(sender_type_id),
                                     id_party(g_receiver_id), alipay_en, wechat_en, api_name)

                        Edges.append(edge)

                        writeFileMatchStandardEdge(f,edge_id, sentence, o_sentence, sender, receiver, content, id_party(sender_type_id),
                         id_party(g_receiver_id), alipay_en, wechat_en, platform, api_name)

                        edge_id += 1
        elif sender_type_id < 0 and receiver_type_id > 0 or sender_type_id == 4 and 0 <= receiver_type_id < 4:
            g_sender_ids = find_party(sender_type, 'receiver', receiver_type_id, content, alipay_edges)
            for g_sender_id in g_sender_ids:
                if 4 > g_sender_id > 0 or g_sender_id == 0 and receiver_type_id != 2:
                    alipay_en = edge_matching(alipay_edges, g_sender_id, receiver_type_id, content)
                    wechat_en = edge_matching(wechat_edges, g_sender_id, receiver_type_id, content)
                    if alipay_en and wechat_en:

                        edge = State()
                        edge_assign(edge, edge_id, o_sentence, sentence, content,
                                    id_party(g_sender_id), id_party(receiver_type_id), alipay_en, wechat_en, api_name)
                        Edges.append(edge)

                        writeFileMatchStandardEdge(f,edge_id, sentence, o_sentence,sender, receiver, content, id_party(g_sender_id),
                         id_party(receiver_type_id), alipay_en, wechat_en, platform, api_name)
                        edge_id += 1

        if 4 > sender_type_id >= 0 and 4 > receiver_type_id >= 0:
            alipay_en = edge_matching(alipay_edges, sender_type_id, receiver_type_id, content)
            wechat_en = edge_matching(wechat_edges, sender_type_id, receiver_type_id, content)

            if alipay_en and wechat_en:

                edge = State()
                edge_assign(edge, edge_id, o_sentence, sentence, content,
                            id_party(sender_type_id),id_party(receiver_type_id), alipay_en, wechat_en, api_name)
                Edges.append(edge)

                writeFileMatchStandardEdge(f,edge_id, sentence, o_sentence,sender, receiver, content, id_party(sender_type_id),
                                         id_party(receiver_type_id), alipay_en, wechat_en,platform,api_name)
                edge_id += 1


def findParameter(api):
    global platform
    global thirdPaymentName
    send_parameter, receive_parameter = '', ''
    postFileDir = "../data/tmp/parameter/"+platform+"/"+api+"-"+thirdPaymentName+'-'+'post.txt'
    if os.path.exists(postFileDir):
        postFile = open ("../data/tmp/parameter/"+platform+"/"+api+"-"+thirdPaymentName+'-'+'post.txt').readlines()
        send_parameter = postFile[0].strip('\r\n')
    receiveFileDir =  "../data/tmp/parameter/" + platform + "/" + api + "-" + thirdPaymentName + '-' + 'receive.txt'
    if os.path.exists(receiveFileDir):
        receiveFile = open(receiveFileDir).readlines()
        receive_parameter = receiveFile[0].strip('\r\n')
    return send_parameter, receive_parameter

def createFSMwApi(edge_id,result,api):
    FSM = State()
    FSM.edge_id = edge_id
    FSM.id_in_kb = result[0]
    FSM.sender = result[2]
    FSM.receiver = result[3]
    FSM.content = result[5]
    FSM.api_interface = api
    FSM.send_parameter, FSM.receive_parameter = findParameter(api)
    return FSM


def checkSRinApi(platform,third):
    require = dict()
    require_sentence = []
    for parent, dirs, filenames in os.walk("../data/input/apiDescription/" + platform):
        for filename in filenames:
            if filename.startswith('.'): continue
            parameter_result = []
            p_list = filetolist("../data/input/apiDescription/" + platform + "/" + filename)
            api = filename.split('-')[0]
            thirdpayment = filename.split('-')[1]
            if thirdpayment != third:
                continue
            for p in p_list:
                description = p.split('***')[-1]
                words = list(segmentor.segment(description))
                postags = postagger.postag(words)
                arcs = parser.parse(words, postags)
                rely_id = [arc.head - 1 for arc in arcs]  # extract head id
                relation = [arc.relation for arc in arcs]
                verbs = [words[i] for i in range(len(words)) if postags[i] == 'v']

                types = ['金额', '签名', '收款人','notify_id']
                if description.count('验签') > 0: require[api] = '签名'
                verify_p = list(set([x for x in verify_verbs if x in verbs]))
                if_match = [x for x in consistent if x in words]

                if len(verify_p) > 0:
                    end = 0
                    for m in if_match:
                        if words.index(m) > end:
                            end = words.index(m)
                    for p in verify_p:
                        begin = words.index(p)
                        for i in range(begin, end):
                            for j in range(len(check_contents)):
                                if words[i] in check_contents[j] and description not in require_sentence:

                                    require_sentence.append(description)
                                    require[api] += types[j]
                                    require[api] += '|'
    return require


def match_api_interface(result,f):
    global edge_id
    global FSMwApis
    ask_for_api = result[7]
    # print ask_for_api
    if ask_for_api == 'False':
        FSM  = createFSMwApi(edge_id, result, '')
        FSMwApis.append(FSM)
        writeFileAPI(edge_id, f, result, '')
        edge_id += 1
    else:
        e_contents = result[4].split('|')
        content,api = result[5],extract_api(result[6])
        content_r = preprocess('../data/configure/content_replace', content)
        api_r = preprocess('../data/configure/content_replace', api)
        max_sim,thresh  = 0, 0
        api_name = ''

        # print ek,em,result[4],content,api
        for can_api in api_list:
            can_api_r = preprocess('../data/configure/content_replace', can_api)
            sim1, sim2 = 0, 0
            if len(content) > 0: sim1 = similarity(content_r, can_api_r)
            if len(api) > 0: sim2 = similarity(api_r, can_api_r)
            sim = max(sim1, sim2)
            thresh = makeThreshAPI(api_r, can_api_r)

            if sim > max_sim and sim > thresh:
                api_name, max_sim = can_api, sim
                #print  '    candidate api:', can_api_r, 'content:', content_r, "api:", api, '|similarity:', sim

            for e_content in e_contents:
                sim = 0

                if len(e_content) > 0:
                    sim = similarity(e_content, can_api_r)
                    thresh = makeThreshAPI(e_content, can_api_r)
                if sim > max_sim and sim > thresh:
                    api_name, max_sim = can_api, sim
                    #print  '    candidate api:', can_api_r, 'e_content:', e_content, ' ', '|similarity:', sim, 'thresh:', thresh

        if max_sim > thresh:
            FSM = createFSMwApi(edge_id, result, api_name)
            FSMwApis.append(FSM)
            #print api_name
            writeFileAPI(edge_id, f, result, api_name)
            edge_id += 1
        else:
            FSM = createFSMwApi(edge_id, result, '')
            FSMwApis.append(FSM)
            writeFileAPI(edge_id, f, result, '')

def addResponseParameter(FSMwApis,response_id,response_api):
    global platform, thirdPaymentName
    for f in FSMwApis:
        if f.id_in_kb == response_id:
            if f.api_interface == '':
                f.api_interface = response_api
                receive_parameter = ''
                receiveFileDir = "../data/tmp/parameter/" + platform + "/" + response_api + "-" + thirdPaymentName + '-' + 'receive.txt'
                if os.path.exists(receiveFileDir):
                    receiveFile = open(receiveFileDir).readlines()
                    receive_parameter = receiveFile[0].strip('\r\n')
                if f.receive_parameter == '':
                    f.receive_parameter = receive_parameter
                else:
                    p1 = f.receive_parameter.split('|')
                    p2 = receive_parameter.split('|')
                    parameter = set(p1 + p2)
                    pstr = ''
                    for i,p in enumerate(parameter):
                        if i < len(parameter)-1:
                            pstr = pstr + p +'|'
                        else:
                            pstr = pstr + p
                    f.receive_parameter = pstr
    return FSMwApis

# default settings
LTP_DATA_DIR='../../Documents/ltp_data_v3.4.0'
platform = 'BeeCloud'

if __name__ == '__main__':

    if len(sys.argv)>1:
        platform = sys.argv[1]
        LTP_DATA_DIR = sys.argv[2]

    '''extract conponents<sender, receiver, content> from sentence'''
    Records = []
    filename = os.path.join('../data/input/payDocument/', platform + '.txt')
    document = filetolist(filename)
    sr_in_doc = dict()
    for paragraph in document:
        sentences=SentenceSplitter.split(paragraph)

        for o_sentence in sentences:
            records = []
            sentence, words, rely_id, relation, send_ids, receive_ids, call_id, invoke_id = parse_sentence(sr_in_doc)

            for s_id in send_ids:
                for r_id in receive_ids:

                    order_feature=verb_order(s_id,r_id,call_id,invoke_id)
                    role_predict(s_id)
                    role_predict(r_id)
                    role_predict(call_id)
                    role_predict(invoke_id)

            for record in records:
                assign_role(record)
                Records.append(record)

    validRecords = []

    # delete invalid records
    for i,r in enumerate(Records):
        if 'Not Found' not in r.content :
            if not ((r.sender == 'None' or r.sender == '其他') and  (r.receiver == 'None' or r.receiver == '其他')):
                validRecords.append(r)
        elif  r.api_name != '':
            content = r.api_name.split('的')
            r.content = content[1] if len(content) > 1 else content
            if not ((r.sender == 'None' or r.sender == '其他') and (r.receiver == 'None' or r.receiver == '其他')):
                validRecords.append(r)

    PRINT_RECORD = 0
    if PRINT_RECORD:
        for r in validRecords:
            print_record(r)

    ''' match with the standard edge summarized from third payment'''
    from match import *
    Edges = []
    edge_id = 0
    alipay_edges = read_edges('../data/configure/standard_edge/edge.alipay.txt')
    wechat_edges = read_edges('../data/configure/standard_edge/edge.wechat.txt')
    makedir('../data/tmp/matchStandardEdge/')
    with open('../data/tmp/matchStandardEdge/' + platform + '.edge.txt', 'w') as f:
        for r in validRecords:
            matchStandardEdge(r,f)
            #platform = result[0]

    ''' check the parameters related with security requirement in each API'''
    checkParameterInAllApis(platform)

    '''get FSM extension'''
    from findExtensionFSMs import *
    makedir('../data/tmp/extensionFSM')
    thirdPaymentNames = ['alipay', 'wechat']
    syndicationName = platform
    for thirdPaymentName in thirdPaymentNames:
        readThirdPaymentBasicEdge(thirdPaymentName)
        # readAllPossibleFSM(thirdPaymentName)
        readSyndicationDocumentationEdge(thirdPaymentName, syndicationName)
        matchFSM(thirdPaymentName, syndicationName)

        '''match API for each FSM'''
        filename = "%s.%s.txt"%(syndicationName , thirdPaymentName)
        FSMs = readFromFSM("../data/tmp/extensionFSM/"+filename)
        api_list = readApiList(platform)
        sen_api = []
        # [ek,em,sender,receiver,contents_k,content,api,ask]
        edge_id = 0
        makedir("../data/tmp/FSMwithAPI/")
        FSMwApis=[]
        with open("../data/tmp/FSMwithAPI/"+filename,'w') as f:
            for FSM in FSMs:
                match_api_interface(FSM,f)

        '''check security requirement in api'''
        sr_in_api = checkSRinApi(platform, thirdPaymentNames)

        '''add parameter for the response edge'''
        responses = readResponse(thirdPaymentName)


        for f in FSMwApis:

            if responses[str(f.id_in_kb)]!='':
                response_id = responses[str(f.id_in_kb)]
                response_api = f.api_interface
                FSMwApis = addResponseParameter(FSMwApis,response_id,response_api)


        makedir("../data/tmp/FSMwithParameterandSR/")
        with open("../data/tmp/FSMwithParameterandSR/" + filename, 'w') as f:
            writeFSMwithParameterAndCheck(FSMwApis,f,sr_in_doc,sr_in_api,thirdPaymentName,syndicationName,Edges)
            
        """
        '''predict logic vulnerability '''
        from predictLogicVulnerability import *
        readThirdPaymentBasicEdge(thirdPaymentName)

        readPreconfigInformation(thirdPaymentName, syndicationName)
        print('Possesion:', Possesion, '\n')

        readSyndicationDocumentationEdge(thirdPaymentName, syndicationName)
        print(SyndicationDocumentationEdge)

        identifyLogicVunlerability(thirdPaymentName)
        """


segmentor.release()
postagger.release()
recognizer.release()
labeller.release()
