# coding:utf-8
import os
from pyltp import SentenceSplitter,Segmentor,Postagger,Parser,NamedEntityRecognizer,SementicRoleLabeller
from libsvm.python.svmutil import *
obj_pattern=0
con_pattern=0
sub_pattern=0

LTP_DATA_DIR='../../Documents/ltp_data_v3.4.0'
cws_model_path=os.path.join(LTP_DATA_DIR,'cws.model')
ner_model_path=os.path.join(LTP_DATA_DIR,'ner.model')
parser_model_path=os.path.join(LTP_DATA_DIR,'parser.model')
pos_model_path=os.path.join(LTP_DATA_DIR,'pos.model')
pisrl_model_path=os.path.join(LTP_DATA_DIR,'pisrl.model')


role_model = svm_load_model("../data/models/role.model")
segmentor=Segmentor()
segmentor.load_with_lexicon(cws_model_path,'../data/configure/lexicon.txt')

postagger=Postagger()
postagger.load_with_lexicon(pos_model_path,'../data/configure/pos.txt')

parser=Parser()
parser.load(parser_model_path)

recognizer=NamedEntityRecognizer()
recognizer.load(ner_model_path)

labeller=SementicRoleLabeller()
labeller.load(pisrl_model_path)


class Record():

    def __init__(self):

        self.original_sentence = ''
        self.sentence = ''

        self.sender = ''
        self.sender_name = ''
        self.receiver = ''
        self.receiver_name = ''
        self.content = ''
        self.api_name = ''
        self.verb = ''

        self.verb_id = -1
        self.sender_id = -1
        self.receiver_id = -1
        self.content_id = -1

        self.feature = []
        self.label = -1





def verb_type(verb):
    if verb in send_verbs: return 0
    elif verb in receive_verbs: return 1
    elif verb in call_verbs: return 2
    elif verb in invoke_verbs: return 3
    else: return -1


def verb_order(s,r,c,i):
    result=[]

    ordered_verb=[s,r,c,i]
    ordered_verb.sort()
    verb_list = [s, r, c, i]
    count_negative=len([x for x in verb_list if x <0])
    for x in verb_list:
        if x>0: result.append(ordered_verb.index(x)-count_negative)
        else: result.append(-1)
    return result


def assign_role_id(feature, record, id):
    role,_,_ = svm_predict([],[feature],role_model)
    role = int(role[0])
    if role == 0: record.sender_id = id
    if role == 1: record.receiver_id = id
    if role == 2: record.content_id = id


def svm_dataformat(feature):
    feature = [float(x) for x in feature]
    svm_feature = dict()
    for i in range(6): svm_feature[i + 1] = feature[i]
    return svm_feature




def print_record(r):
    print "sentence:", r.sentence
    print "sender:", r.sender
    print "receiver:", r.receiver
    print "content:", r.content
    print "api:", r.api_name



def filetolist(filename):
    data=[]
    lines=open(filename,'r').readlines()
    for line in lines:
        line=line.strip('\n\r')
        data.append(line)
    return data

def party_id(party):
    if party=='商户客户端':
        return 1
    if party=='商户服务器':
        return 2
    if party=='支付渠道':
        return 3
    if party=='第四方服务器':
        return 4


def word_type(word,type_list):
    type=0
    for i in range(len(type_list)):
        for t in type_list[i]:
            if word.count(t)>0:
                type= i+1
    if word=='Not Found':
        return -1
    return type


def party_type(party,side, att_party,att_side,party_word):

    if party==-1:# not found
        return 'None'
    if  att_side==3 or side==3: # 修饰语/主体为第四方
        if party<4:
            return '第四方服务器'
        elif party==4: # 主体为SDK
            return '商户客户端/商户服务器'
    elif party == 1:  # server
        if att_side == 1or side==1 or party_word=='回调地址':  # user
            return '商户服务器'
        else:
            return '？服务器'
    elif party == 3 or att_party==3 or att_side == 2 or side==2:  # third payment
        return '支付渠道'
    elif party == 2 or party_word=='SDK收银台':  # client
        return '商户客户端'
    elif party==4: # sdk
        if att_party==1: #server
            return '商户服务器'
        elif att_party==2: #client
            return '商户客户端'
        else:
            return '商户客户端/商户服务器'
    else:
        return '其他'


