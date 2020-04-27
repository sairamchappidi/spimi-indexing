## UnaryValueGenerator
# @params {offset_len} - offset length  of the gap
# @return {unary_value} - unary_value of the gap in string
def UnaryValueGenerator(offset_len):
    unary_value = ""
    for i in range(0,offset_len):
        unary_value += str(1)
    return unary_value + str(0)


## GammaEncoding
# @params {gap} - gap between the posting lists
# @return {gamma_code} - gamma code of the gap
def GammaEncoding(gap):
    binary_rep = str(bin(gap))[2:]
    offset = binary_rep[1:]
    unary_value = UnaryValueGenerator(len(offset))
    gamma_code = unary_value + offset
    return gamma_code


def BlockCompression(dictionary):
    block_size = 4
    temp_block_size = 0
    string_dict = ""
    gamma_encoding_list = []
    length = 0
    compressed_dict = {}
    for term, posting_list in dictionary:
        length += 1
        if(temp_block_size < block_size):
            string_dict += str(len(term)) + term
            prev_doc_id = 0
            for doc_id, term_freq in posting_list:
                doc_gamma_code = GammaEncoding(doc_id - prev_doc_id)
                prev_doc_id = doc_id
                gamma_encoding_list.append(doc_gamma_code)
            temp_block_size += 1

        if temp_block_size == block_size or length == len(dictionary) - 1:
            compressed_dict[string_dict] = gamma_encoding_list
            temp_block_size = 0
            string_dict = ""
            gamma_encoding_list = []

    fw = open("Index_Version1.compressed.txt", "wb")
    fw.write(str(compressed_dict).encode())
    fw.close()

## GetCommonPrefix
# @params {term_array} - array of term in a block
# @return {prefix} -returns the common prefix of the terms in the array
def GetCommonPrefix(term_array):
    min_term = min(term_array)
    max_term = max(term_array)
    for index, char in enumerate(min_term):
        if char != max_term[index]:
            return min_term[:index]
    return min_term

def DeltaEnCoding(gap):
    binary_rep = str(bin(gap))[2:]
    gamma_code = GammaEncoding(len(binary_rep))
    offset = binary_rep[1:]
    delta_code = gamma_code + offset
    return delta_code

def FrontCoding(dictionary):
    block_size = 8
    temp_block_size = 0
    delta_encoding_list = []
    term_list = []
    temp_index_list = []
    prefix = ""
    string_dict = ""
    length = 0
    compressed_dict = {}

    for term, posting_list in dictionary:
        length += 1
        if temp_block_size < block_size:
            term_list.append(term)
            temp_block_size += 1
            prev_doc_id = 0

        for doc_id, term_freq in posting_list:
            doc_delta_code = DeltaEnCoding(doc_id - prev_doc_id)
            prev_doc_id = doc_id
            delta_encoding_list.append(doc_delta_code)


        if temp_block_size == block_size or length == len(dictionary) - 1:
            temp_block_size = 0
            prefix = GetCommonPrefix(term_list)
            if prefix:
                string_dict += "["
                for index, item in enumerate(term_list):
                    if item.startswith(prefix):
                        if index == 0:
                            string_dict += str(len(item)) + prefix + "*" + item[len(prefix):]
                        if index > 0:
                            string_dict += str(len(item[len(prefix):])) + "|" + item[len(prefix):]
                    else:
                        if index == 0:
                            string_dict += str(len(item)) + prefix + "*" + item[:]
                        if index > 0:
                            string_dict += str(len(item[:])) + "|" + item[:]
            else:
                string_dict += "["
                for index, item in enumerate(term_list):
                    string_dict += item
            string_dict += "]"
            temp_index_list.append(delta_encoding_list)
            compressed_dict[string_dict] = temp_index_list
            string_dict = ""
            temp_index_list = []
            delta_encoding_list = []
            term_list = []


    fw = open("Index_Version2.compressed.txt", "wb")
    fw.write(str(compressed_dict).encode())
    fw.close()
