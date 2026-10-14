# 上游许可及版权信息见本目录 NOTICE 和 LICENSE。
"BERT 分词器实现。"


from __future__ import absolute_import, division, print_function, unicode_literals


import collections

import logging

import os

import unicodedata

from io import open


from core.file_utils import cached_path


logger = logging.getLogger(__name__)


PRETRAINED_VOCAB_ARCHIVE_MAP = {

    'bert-base-uncased': "https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-uncased-vocab.txt",

    'bert-large-uncased': "https://s3.amazonaws.com/models.huggingface.co/bert/bert-large-uncased-vocab.txt",

    'bert-base-cased': "https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-cased-vocab.txt",

    'bert-large-cased': "https://s3.amazonaws.com/models.huggingface.co/bert/bert-large-cased-vocab.txt",

    'bert-base-multilingual-uncased': "https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-multilingual-uncased-vocab.txt",

    'bert-base-multilingual-cased': "https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-multilingual-cased-vocab.txt",

    'bert-base-chinese': "https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-chinese-vocab.txt",

}

PRETRAINED_VOCAB_POSITIONAL_EMBEDDINGS_SIZE_MAP = {

    'bert-base-uncased': 512,

    'bert-large-uncased': 512,

    'bert-base-cased': 512,

    'bert-large-cased': 512,

    'bert-base-multilingual-uncased': 512,

    'bert-base-multilingual-cased': 512,

    'bert-base-chinese': 512,

}

VOCAB_NAME = 'vocab.txt'


def load_vocab(vocab_file):

    "从词表文件读取词元及其编号。"

    vocab = collections.OrderedDict()

    index = 0

    with open(vocab_file, "r", encoding="utf-8") as reader:

        while True:

            token = reader.readline()

            if not token:

                break

            token = token.strip()

            vocab[token] = index

            index += 1

    return vocab


def whitespace_tokenize(text):

    "按空白字符切分文本，忽略空输入。"

    text = text.strip()

    if not text:

        return []

    tokens = text.split()

    return tokens