def find_type(sender,receiver,sender_att,receiver_att):
    sender_party = word_type(sender, party_list)
    receiver_party = word_type(receiver, party_list)
    sender_side=word_type(sender,side_list)
    receiver_side=word_type(receiver,side_list)
    sender_att_side = word_type(sender_att,side_list)
    receiver_att_side = word_type(receiver_att,side_list)
    sender_att_party=word_type(sender_att,party_list)
    receiver_att_party = word_type(receiver_att,party_list)
    sender_type = party_type(sender_party, sender_side,sender_att_party,sender_att_side,sender)
    receiver_type = party_type(receiver_party,receiver_side, receiver_att_party,receiver_att_side,receiver)
    return sender_type,receiver_type


def find_attribute(main_id,words,rely_id,relation):
    att=''
    main_type_party=word_type(words[main_id],party_list)
    main_type_side=word_type(words[main_id],side_list)
    #print words[main_id],word_type(words[main_id],[party_server, party_client, party_gateway])
    for x in range(main_id):
        i=main_id-x-1
        if ((relation[i] == 'ATT'or relation[i]=='SBV') and rely_id[i] == main_id )\
                or (relation[i]==relation[main_id]=='SBV'or relation[i]==relation[main_id]=='ATT')and rely_id[i]==rely_id[main_id]:
            att_type_party=word_type(words[i],party_list)
            att_type_side=word_type(words[i],side_list)
            # 主体是服务端/客户端时，需要向前找到side的修饰语
            if 0<main_type_party:
                if att_type_side>0 or att_type_party>0:
                    att=words[i]
                    for j in range(main_id):
                        if rely_id[j]==i and relation[j]=='LAD' :
                            att = words[j]+words[i]
                        elif rely_id[j]==i and relation[j]=='RAD':
                            att = words[i]+words[j]
            # 主体是非party时，只合并一个修饰语即修饰语的定语和左右依存词。
            elif main_type_party<1:
                if words[main_id].count('支付')>0:
                    break
                att = words[i]
                for j in range(main_id ):
                    if (relation[j] == 'ATT' or relation[j]=='SBV' or relation[j]=='LAD')and rely_id[j] ==i :
                        att = words[j]+words[i]
                    if rely_id[j]==i and relation[j]=='RAD' :
                        att=words[i]+words[j]
                break
    return att

def extend_conponent(sender_id,receiver_id,content_id,words, rely_id, relation,api):
    if sender_id >= 0:
        sender_att = find_attribute(sender_id, words, rely_id, relation)
        sender = sender_att + words[sender_id]
    else:
        sender = 'Not Found'
        sender_att = ''
    if receiver_id >= 0:
        receiver_att = find_attribute(receiver_id, words, rely_id, relation)
        receiver = receiver_att + words[receiver_id]
    else:
        receiver = 'Not Found'
        receiver_att = ''
    if content_id > 0:
        content = find_attribute(content_id, words, rely_id, relation) + words[content_id]
    else:
        content = 'Not Found'
    sender_type, receiver_type = find_type(sender, receiver, sender_att, receiver_att)
    if word_type(sender, [content_list]) > 0:
        sender='Not Found'
    if word_type(receiver, [content_list]) > 0:

        receiver='Not Found'
    if api=='':
        return sender, receiver, content, sender_type, receiver_type
    else:
        return sender,receiver,content,sender_type, receiver_type,api

def find_subject(verb_id, words, rely_id, relation):
    sub_id = -1
    sub = ''
    L=len(words)

    for i in range(L):
        if rely_id[i]==verb_id and relation[i]=='SBV':
            if rely_id[i+1]==verb_id and relation[i+1]=='SBV':
                sub_id=i+1
                if sub_pattern == 1: print "sub 1"
            else:
                sub_id = i
                if sub_pattern == 1: print "sub 2"
            sub = words[sub_id]
            if word_type(sub,party_list)>0 or word_type(sub,side_list)>0:break
    if sub_id<0:
        for i in range(L):
            if rely_id[i] == verb_id and (relation[i] == 'CMP' or relation[i] == 'ADV'):
                for j in range(L):
                    if rely_id[j] == i and relation[j] == 'POB' and (prep_from.count(words[i]) > 0 or prep_on.count(words[i])>0):
                        sub_id = j
                        sub = words[sub_id]
                        if sub_pattern == 1: print "sub 3"
    return sub,sub_id

