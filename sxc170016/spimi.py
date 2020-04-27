import sys
import ast
import re
import nltk
import collections
from collections import OrderedDict
stopwords = []
from nltk.stem import PorterStemmer
lemmatizer = nltk.WordNetLemmatizer()
porter_stemmer = PorterStemmer()

## StopWords
# reades stopword file from resource and adds them to list
# @return {stopwords} - list of stopwords
def StopWords():
    filePath = 'IR/stopwords'
    file = open(filePath, 'r')
    lines = file.readlines()
    for words in lines:
        stopwords.append(words.rstrip('\n'))

## StopWords
# reades stopword file from resource and adds them to list
# @return {stopwords} - list of stopwords
def PoterStem():
    filePath = 'IR/stopwords'
    file = open(filePath, 'r')
    lines = file.readlines()
    for words in lines:
        stopwords.append(words.rstrip('\n'))

## MaxTerm
# takes dcoument and returns maximum frequent term in the document and its count
# @params {document} - takes document of words
# @return {object} - maximum frequent term and its count in the document
def MaxTerm(document):
    term = max(set(document), key=document.count)
    return term, document.count(term)

## SPIMI
# takes documents and generates dictionary with term and postings list
# @params {documents} - list of documents with each document having corresponding text
# @params {text} - lines of data from cranfield files
# writes sorted block of size 750000bytes
# @return {doc_len} - dict of document details with max term, max term freq, docid, and len of doc
def SPIMI(documents, block_size, block_path='index_blocks/',  lematize=False, stemm=False):
    block_number = 0
    documents_count = len(documents)
    dictionary = {}  # (term - postings list)
    doc_details = {}
    StopWords()
    for index, docID in enumerate(documents):
        if lematize:
            max_term, max_freq = MaxTerm(documents[docID])
            doc_len = len(documents[docID])
            doc_details[docID.lstrip('0')] = {
                'max_term': max_term,
                'max_freq': max_freq,
                'docid': docID,
                'doc_len': doc_len
            }
        for word in documents[docID]:
            if word not in stopwords:
                if lematize:
                    term = lemmatizer.lemmatize(word)
                if stemm:
                    term = porter_stemmer.stem(word)
                # If term occurs for the first time
                if term not in dictionary:
                    # Add term to dictionary, create new postings list, and add docID
                    dictionary[term] = [docID]
                else:
                    # Add a posting (docID) to the existing posting list of the term
                    dictionary[term].append(docID)

        if sys.getsizeof(dictionary) > block_size or (index == documents_count - 1):
            temp_dict = SortBlock(dictionary)  # sorting the block level dictionary
            WriteBlockToDisk(temp_dict, block_number, block_path)
            temp_dict = {}
            block_number += 1
            dictionary = {}

    if lematize:
        return doc_details

## SortBlock
# Sorts dictionary terms in lexographical order
# @params {term_postings_list} - takes term ans there corresponding postings list
# @return {sorted_dictionary} - sorted block level terms with term frequency w.r.t document
def SortBlock(term_postings_list):
    sorted_dictionary = OrderedDict() # keep track of insertion order
    sorted_terms = sorted(term_postings_list)
    for term in sorted_terms:
        result = [int(docIds) for docIds in term_postings_list[term]]
        result_tftd = CalculatetTfTd(result)
        sorted_dictionary[term] = result_tftd
    return sorted_dictionary


## CalculatetTfTd
# Add term frequency of term in each document
# @params {postinglist_with_duplicates} - takes postings list
# @return {pl_tftd} - returns  term frequency in each document
def CalculatetTfTd(postinglist_with_duplicates):
    counter = collections.Counter(postinglist_with_duplicates)
    pl_tftd = [[int(docId), counter[docId]] for docId in counter.keys()]
    return pl_tftd

## WriteBlockToDisk
# Writes index of the block (dictionary + postings list) to disk
# @params {term_postings_list} - term with posting list and frequency
# @params {block_number} - block number
# @params {block_path} - block_path
def WriteBlockToDisk(term_postings_list, block_number, block_path):
    # Define block

    base_path = block_path
    block_name = 'block-' + str(block_number) + '.txt'
    block = open(base_path + block_name, 'a+')
    # Write term : posting lists to block
    for index, term in enumerate(term_postings_list):
        # Term - Posting List Format
        # term:[docID1, docID2, docID3]
        # e.g. cat:[4,9,21,42]
        block.write(str(term) + ":" + str((term_postings_list[term])) + "\n")
    block.close()


def MergeBlocks(blocks, fileName):
    """ Merges SPIMI blocks into final inverted index """
    merge_completed = False
    spimi_index = open(fileName+'.txt', 'a+')
    # Collect initial pointers to (term : postings list) entries of each SPIMI blocks
    temp_index = OrderedDict()
    dictionary = OrderedDict()
    for num, block in enumerate(blocks):
        line = blocks[num].readline() # term:[docID1, docID2, docID3]
        line_tpl = line.rsplit(':', 1)
        term = line_tpl[0]
        postings_list = ast.literal_eval(line_tpl[1])
        temp_index[num] = {term:postings_list}
    while not merge_completed:
        # Convert into an array of [{term: [postings list]}, blockID]
        tpl_block = ([[temp_index[i], i] for i in temp_index])
        # Fetch the current term postings list with the smallest alphabetical term
        smallest_tpl = min(tpl_block, key=lambda t: list(t[0].keys()))
        # Extract term
        smallest_tpl_term = (list(smallest_tpl[0].keys())[0])
        # Fetch all IDs of blocks that contain the same term in their currently pointed (term: postings list) :
        # For each block, check if the smallest term is in the array of terms from all blocks then extract the block id
        smallest_tpl_block_ids = [block_id for block_id in temp_index if smallest_tpl_term in [term for term in temp_index[block_id]]]
        # Build a new postings list which contains all postings related to the current smallest term
        # Flatten the array of postings and sort
        smallest_tpl_pl = sorted(sum([pl[smallest_tpl_term] for pl in (temp_index[block_id] for block_id in smallest_tpl_block_ids)], []))
        dictionary[smallest_tpl_term] = smallest_tpl_pl
        spimi_index.write(str(smallest_tpl_term) + ":" + str(smallest_tpl_pl) + "\n")

        # Collect the next sectioned (term : postings list) entries from blocks that contained the previous smallest tpl term
        for block_id in smallest_tpl_block_ids:
            # Read the blocks and read tpl in a temporary index
            block = [file for file in blocks if re.search('block-'+str(block_id), file.name)]
            if block[0]:
                line = block[0].readline()
                if not line == '':
                    line_tpl = line.rsplit(':', 1)
                    term = line_tpl[0]
                    postings_list = ast.literal_eval(line_tpl[1])
                    temp_index[block_id] = {term:postings_list}
                else:
                    # Delete block entry from the temporary sectioned index holder if no line found
                    del temp_index[block_id]
                    blocks.remove(block[0])
            else:
                blocks.remove(block[0])
        # If all block IO streams have been merged
        if not blocks:
            merge_completed = True
            print("SPIMI completed! All blocks merged into final index: "+fileName)
    return dictionary