class BertTokenizer(object):

    "组合基础分词和子词分词，提供词元与编号转换。"


    def __init__(self, vocab_file, do_lower_case=True, max_len=None, do_basic_tokenize=True,

                 never_split=("[UNK]", "[SEP]", "[PAD]", "[CLS]", "[MASK]")):

        "初始化对象，配置参数包括 vocab_file, do_lower_case, max_len, do_basic_tokenize, never_split。"

        if not os.path.isfile(vocab_file):

            raise ValueError(

                "Can't find a vocabulary file at path '{}'. To load the vocabulary from a Google pretrained "

                "model use `tokenizer = BertTokenizer.from_pretrained(PRETRAINED_MODEL_NAME)`".format(vocab_file))

        self.vocab = load_vocab(vocab_file)

        self.ids_to_tokens = collections.OrderedDict(

            [(ids, tok) for tok, ids in self.vocab.items()])

        self.do_basic_tokenize = do_basic_tokenize

        if do_basic_tokenize:

          self.basic_tokenizer = BasicTokenizer(do_lower_case=do_lower_case,

                                                never_split=never_split)

        self.wordpiece_tokenizer = WordpieceTokenizer(vocab=self.vocab)

        self.max_len = max_len if max_len is not None else int(1e12)


    def tokenize(self, text):

        split_tokens = []

        if self.do_basic_tokenize:

            for token in self.basic_tokenizer.tokenize(text):

                for sub_token in self.wordpiece_tokenizer.tokenize(token):

                    split_tokens.append(sub_token)

        else:

            split_tokens = self.wordpiece_tokenizer.tokenize(text)

        return split_tokens


    def convert_tokens_to_ids(self, tokens):

        "将词元转换为词表编号。"

        ids = []

        for token in tokens:

            ids.append(self.vocab[token])

        if len(ids) > self.max_len:

            logger.warning(

                "Token indices sequence length is longer than the specified maximum "

                " sequence length for this BERT model ({} > {}). Running this"

                " sequence through BERT will result in indexing errors".format(len(ids), self.max_len)

            )

        return ids


    def convert_ids_to_tokens(self, ids):

        "将词表编号转换回词元。"

        tokens = []

        for i in ids:

            tokens.append(self.ids_to_tokens[i])

        return tokens


    def save_vocabulary(self, vocab_path):

        "将词表保存到指定目录。"

        index = 0

        if os.path.isdir(vocab_path):

            vocab_file = os.path.join(vocab_path, VOCAB_NAME)

        with open(vocab_file, "w", encoding="utf-8") as writer:

            for token, token_index in sorted(self.vocab.items(), key=lambda kv: kv[1]):

                if index != token_index:

                    logger.warning("Saving vocabulary to {}: vocabulary indices are not consecutive."

                                   " Please check that the vocabulary is not corrupted!".format(vocab_file))

                    index = token_index

                writer.write(token + u'\n')

                index += 1

        return vocab_file


    @classmethod

    def from_pretrained(cls, pretrained_model_name_or_path, cache_dir=None, *inputs, **kwargs):

        "从预训练名称、本地目录或缓存加载模型或分词器，并应用传入的配置参数。"

        if pretrained_model_name_or_path in PRETRAINED_VOCAB_ARCHIVE_MAP:

            vocab_file = PRETRAINED_VOCAB_ARCHIVE_MAP[pretrained_model_name_or_path]

            if '-cased' in pretrained_model_name_or_path and kwargs.get('do_lower_case', True):

                logger.warning("The pre-trained model you are loading is a cased model but you have not set "

                               "`do_lower_case` to False. We are setting `do_lower_case=False` for you but "

                               "you may want to check this behavior.")

                kwargs['do_lower_case'] = False

            elif '-cased' not in pretrained_model_name_or_path and not kwargs.get('do_lower_case', True):

                logger.warning("The pre-trained model you are loading is an uncased model but you have set "

                               "`do_lower_case` to False. We are setting `do_lower_case=True` for you "

                               "but you may want to check this behavior.")

                kwargs['do_lower_case'] = True

        else:

            vocab_file = pretrained_model_name_or_path

        if os.path.isdir(vocab_file):

            vocab_file = os.path.join(vocab_file, VOCAB_NAME)

        # 必要时转到缓存文件。

        try:

            resolved_vocab_file = cached_path(vocab_file, cache_dir=cache_dir)

        except EnvironmentError:

            logger.error(

                "Model name '{}' was not found in model name list ({}). "

                "We assumed '{}' was a path or url but couldn't find any file "

                "associated to this path or url.".format(

                    pretrained_model_name_or_path,

                    ', '.join(PRETRAINED_VOCAB_ARCHIVE_MAP.keys()),

                    vocab_file))

            return None

        if resolved_vocab_file == vocab_file:

            logger.info("loading vocabulary file {}".format(vocab_file))

        else:

            logger.info("loading vocabulary file {} from cache at {}".format(

                vocab_file, resolved_vocab_file))

        if pretrained_model_name_or_path in PRETRAINED_VOCAB_POSITIONAL_EMBEDDINGS_SIZE_MAP:

            # 使用预训练模型时，限制分词序列长度，

            # 确保不超过位置嵌入表的大小。

            max_len = PRETRAINED_VOCAB_POSITIONAL_EMBEDDINGS_SIZE_MAP[pretrained_model_name_or_path]

            kwargs['max_len'] = min(kwargs.get('max_len', int(1e12)), max_len)

        # 创建分词器实例。

        tokenizer = cls(resolved_vocab_file, *inputs, **kwargs)

        return tokenizer