def find_content(verb_id,words,rely_id,relation):
    con_id=-1
    con=''
    L=len(words)
    for i in range(L):
        if rely_id[i]==verb_id and relation[i]=='VOB' and word_type(words[i],party_list)<1:
            con_id=i
            con=words[i]
            for j in range(i+1,L-1):
                if rely_id[j]==i and relation[j]=='RAD' and rely_id[j+1]==verb_id and relation[j+1]=='VOB'and word_type(words[i],party_list)<1:
                    con = words[i]+words[j]+words[j+1]
                    con_id=j+1
            if con_pattern == 1: print "con 1",con
            if word_type(con,[content_list])>0:return con,con_id
    if con_id < 0 or word_type(con,party_list)>0:
        for i in range(L):
            if rely_id[i] == verb_id and relation[i] == 'ADV' and prep_by.count(words[i]) > 0:
                for j in range(L):
                    if rely_id[j] == i and relation[j] == 'POB' :
                        if word_type(con, [party_server, party_client, party_gateway]) <1:
                            con_id = j
                            con = words[j]
                            if con_pattern == 1: print "con 2",con
                            break
                if con_id < 0:
                    for j in range(L):
                        if (rely_id[j] == i or rely_id[i] == verb_id) and relation[j] == 'ADV':
                            if word_type(con, [party_server, party_client, party_gateway]) < 1:
                                con_id = j
                                con = words[j]
                                if con_pattern == 1: print "con 3",con
    if con_id<0:
        for i in range(L):
            if rely_id[i]==verb_id and relation[i]=='COO' or rely_id[verb_id]==i and relation[verb_id]=='COO' :
                for j in range(L):
                    if rely_id[j]==i and relation[j]=='VOB':
                        con_id=j
                        con=words[j]
                        if con_pattern == 1: print "con 4"
                if con_id<0:
                    for j in range(L):
                        if rely_id[j]==i and relation[j]=='POB':
                            con_id=j
                            con=words[j]
                            if con_pattern == 1: print "con 5",con
    #  商户服务器将订单信息参数按照格式应用信息中的privatekey做RSA加密签名后 ， 拼接结果并返回给商户客户端。
    if con_id<0:
        for i in range(verb_id):
            if rely_id[i]==verb_id and relation[i]=='ADV':
                for j in range(i):
                    if rely_id[j]==i:
                        for k in range(j):
                            if rely_id[k]==j and prep_by.count(words[k])>0:
                                for h in range(j):
                                    if rely_id[h]==k and relation[h]=='POB':
                                        con_id = h
                                        con = words[h]
                                        if con_pattern == 1: print "con 6"
    if word_type(con,party_list)>0 or word_type(con.strip('支付'),side_list)>0:
        con=''
        con_id=-1

    if con_id>=0:
        for i in range(con_id,L):
            if rely_id[i]==con_id and relation[i]=='VOB':
                con=con+words[i]
    return con,con_id
def find_api(call_id,next_id,words):
    api=''
    for i in range(call_id+1,next_id):
        api+=words[i]
        if word_type(words[i],[api_list])>0:
            break
    return api

