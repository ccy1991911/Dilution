# coding:utf-8
SIZE=100
from gensim.models import word2vec
import os
import numpy as np
from pyltp import Segmentor,Postagger
import sys
reload(sys)
sys.setdefaultencoding("utf-8")


LTP_DATA_DIR='../../Documents/ltp_data_v3.4.0'
cws_model_path=os.path.join(LTP_DATA_DIR,'cws.model')
pos_model_path=os.path.join(LTP_DATA_DIR,'pos.model')


segmentor=Segmentor()
#segmentor.load(cws_model_path)
segmentor.load_with_lexicon(cws_model_path,'../data/configure/match_dict.txt')
postagger=Postagger()
postagger.load_with_lexicon(pos_model_path,'../data/configure/pos.txt')
save_model_name='../data/models/wordEmbedding/model_10_30.txt'

model = word2vec.Word2Vec.load(save_model_name)

def filetolist(filename):
    data=[]
    lines=open(filename,'r').readlines()
    for line in lines:
        line=line.strip('\n\r')
        if line!='':
            data.append(line)
    return data
def file_to_matrix(filename,mark):
    data = []
    lines = open(filename, 'r').readlines()
    for line in lines:
        line = line.strip('\n\r').split(mark)
        if line != '':
            data.append(line)
    return data
def makedir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def cosine_distance(v1,v2):
    #sqrt(sum_i{(a_i-b_i)^2})
    dist=np.linalg.norm(v1-v2)
    return 1/(1+dist)
def cosine_similarity(v1,v2):
    # \sum_i{a_i*b_i}
    num=np.sum(v1*v2)
    #|a||b|
    denom=np.linalg.norm(v1)*np.linalg.norm(v2)
    #print "denom",denom
    cos=0
    if denom!=0:
        cos=num/denom
    return 0.5+0.5*cos

def phrase_vec(wordseq):
    #print "word sequence:",wordseq
    phrasevec=np.zeros(SIZE)
    for i in range(len(wordseq)):
        word =wordseq[i]
        if word not in model:
            #print word, "not in model"
            continue
        phrasevec+=model[word]
    phrasevec/=float(len(wordseq))
    return phrasevec
def phrase_similarity(seq1,seq2):

    return cosine_similarity(phrase_vec(seq1),phrase_vec(seq2))

def phrase_to_sequence(phrase):
    phrase=phrase.replace('\n','').replace('0xe6','').replace('第四方','')
    result=[]
    words = segmentor.segment(phrase)
    #postags=postagger.postag(words)
    for word in words:
        #print word,' ',
        word=unicode(word,'utf8')
        result.append(word)
    return result

def similarity(c1,c2):

    s1 = phrase_to_sequence(c1)

    s2 = phrase_to_sequence(c2)

    if len(s1)>0 and len(s2)>0:

        return phrase_similarity(s1, s2)
    else: return 0

def print_phrase_similarity(seq1,seq2):
    v1=phrase_vec(seq1)
    v2=phrase_vec(seq2)
    p1=""
    p2=""
    for word in seq1:
        p1+=word
    for word in seq2:
        p2+=word
    print "【",p1,"】和【",p2,"】的相似度："
    #print "cosine distance similarity", cosine_distance(v1,v2)
    print "cosine similarity", cosine_similarity(v1, v2)
    return cosine_similarity(v1, v2)

def pop(array):
    for i in range(len(array)-1):
        array[i]=array[i+1]
    return array
def push(array,item,n):
    if len(array)<n:
        array.append(item)
    else:
        array=pop(array)
        array[-1]=item
    return array

def find_most_similar(seq1,seq2,num):

    max=0
    candidates=[]
    sims=[]

    thresh=0.95
    vocab = model.wv.vocab
    for v in vocab:
        v=str(v)
        sim=similarity(seq1,seq2+v)
        if sim>thresh:

            candidates=push(candidates,[v,sim],num)


    return candidates