class BasicTokenizer(object):

    "基础分词器，处理空白、大小写、重音、标点及中文字符。"


    def __init__(self,

                 do_lower_case=True,

                 never_split=("[UNK]", "[SEP]", "[PAD]", "[CLS]", "[MASK]")):

        "初始化对象，配置参数包括 do_lower_case, never_split。"

        self.do_lower_case = do_lower_case

        self.never_split = never_split


    def tokenize(self, text):

        "对输入文本进行基础分词或子词切分，返回词元列表。"

        text = self._clean_text(text)

        # 中文字符切分规则用于中文和多语言模型，

        # 同时也应用于英文模型；

        # 英文模型的训练数据主要为英文，

        # 词表仍可能包含部分中文字符，

        # 因为英文维基百科中也有中文词汇。

        # 中文字符统一采用单字切分。

        text = self._tokenize_chinese_chars(text)

        orig_tokens = whitespace_tokenize(text)

        split_tokens = []

        for token in orig_tokens:

            if self.do_lower_case and token not in self.never_split:

                token = token.lower()

                token = self._run_strip_accents(token)

            split_tokens.extend(self._run_split_on_punc(token))


        output_tokens = whitespace_tokenize(" ".join(split_tokens))

        return output_tokens


    def _run_strip_accents(self, text):

        "移除字符的重音标记。"

        text = unicodedata.normalize("NFD", text)

        output = []

        for char in text:

            cat = unicodedata.category(char)

            if cat == "Mn":

                continue

            output.append(char)

        return "".join(output)


    def _run_split_on_punc(self, text):

        "按标点边界拆分词元。"

        if text in self.never_split:

            return [text]

        chars = list(text)

        i = 0

        start_new_word = True

        output = []

        while i < len(chars):

            char = chars[i]

            if _is_punctuation(char):

                output.append([char])

                start_new_word = True

            else:

                if start_new_word:

                    output.append([])

                start_new_word = False

                output[-1].append(char)

            i += 1


        return ["".join(x) for x in output]


    def _tokenize_chinese_chars(self, text):

        "在中文字符周围添加分隔空白。"

        output = []

        for char in text:

            cp = ord(char)

            if self._is_chinese_char(cp):

                output.append(" ")

                output.append(char)

                output.append(" ")

            else:

                output.append(char)

        return "".join(output)


    def _is_chinese_char(self, cp):

        "判断字符是否位于 CJK 统一表意文字范围。"

        # 按 CJK 统一表意文字范围判断中文字符。

        # 字符范围参考：https://en.wikipedia.org/wiki/CJK_Unified_Ideographs_(Unicode_block)

        #

        # CJK 表意文字范围不包括所有日文、韩文字符；

        # 韩文音节使用独立的 Unicode 区块，

        # 日文平假名、片假名同样使用独立区块；

        # 这些字符不套用本函数的中文单字规则，

        # 而由后续分词流程处理。

        if ((cp >= 0x4E00 and cp <= 0x9FFF) or  #

                (cp >= 0x3400 and cp <= 0x4DBF) or  #

                (cp >= 0x20000 and cp <= 0x2A6DF) or  #

                (cp >= 0x2A700 and cp <= 0x2B73F) or  #

                (cp >= 0x2B740 and cp <= 0x2B81F) or  #

                (cp >= 0x2B820 and cp <= 0x2CEAF) or

                (cp >= 0xF900 and cp <= 0xFAFF) or  #

                (cp >= 0x2F800 and cp <= 0x2FA1F)):  #

            return True


        return False


    def _clean_text(self, text):

        "移除无效或控制字符，并统一空白。"

        output = []

        for char in text:

            cp = ord(char)

            if cp == 0 or cp == 0xfffd or _is_control(char):

                continue

            if _is_whitespace(char):

                output.append(" ")

            else:

                output.append(char)

        return "".join(output)


class WordpieceTokenizer(object):

    "通过最长匹配将词语拆为词表中的子词。"


    def __init__(self, vocab, unk_token="[UNK]", max_input_chars_per_word=100):

        self.vocab = vocab

        self.unk_token = unk_token

        self.max_input_chars_per_word = max_input_chars_per_word


    def tokenize(self, text):

        "对输入文本进行基础分词或子词切分，返回词元列表。"


        output_tokens = []

        for token in whitespace_tokenize(text):

            chars = list(token)

            if len(chars) > self.max_input_chars_per_word:

                output_tokens.append(self.unk_token)

                continue


            is_bad = False

            start = 0

            sub_tokens = []

            while start < len(chars):

                end = len(chars)

                cur_substr = None

                while start < end:

                    substr = "".join(chars[start:end])

                    if start > 0:

                        substr = "##" + substr

                    if substr in self.vocab:

                        cur_substr = substr

                        break

                    end -= 1

                if cur_substr is None:

                    is_bad = True

                    break

                sub_tokens.append(cur_substr)

                start = end


            if is_bad:

                output_tokens.append(self.unk_token)

            else:

                output_tokens.extend(sub_tokens)

        return output_tokens


def _is_whitespace(char):

    "判断字符是否为空白。"

    # 制表符、换行符和回车符在 Unicode 中属于控制字符，

    # 此处按空白字符处理。

    if char == " " or char == "\t" or char == "\n" or char == "\r":

        return True

    cat = unicodedata.category(char)

    if cat == "Zs":

        return True

    return False


def _is_control(char):

    "判断字符是否为应移除的控制字符。"

    # 这些字符虽属于控制字符，

    # 但此处按空白字符处理。

    if char == "\t" or char == "\n" or char == "\r":

        return False

    cat = unicodedata.category(char)

    if cat.startswith("C"):

        return True

    return False


def _is_punctuation(char):

    "判断字符是否为标点。"

    cp = ord(char)

    # 非字母和数字的 ASCII 字符按标点处理。

    # 部分符号不属于 Unicode 标点类别，

    # 为保持分词行为一致，

    # 仍按标点处理。

    if ((cp >= 33 and cp <= 47) or (cp >= 58 and cp <= 64) or

            (cp >= 91 and cp <= 96) or (cp >= 123 and cp <= 126)):

        return True

    cat = unicodedata.category(char)

    if cat.startswith("P"):

        return True

    return False
