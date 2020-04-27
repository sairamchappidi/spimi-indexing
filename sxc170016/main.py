import os
import sys
import time
import timeit
import glob
import re
from os import listdir
from collections import OrderedDict

from sxc170016.spimi import SPIMI, MergeBlocks
from sxc170016.compression import BlockCompression, FrontCoding

LemaDict = OrderedDict()
StemDict = OrderedDict()
files_length = 0


## Tokenizer
# cleans the text from cranfield data
# @params {text} - lines of data from cranfield files
# @return {list} - cleaned word list
def Tokenize(text):
    text = re.sub("\\<.*?>", " ", text)
    text = re.sub("[\\d+]", " ", text)
    text = re.sub("[+^:,?;=%#&~$!@*_)/(}{\\.]", "", text)
    text = re.sub("[-]", " ", text)
    text = re.sub("\\'[a-z]*[A-Z]*", "", text)
    text = re.sub("\\s+", " ", text)
    return text.split()


def PrintDocDetails(doc_details):
    max_tf = 0
    max_tf_doc_id = 0
    max_doc_len_id = 0
    max_doc_len = 0
    for doc_id in doc_details:
        if doc_details[doc_id]['max_freq'] > max_tf:
            max_tf = doc_details[doc_id]['max_freq']
            max_tf_doc_id = doc_id
        if doc_details[doc_id]['doc_len'] > max_doc_len:
            max_doc_len = doc_details[doc_id]['doc_len']
            max_doc_len_id = doc_id
    print("doc with largest max_tf " + str(max_tf_doc_id) + " with a max term freq of " + str(max_tf))
    print("doc with largest doclen " + str(max_doc_len_id) + " with a max doc length of " + str(max_doc_len))


def TotalTermFrequency(posting):
    total_tf = 0
    for doc_id, tf in posting:
        total_tf += tf
    return total_tf


def PrintSearchResults(dictionary, search_words, index_type):
    print('Search Term details with respect to ' + index_type)
    for term in search_words:
        postinglist = dictionary[term]
        total_tf = TotalTermFrequency(postinglist)
        print('Details of ' + term)
        print('Term Frequqency: ' + str(total_tf))
        print('Document Frequency: ' + str(len(postinglist)))
        print('Size of inverted posting list in bytes: ' + str(sys.getsizeof(postinglist)))


def PrintNasaDetails(dictionary, index_type):
    print('NASA Stats from ' + index_type)
    nasaPostList = dictionary['nasa']
    count = 1
    for doc_id, tf in nasaPostList:
        if (count > 3):
            break
        docId = str(doc_id)
        max_freq = doc_details[docId]['max_freq']
        doc_len = doc_details[docId]['doc_len']
        count += 1
        print('Term frequency of NASA in ' + docId + ' is : ' + str(tf))
        print('DocumentLen of the posting  of NASA in ' + docId + ' is : ' + str(doc_len))
        print('Maximum term frequency of the posting  NASA in ' + docId + ' is : ' + str(max_freq))
        print('document frequency of NASA in ' + docId + ' is : ' + str(len(nasaPostList)))


def PrintMaxMinDF(dictionary, index_type):
    max_df = 0
    min_df = files_length

    for term, posting_list in dictionary.items():
        df = len(posting_list)
        if df > max_df:
            max_df = df
        if df < min_df:
            min_df = df

    max_df_terms = []
    min_df_terms = []
    for term, posting_list in dictionary.items():
        df = len(posting_list)
        if df == max_df:
            max_df_terms.append(term)
        elif df == min_df:
            min_df_terms.append(term)

    print("The terms from " + index_type + " with the largest df:", max_df_terms)
    print("The terms from " + index_type + " with the lowest df:", min_df_terms)


if __name__ == '__main__':
    start = timeit.default_timer()
    cwd = os.getcwd()
    filesPath = []
    words = {}
    block_size = 75000
    if len(sys.argv) > 1:
        filesPath = glob.glob(sys.argv[1] + '/*')
    else:
        filesPath = glob.glob(cwd + "/Cranfield/*")
    num = 0
    files = []
    for fileName in filesPath:
        files.append(fileName)
    files.sort()
    files_length = len(files)
    for fileName in files:
        cranfield, doc_id = fileName.split('cranfield')
        words[doc_id] = []
        file = open(fileName, 'r')
        lines = file.readlines()
        for line in lines:
            words[doc_id] += Tokenize(line)

    startTime = int(round(time.time() * 1000))
    doc_details = SPIMI(words, block_size, 'index_blocks/', True)
    spimiBlocks = [open('index_blocks/' + block) for block in listdir('index_blocks/')]
    LemaDict = MergeBlocks(spimiBlocks, 'Index_Version1.uncompress')
    endTime = int(round(time.time() * 1000))
    runtime = (endTime - startTime)
    print("Time taken to Create Index_Version1.uncompress: " + str(runtime) + " milliseconds")

    f = open("doc_details.txt", "a")
    f.write(str(doc_details))
    f.close()

    startTime = int(round(time.time() * 1000))
    SPIMI(words, block_size, 'index_blocks2/', False, True)
    spimiBlocks2 = [open('index_blocks2/' + block) for block in listdir('index_blocks2/')]
    StemDict = MergeBlocks(spimiBlocks2, 'Index_Version2.uncompress')
    endTime = int(round(time.time() * 1000))
    runtime = (endTime - startTime)
    print("Time taken to Create Index_Version2.uncompress: " + str(runtime) + " milliseconds")
    
    startTime = int(round(time.time() * 1000))
    BlockCompression(LemaDict.items())
    endTime = int(round(time.time() * 1000))
    runtime = (endTime - startTime)
    print("Time taken to Create Index_Version1.compress: " + str(runtime) + " milliseconds")
    
    startTime = int(round(time.time() * 1000))
    FrontCoding(StemDict.items())
    endTime = int(round(time.time() * 1000))
    runtime = (endTime - startTime)
    print("Time taken to Create Index_Version2.compress: " + str(runtime) + " milliseconds")
    
    size = os.path.getsize("Index_Version1.uncompress.txt")
    print("Size of Index_Version1.uncompress: " + str(size) + " bytes")
    
    size = os.path.getsize("Index_Version2.uncompress.txt")
    print("Size of Index_Version2.uncompress: " + str(size) + " bytes")
    
    size = os.path.getsize("Index_Version1.compressed.txt")
    print("Size of Index_Version1.compressed: " + str(size) + " bytes")
    
    size = os.path.getsize("Index_Version2.compressed.txt")
    print("Size of Index_Version2.compressed: " + str(size) + " bytes")
    
    search_words_lema = ["reynolds", "nasa", "prandtl", "flow", "pressure", "boundary", "shock"]
    PrintSearchResults(LemaDict, search_words_lema, 'index-1')
    search_words_stem = ["reynold", "nasa", "prandtl", "flow", "pressur", "boundari", "shock"]
    PrintSearchResults(StemDict, search_words_stem, 'index-2')
    
    PrintNasaDetails(LemaDict, 'index-1')
    PrintNasaDetails(StemDict, 'index-2')
    
    PrintMaxMinDF(LemaDict, 'index-1')
    PrintMaxMinDF(StemDict, 'index-2')
    
    PrintDocDetails(doc_details)