def find_object(verb_id,words,rely_id,relation):
    obj_id=-1
    obj=''
    L=len(words)
    #print "verb id in object:", verb_id
    for i in range(L):
        if rely_id[i]==verb_id and relation[i]=='IOB':
            obj_id=i
            obj=words[obj_id]
            if obj_pattern == 1:print "obj 1"
            break
        elif rely_id[i]==verb_id and (relation[i]=='CMP'or relation[i]=='ADV'):
            if prep_to.count(words[i])>0 and i<verb_id or  i>verb_id:
                for j in range(L):
                    if rely_id[j]==i and relation[j]=='POB':
                            obj_id=j
                            obj=words[obj_id]
                            if obj_pattern==1:print "obj,2"
    if obj_id<0:
        for i in range(L):
            if rely_id[i] == verb_id and relation[i] == 'CMP':
                for j in range(len(words)):
                    if rely_id[j] == i and relation[j] == 'VOB':
                        obj_id = j
                        obj = words[obj_id]
                        if obj_pattern == 1:print "obj 3"
    if obj_id<0:
        for i in range(L-1):
            if rely_id[i]==verb_id and relation[i]=='VOB' :
                if  word_type(words[i], party_list) > 0 or word_type(words[i].strip('支付'),side_list)>0:
                    obj_id = i
                    obj = words[obj_id]
                    if obj_pattern == 1:print "obj 4"
                if obj_id<0:
                    if rely_id[i+1]==i and relation[i+1]=='CMP' :
                        for j in range(L):
                            if rely_id[j]==i+1 and relation[j]=='POB':
                                obj_id = j
                                obj = words[obj_id]
                                if obj_pattern == 1:print "obj 5"
                if obj_id<0:
                    for j in range(verb_id, i):
                        if prep_to.count(words[j]) > 0 and abs(i - j) < 6:
                            obj_id = i
                            obj = words[obj_id]
                            if obj_pattern == 1: print "obj 6"
    if obj_id<0:
        if relation[verb_id]=='ATT' :
            c_id=rely_id[verb_id]
            if word_type(words[c_id],party_list)>0 or word_type(words[c_id],side_list)>0:
                obj_id=c_id
                obj=words[obj_id]
                if obj_pattern == 1: print "obj 7"
    if obj_pattern: print "find_object:",obj
    return obj,obj_id

def add_find_object(sender_id,verb_id,words,rely_id,relation):
    obj=''
    obj_id=-1
    L=len(words)
    for i in range(len(words)):
        if rely_id[i]==verb_id and (relation[i]=='CMP'or relation[i]=='ADV'):

            for j in range(L):
                if rely_id[j]==i and relation[j]=='POB':
                    if (prep_to.count(words[i])>0 or prep_on.count(words[i])>0) :
                        if  i>verb_id or j!=sender_id :
                            obj_id=j
                            obj=words[obj_id]
                            if obj_pattern: print 'obj 8'
    return obj,obj_id
def add_find_subject(receiver_id,verb_id,words,rely_id,relation):
    sub=''
    sub_id=-1
    if relation.count('SBV') > 0:
        for i in range(verb_id):
            if relation[i] == ('SBV') and word_type(words[i], [party_server, party_client, party_gateway]) > 0:
                if receiver_id==i:
                    continue
                sub_id = i
                sub = words[sub_id]
                if sub_pattern == 1: print "sub 4", sub
                break
    return sub,sub_id

def find_verbs(verb,words):
    return [i for i in range(len(words)) if words[i]==verb]

def find_first_verb(verb,words):
    return words.index(verb) if words.count(verb)>0 else -1

send_verbs=filetolist('../data/configure/verb/send')
receive_verbs=filetolist('../data/configure/verb/receive')
call_verbs=filetolist('../data/configure/verb/call')
invoke_verbs=filetolist('../data/configure/verb/invoke')
request_verbs=filetolist('../data/configure/verb/request')
respond_verbs=filetolist('../data/configure/verb/respond')


party_server=filetolist('../data/configure/party/server')
party_client=filetolist('../data/configure/party/client')
party_gateway=filetolist('../data/configure/party/gateway')
party_sdk=filetolist('../data/configure/party/sdk')
party_list=[party_server, party_client, party_gateway,party_sdk]

side_user=filetolist('../data/configure/side/user')
side_third=filetolist('../data/configure/side/third')
side_forth=filetolist('../data/configure/side/forth')
side_list=[side_user,side_third,side_forth]

prep_from=filetolist('../data/configure/prep/from')
prep_to=filetolist('../data/configure/prep/to')
prep_by=filetolist('../data/configure/prep/by')
prep_on=filetolist('../data/configure/prep/on')

content_list=filetolist('../data/configure/content')
api_list=filetolist('../data/configure/api')
