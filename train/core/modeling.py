# 上游许可及版权信息见本目录 NOTICE 和 LICENSE。
"基于 PyTorch 的 BERT 模型实现。"


from __future__ import absolute_import, division, print_function, unicode_literals


import copy

import json

import logging

import math

import os

import shutil

import tarfile

import tempfile

import sys

from io import open


import torch

from torch import nn

from torch.nn import CrossEntropyLoss


from .file_utils import cached_path, WEIGHTS_NAME, CONFIG_NAME


logger = logging.getLogger(__name__)


PRETRAINED_MODEL_ARCHIVE_MAP = {

    'bert-base-uncased': "https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-uncased.tar.gz",

    'bert-large-uncased': "https://s3.amazonaws.com/models.huggingface.co/bert/bert-large-uncased.tar.gz",

    'bert-base-cased': "https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-cased.tar.gz",

    'bert-large-cased': "https://s3.amazonaws.com/models.huggingface.co/bert/bert-large-cased.tar.gz",

    'bert-base-multilingual-uncased': "https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-multilingual-uncased.tar.gz",

    'bert-base-multilingual-cased': "https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-multilingual-cased.tar.gz",

    'bert-base-chinese': "https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-chinese.tar.gz",

}

BERT_CONFIG_NAME = 'bert_config.json'

TF_WEIGHTS_NAME = 'model.ckpt'


def load_tf_weights_in_bert(model, tf_checkpoint_path):

    "将 TensorFlow 检查点中的参数加载到 PyTorch BERT 模型。"

    try:

        import re

        import numpy as np

        import tensorflow as tf

    except ImportError:

        print("Loading a TensorFlow models in PyTorch, requires TensorFlow to be installed. Please see "

            "https://www.tensorflow.org/install/ for installation instructions.")

        raise

    tf_path = os.path.abspath(tf_checkpoint_path)

    print("Converting TensorFlow checkpoint from {}".format(tf_path))

    # 从 TensorFlow 模型加载权重。

    init_vars = tf.train.list_variables(tf_path)

    names = []

    arrays = []

    for name, shape in init_vars:

        print("Loading TF weight {} with shape {}".format(name, shape))

        array = tf.train.load_variable(tf_path, name)

        names.append(name)

        arrays.append(array)


    for name, array in zip(names, arrays):

        name = name.split('/')

        # 优化器的一阶、二阶状态用于训练，

        # 预训练模型推理不需要加载这些状态。

        if any(n in ["adam_v", "adam_m", "global_step"] for n in name):

            print("Skipping {}".format("/".join(name)))

            continue

        pointer = model

        for m_name in name:

            if re.fullmatch(r'[A-Za-z]+_\d+', m_name):

                l = re.split(r'_(\d+)', m_name)

            else:

                l = [m_name]

            if l[0] == 'kernel' or l[0] == 'gamma':

                pointer = getattr(pointer, 'weight')

            elif l[0] == 'output_bias' or l[0] == 'beta':

                pointer = getattr(pointer, 'bias')

            elif l[0] == 'output_weights':

                pointer = getattr(pointer, 'weight')

            elif l[0] == 'squad':

                pointer = getattr(pointer, 'classifier')

            else:

                try:

                    pointer = getattr(pointer, l[0])

                except AttributeError:

                    print("Skipping {}".format("/".join(name)))

                    continue

            if len(l) >= 2:

                num = int(l[1])

                pointer = pointer[num]

        if m_name[-11:] == '_embeddings':

            pointer = getattr(pointer, 'weight')

        elif m_name == 'kernel':

            array = np.transpose(array)

        try:

            assert pointer.shape == array.shape

        except AssertionError as e:

            e.args += (pointer.shape, array.shape)

            raise

        print("Initialize PyTorch weight {}".format(name))

        pointer.data = torch.from_numpy(array)

    return model


def gelu(x):

    "高斯误差线性激活函数，使用误差函数计算。"

    return x * 0.5 * (1.0 + torch.erf(x / math.sqrt(2.0)))


def swish(x):

    return x * torch.sigmoid(x)


ACT2FN = {"gelu": gelu, "relu": torch.nn.functional.relu, "swish": swish}


class BertConfig(object):

    "BERT 配置：词表、隐藏层、注意力头、层数和随机丢弃概率。"

    def __init__(self,

                 vocab_size_or_config_json_file,

                 hidden_size=768,

                 num_hidden_layers=12,

                 num_attention_heads=12,

                 intermediate_size=3072,

                 hidden_act="gelu",

                 hidden_dropout_prob=0.1,

                 attention_probs_dropout_prob=0.1,

                 max_position_embeddings=512,

                 type_vocab_size=2,

                 initializer_range=0.02):

        "初始化对象，配置参数包括 vocab_size_or_config_json_file, hidden_size, num_hidden_layers, num_attention_heads, intermediate_size, hidden_act, hidden_dropout_prob, attention_probs_dropout_prob, max_position_embeddings, type_vocab_size, initializer_range。"

        if isinstance(vocab_size_or_config_json_file, str) or (sys.version_info[0] == 2

                        and isinstance(vocab_size_or_config_json_file, unicode)):

            with open(vocab_size_or_config_json_file, "r", encoding='utf-8') as reader:

                json_config = json.loads(reader.read())

            for key, value in json_config.items():

                self.__dict__[key] = value

        elif isinstance(vocab_size_or_config_json_file, int):

            self.vocab_size = vocab_size_or_config_json_file

            self.hidden_size = hidden_size

            self.num_hidden_layers = num_hidden_layers

            self.num_attention_heads = num_attention_heads

            self.hidden_act = hidden_act

            self.intermediate_size = intermediate_size

            self.hidden_dropout_prob = hidden_dropout_prob

            self.attention_probs_dropout_prob = attention_probs_dropout_prob

            self.max_position_embeddings = max_position_embeddings

            self.type_vocab_size = type_vocab_size

            self.initializer_range = initializer_range

        else:

            raise ValueError("First argument must be either a vocabulary size (int)"

                             "or the path to a pretrained model config file (str)")


    @classmethod

    def from_dict(cls, json_object):

        "从字典构造配置对象。"

        config = BertConfig(vocab_size_or_config_json_file=-1)

        for key, value in json_object.items():

            config.__dict__[key] = value

        return config


    @classmethod

    def from_json_file(cls, json_file):

        "从 JSON 文件读取配置。"

        with open(json_file, "r", encoding='utf-8') as reader:

            text = reader.read()

        return cls.from_dict(json.loads(text))


    def __repr__(self):

        return str(self.to_json_string())


    def to_dict(self):

        "将配置转换为字典。"

        output = copy.deepcopy(self.__dict__)

        return output


    def to_json_string(self):

        "将配置序列化为 JSON 字符串。"

        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


    def to_json_file(self, json_file_path):

        "将配置写入 JSON 文件。"

        with open(json_file_path, "w", encoding='utf-8') as writer:

            writer.write(self.to_json_string())


try:

    from apex.normalization.fused_layer_norm import FusedLayerNorm as BertLayerNorm

except ImportError:

    logger.info("Better speed can be achieved with apex installed from https://www.github.com/nvidia/apex .")

    class BertLayerNorm(nn.Module):

        def __init__(self, hidden_size, eps=1e-12):

            "初始化对象，配置参数包括 hidden_size, eps。"

            super(BertLayerNorm, self).__init__()

            self.weight = nn.Parameter(torch.ones(hidden_size))

            self.bias = nn.Parameter(torch.zeros(hidden_size))

            self.variance_epsilon = eps


        def forward(self, x):

            u = x.mean(-1, keepdim=True)

            s = (x - u).pow(2).mean(-1, keepdim=True)

            x = (x - u) / torch.sqrt(s + self.variance_epsilon)

            return self.weight * x + self.bias


class BertEmbeddings(nn.Module):

    "将词元、位置和句段嵌入相加，进行归一化及随机丢弃。"

    def __init__(self, config):

        super(BertEmbeddings, self).__init__()

        self.word_embeddings = nn.Embedding(config.vocab_size, config.hidden_size, padding_idx=0)

        self.position_embeddings = nn.Embedding(config.max_position_embeddings, config.hidden_size)

        self.token_type_embeddings = nn.Embedding(config.type_vocab_size, config.hidden_size)


        # LayerNorm 名称与 TensorFlow 权重中的变量名保持一致，

        # 便于加载相应检查点。

        self.LayerNorm = BertLayerNorm(config.hidden_size, eps=1e-12)

        self.dropout = nn.Dropout(config.hidden_dropout_prob)


    def forward(self, input_ids, token_type_ids=None):

        seq_length = input_ids.size(1)

        position_ids = torch.arange(seq_length, dtype=torch.long, device=input_ids.device)

        position_ids = position_ids.unsqueeze(0).expand_as(input_ids)

        if token_type_ids is None:

            token_type_ids = torch.zeros_like(input_ids)


        words_embeddings = self.word_embeddings(input_ids)

        position_embeddings = self.position_embeddings(position_ids)

        token_type_embeddings = self.token_type_embeddings(token_type_ids)


        embeddings = words_embeddings + position_embeddings + token_type_embeddings

        embeddings = self.LayerNorm(embeddings)

        embeddings = self.dropout(embeddings)

        return embeddings


class BertSelfAttention(nn.Module):

    def __init__(self, config):

        super(BertSelfAttention, self).__init__()

        if config.hidden_size % config.num_attention_heads != 0:

            raise ValueError(

                "The hidden size (%d) is not a multiple of the number of attention "

                "heads (%d)" % (config.hidden_size, config.num_attention_heads))

        self.num_attention_heads = config.num_attention_heads

        self.attention_head_size = int(config.hidden_size / config.num_attention_heads)

        self.all_head_size = self.num_attention_heads * self.attention_head_size


        self.query = nn.Linear(config.hidden_size, self.all_head_size)

        self.key = nn.Linear(config.hidden_size, self.all_head_size)

        self.value = nn.Linear(config.hidden_size, self.all_head_size)


        self.dropout = nn.Dropout(config.attention_probs_dropout_prob)


    def transpose_for_scores(self, x):

        new_x_shape = x.size()[:-1] + (self.num_attention_heads, self.attention_head_size)

        x = x.view(*new_x_shape)

        return x.permute(0, 2, 1, 3)


    def forward(self, hidden_states, attention_mask):

        mixed_query_layer = self.query(hidden_states)

        mixed_key_layer = self.key(hidden_states)

        mixed_value_layer = self.value(hidden_states)


        query_layer = self.transpose_for_scores(mixed_query_layer)

        key_layer = self.transpose_for_scores(mixed_key_layer)

        value_layer = self.transpose_for_scores(mixed_value_layer)


        # 计算查询与键的点积，得到未归一化的注意力分数。

        attention_scores = torch.matmul(query_layer, key_layer.transpose(-1, -2))

        attention_scores = attention_scores / math.sqrt(self.attention_head_size)

        # 应用已在前向传播中构造的注意力掩码。

        attention_scores = attention_scores + attention_mask


        # 将注意力分数归一化为概率。

        attention_probs = nn.Softmax(dim=-1)(attention_scores)


        # 此处随机屏蔽部分被关注的词元，

        # 与原始 Transformer 的注意力丢弃方式一致。

        attention_probs = self.dropout(attention_probs)


        context_layer = torch.matmul(attention_probs, value_layer)

        context_layer = context_layer.permute(0, 2, 1, 3).contiguous()

        new_context_layer_shape = context_layer.size()[:-2] + (self.all_head_size,)

        context_layer = context_layer.view(*new_context_layer_shape)

        return context_layer


class BertSelfOutput(nn.Module):

    def __init__(self, config):

        super(BertSelfOutput, self).__init__()

        self.dense = nn.Linear(config.hidden_size, config.hidden_size)

        self.LayerNorm = BertLayerNorm(config.hidden_size, eps=1e-12)

        self.dropout = nn.Dropout(config.hidden_dropout_prob)


    def forward(self, hidden_states, input_tensor):

        hidden_states = self.dense(hidden_states)

        hidden_states = self.dropout(hidden_states)

        hidden_states = self.LayerNorm(hidden_states + input_tensor)

        return hidden_states


class BertAttention(nn.Module):

    def __init__(self, config):

        super(BertAttention, self).__init__()

        self.self = BertSelfAttention(config)

        self.output = BertSelfOutput(config)


    def forward(self, input_tensor, attention_mask):

        self_output = self.self(input_tensor, attention_mask)

        attention_output = self.output(self_output, input_tensor)

        return attention_output


class BertIntermediate(nn.Module):

    def __init__(self, config):

        super(BertIntermediate, self).__init__()

        self.dense = nn.Linear(config.hidden_size, config.intermediate_size)

        if isinstance(config.hidden_act, str) or (sys.version_info[0] == 2 and isinstance(config.hidden_act, unicode)):

            self.intermediate_act_fn = ACT2FN[config.hidden_act]

        else:

            self.intermediate_act_fn = config.hidden_act


    def forward(self, hidden_states):

        hidden_states = self.dense(hidden_states)

        hidden_states = self.intermediate_act_fn(hidden_states)

        return hidden_states


class BertOutput(nn.Module):

    def __init__(self, config):

        super(BertOutput, self).__init__()

        self.dense = nn.Linear(config.intermediate_size, config.hidden_size)

        self.LayerNorm = BertLayerNorm(config.hidden_size, eps=1e-12)

        self.dropout = nn.Dropout(config.hidden_dropout_prob)


    def forward(self, hidden_states, input_tensor):

        hidden_states = self.dense(hidden_states)

        hidden_states = self.dropout(hidden_states)

        hidden_states = self.LayerNorm(hidden_states + input_tensor)

        return hidden_states


class BertLayer(nn.Module):

    def __init__(self, config):

        super(BertLayer, self).__init__()

        self.attention = BertAttention(config)

        self.intermediate = BertIntermediate(config)

        self.output = BertOutput(config)


    def forward(self, hidden_states, attention_mask):

        attention_output = self.attention(hidden_states, attention_mask)

        intermediate_output = self.intermediate(attention_output)

        layer_output = self.output(intermediate_output, attention_output)

        return layer_output


class BertEncoder(nn.Module):

    def __init__(self, config):

        super(BertEncoder, self).__init__()

        layer = BertLayer(config)

        self.layer = nn.ModuleList([copy.deepcopy(layer) for _ in range(config.num_hidden_layers)])


    def forward(self, hidden_states, attention_mask, output_all_encoded_layers=True):

        all_encoder_layers = []

        for layer_module in self.layer:

            hidden_states = layer_module(hidden_states, attention_mask)

            if output_all_encoded_layers:

                all_encoder_layers.append(hidden_states)

        if not output_all_encoded_layers:

            all_encoder_layers.append(hidden_states)

        return all_encoder_layers


class BertPooler(nn.Module):

    def __init__(self, config):

        super(BertPooler, self).__init__()

        self.dense = nn.Linear(config.hidden_size, config.hidden_size)

        self.activation = nn.Tanh()


    def forward(self, hidden_states):

        # 使用第一个词元对应的隐藏状态，

        # 作为池化层的输入。

        first_token_tensor = hidden_states[:, 0]

        pooled_output = self.dense(first_token_tensor)

        pooled_output = self.activation(pooled_output)

        return pooled_output


class BertPredictionHeadTransform(nn.Module):

    def __init__(self, config):

        super(BertPredictionHeadTransform, self).__init__()

        self.dense = nn.Linear(config.hidden_size, config.hidden_size)

        if isinstance(config.hidden_act, str) or (sys.version_info[0] == 2 and isinstance(config.hidden_act, unicode)):

            self.transform_act_fn = ACT2FN[config.hidden_act]

        else:

            self.transform_act_fn = config.hidden_act

        self.LayerNorm = BertLayerNorm(config.hidden_size, eps=1e-12)


    def forward(self, hidden_states):

        hidden_states = self.dense(hidden_states)

        hidden_states = self.transform_act_fn(hidden_states)

        hidden_states = self.LayerNorm(hidden_states)

        return hidden_states


class BertLMPredictionHead(nn.Module):

    def __init__(self, config, bert_model_embedding_weights):

        super(BertLMPredictionHead, self).__init__()

        self.transform = BertPredictionHeadTransform(config)


        # 输出层与输入嵌入共享权重，

        # 同时保留独立的输出偏置。

        self.decoder = nn.Linear(bert_model_embedding_weights.size(1),

                                 bert_model_embedding_weights.size(0),

                                 bias=False)

        self.decoder.weight = bert_model_embedding_weights

        self.bias = nn.Parameter(torch.zeros(bert_model_embedding_weights.size(0)))


    def forward(self, hidden_states):

        hidden_states = self.transform(hidden_states)

        hidden_states = self.decoder(hidden_states) + self.bias

        return hidden_states


class BertOnlyMLMHead(nn.Module):

    def __init__(self, config, bert_model_embedding_weights):

        super(BertOnlyMLMHead, self).__init__()

        self.predictions = BertLMPredictionHead(config, bert_model_embedding_weights)


    def forward(self, sequence_output):

        prediction_scores = self.predictions(sequence_output)

        return prediction_scores


class BertOnlyNSPHead(nn.Module):

    def __init__(self, config):

        super(BertOnlyNSPHead, self).__init__()

        self.seq_relationship = nn.Linear(config.hidden_size, 2)


    def forward(self, pooled_output):

        seq_relationship_score = self.seq_relationship(pooled_output)

        return seq_relationship_score


class BertPreTrainingHeads(nn.Module):

    def __init__(self, config, bert_model_embedding_weights):

        super(BertPreTrainingHeads, self).__init__()

        self.predictions = BertLMPredictionHead(config, bert_model_embedding_weights)

        self.seq_relationship = nn.Linear(config.hidden_size, 2)


    def forward(self, sequence_output, pooled_output):

        prediction_scores = self.predictions(sequence_output)

        seq_relationship_score = self.seq_relationship(pooled_output)

        return prediction_scores, seq_relationship_score


class BertPreTrainedModel(nn.Module):

    "封装 BERT 参数初始化和预训练模型加载。"

    def __init__(self, config, *inputs, **kwargs):

        super(BertPreTrainedModel, self).__init__()

        if not isinstance(config, BertConfig):

            raise ValueError(

                "Parameter config in `{}(config)` should be an instance of class `BertConfig`. "

                "To create a model from a Google pretrained model use "

                "`model = {}.from_pretrained(PRETRAINED_MODEL_NAME)`".format(

                    self.__class__.__name__, self.__class__.__name__

                ))

        self.config = config


    def init_bert_weights(self, module):

        "初始化模型参数。"

        if isinstance(module, (nn.Linear, nn.Embedding)):

            # 此处的正态初始化与 TensorFlow 的截断正态初始化略有不同。

            # 初始化实现参考：https://github.com/pytorch/pytorch/pull/5617

            module.weight.data.normal_(mean=0.0, std=self.config.initializer_range)

        elif isinstance(module, BertLayerNorm):

            module.bias.data.zero_()

            module.weight.data.fill_(1.0)

        if isinstance(module, nn.Linear) and module.bias is not None:

            module.bias.data.zero_()


    @classmethod

    def from_pretrained(cls, pretrained_model_name_or_path, *inputs, **kwargs):

        "从预训练名称、本地目录或缓存加载模型或分词器，并应用传入的配置参数。"

        state_dict = kwargs.get('state_dict', None)

        kwargs.pop('state_dict', None)

        cache_dir = kwargs.get('cache_dir', None)

        kwargs.pop('cache_dir', None)

        from_tf = kwargs.get('from_tf', False)

        kwargs.pop('from_tf', None)


        if pretrained_model_name_or_path in PRETRAINED_MODEL_ARCHIVE_MAP:

            archive_file = PRETRAINED_MODEL_ARCHIVE_MAP[pretrained_model_name_or_path]

        else:

            archive_file = pretrained_model_name_or_path

        # 必要时转到缓存文件。

        try:

            resolved_archive_file = cached_path(archive_file, cache_dir=cache_dir)

        except EnvironmentError:

            logger.error(

                "Model name '{}' was not found in model name list ({}). "

                "We assumed '{}' was a path or url but couldn't find any file "

                "associated to this path or url.".format(

                    pretrained_model_name_or_path,

                    ', '.join(PRETRAINED_MODEL_ARCHIVE_MAP.keys()),

                    archive_file))

            return None

        if resolved_archive_file == archive_file:

            logger.info("loading archive file {}".format(archive_file))

        else:

            logger.info("loading archive file {} from cache at {}".format(

                archive_file, resolved_archive_file))

        tempdir = None

        if os.path.isdir(resolved_archive_file) or from_tf:

            serialization_dir = resolved_archive_file

        else:

            # 将模型归档解压到临时目录。

            tempdir = tempfile.mkdtemp()

            logger.info("extracting archive file {} to temp dir {}".format(

                resolved_archive_file, tempdir))

            with tarfile.open(resolved_archive_file, 'r:gz') as archive:

                archive.extractall(tempdir)

            serialization_dir = tempdir

        # 加载模型配置。

        config_file = os.path.join(serialization_dir, CONFIG_NAME)

        if not os.path.exists(config_file):

            # 兼容旧版配置文件名。

            config_file = os.path.join(serialization_dir, BERT_CONFIG_NAME)

        config = BertConfig.from_json_file(config_file)

        logger.info("Model config {}".format(config))

        # 创建模型实例。

        model = cls(config, *inputs, **kwargs)

        if state_dict is None and not from_tf:

            weights_path = os.path.join(serialization_dir, WEIGHTS_NAME)

            state_dict = torch.load(weights_path, map_location='cpu')

        if tempdir:

            # 清理临时目录。

            shutil.rmtree(tempdir)

        if from_tf:

            # 直接读取 TensorFlow 检查点。

            weights_path = os.path.join(serialization_dir, TF_WEIGHTS_NAME)

            return load_tf_weights_in_bert(model, weights_path)

        # 读取 PyTorch 状态字典。

        old_keys = []

        new_keys = []

        for key in state_dict.keys():

            new_key = None

            if 'gamma' in key:

                new_key = key.replace('gamma', 'weight')

            if 'beta' in key:

                new_key = key.replace('beta', 'bias')

            if new_key:

                old_keys.append(key)

                new_keys.append(new_key)

        for old_key, new_key in zip(old_keys, new_keys):

            state_dict[new_key] = state_dict.pop(old_key)


        missing_keys = []

        unexpected_keys = []

        error_msgs = []

        # 复制状态字典，以便加载过程中修改键名。

        metadata = getattr(state_dict, '_metadata', None)

        state_dict = state_dict.copy()

        if metadata is not None:

            state_dict._metadata = metadata


        def load(module, prefix=''):

            local_metadata = {} if metadata is None else metadata.get(prefix[:-1], {})

            module._load_from_state_dict(

                state_dict, prefix, local_metadata, True, missing_keys, unexpected_keys, error_msgs)

            for name, child in module._modules.items():

                if child is not None:

                    load(child, prefix + name + '.')

        start_prefix = ''

        if not hasattr(model, 'bert') and any(s.startswith('bert.') for s in state_dict.keys()):

            start_prefix = 'bert.'

        load(model, prefix=start_prefix)

        if len(missing_keys) > 0:

            logger.info("Weights of {} not initialized from pretrained model: {}".format(

                model.__class__.__name__, missing_keys))

        if len(unexpected_keys) > 0:

            logger.info("Weights from pretrained model not used in {}: {}".format(

                model.__class__.__name__, unexpected_keys))

        if len(error_msgs) > 0:

            raise RuntimeError('Error(s) in loading state_dict for {}:\n\t{}'.format(

                               model.__class__.__name__, "\n\t".join(error_msgs)))

        return model


class BertModel(BertPreTrainedModel):

    "BERT 编码器。输入词元编号、句段编号和注意力掩码；返回各层或最后一层隐藏状态，以及首词元对应的池化向量。"

    def __init__(self, config):

        super(BertModel, self).__init__(config)

        self.embeddings = BertEmbeddings(config)

        self.encoder = BertEncoder(config)

        self.pooler = BertPooler(config)

        self.apply(self.init_bert_weights)


    def forward(self, input_ids, token_type_ids=None, attention_mask=None, output_all_encoded_layers=True):

        if attention_mask is None:

            attention_mask = torch.ones_like(input_ids)

        if token_type_ids is None:

            token_type_ids = torch.zeros_like(input_ids)


        # 将二维词元掩码扩展为注意力掩码。

        # 扩展后的形状为 [批大小, 1, 1, 目标序列长度]。

        # 通过广播匹配多头注意力的查询和键维度。

        # BERT 使用双向注意力，掩码不需要因果三角结构；

        # 此处只需准备正确的广播维度。

        extended_attention_mask = attention_mask.unsqueeze(1).unsqueeze(2)


        # 掩码中 1 表示保留，0 表示屏蔽；

        # 将其转换成加到注意力分数上的偏置，

        # 保留位置为 0，屏蔽位置为 -10000。

        # 在概率归一化前加入该偏置，

        # 可使屏蔽位置的概率接近零。

        extended_attention_mask = extended_attention_mask.to(dtype=next(self.parameters()).dtype) # 兼容半精度计算。

        extended_attention_mask = (1.0 - extended_attention_mask) * -10000.0


        embedding_output = self.embeddings(input_ids, token_type_ids)

        encoded_layers = self.encoder(embedding_output,

                                      extended_attention_mask,

                                      output_all_encoded_layers=output_all_encoded_layers)

        sequence_output = encoded_layers[-1]

        pooled_output = self.pooler(sequence_output)

        if not output_all_encoded_layers:

            encoded_layers = encoded_layers[-1]

        return encoded_layers, pooled_output


class BertForPreTraining(BertPreTrainedModel):

    "BERT 预训练任务头，联合处理掩码语言建模与下一句预测。提供标签时返回训练损失，否则返回两项预测分数。"

    def __init__(self, config):

        super(BertForPreTraining, self).__init__(config)

        self.bert = BertModel(config)

        self.cls = BertPreTrainingHeads(config, self.bert.embeddings.word_embeddings.weight)

        self.apply(self.init_bert_weights)


    def forward(self, input_ids, token_type_ids=None, attention_mask=None, masked_lm_labels=None, next_sentence_label=None):

        sequence_output, pooled_output = self.bert(input_ids, token_type_ids, attention_mask,

                                                   output_all_encoded_layers=False)

        prediction_scores, seq_relationship_score = self.cls(sequence_output, pooled_output)


        if masked_lm_labels is not None and next_sentence_label is not None:

            loss_fct = CrossEntropyLoss(ignore_index=-1)

            masked_lm_loss = loss_fct(prediction_scores.view(-1, self.config.vocab_size), masked_lm_labels.view(-1))

            next_sentence_loss = loss_fct(seq_relationship_score.view(-1, 2), next_sentence_label.view(-1))

            total_loss = masked_lm_loss + next_sentence_loss

            return total_loss

        else:

            return prediction_scores, seq_relationship_score


class BertForMaskedLM(BertPreTrainedModel):

    "BERT 掩码语言建模。提供词元标签时计算损失，否则返回词表上的预测分数。"

    def __init__(self, config):

        super(BertForMaskedLM, self).__init__(config)

        self.bert = BertModel(config)

        self.cls = BertOnlyMLMHead(config, self.bert.embeddings.word_embeddings.weight)

        self.apply(self.init_bert_weights)


    def forward(self, input_ids, token_type_ids=None, attention_mask=None, masked_lm_labels=None):

        sequence_output, _ = self.bert(input_ids, token_type_ids, attention_mask,

                                       output_all_encoded_layers=False)

        prediction_scores = self.cls(sequence_output)


        if masked_lm_labels is not None:

            loss_fct = CrossEntropyLoss(ignore_index=-1)

            masked_lm_loss = loss_fct(prediction_scores.view(-1, self.config.vocab_size), masked_lm_labels.view(-1))

            return masked_lm_loss

        else:

            return prediction_scores


class BertForNextSentencePrediction(BertPreTrainedModel):

    "BERT 下一句预测任务。提供句对标签时计算损失，否则返回句对关系分数。"

    def __init__(self, config):

        super(BertForNextSentencePrediction, self).__init__(config)

        self.bert = BertModel(config)

        self.cls = BertOnlyNSPHead(config)

        self.apply(self.init_bert_weights)


    def forward(self, input_ids, token_type_ids=None, attention_mask=None, next_sentence_label=None):

        _, pooled_output = self.bert(input_ids, token_type_ids, attention_mask,

                                     output_all_encoded_layers=False)

        seq_relationship_score = self.cls( pooled_output)


        if next_sentence_label is not None:

            loss_fct = CrossEntropyLoss(ignore_index=-1)

            next_sentence_loss = loss_fct(seq_relationship_score.view(-1, 2), next_sentence_label.view(-1))

            return next_sentence_loss

        else:

            return seq_relationship_score


class BertForSequenceClassification(BertPreTrainedModel):

    "在 BERT 池化向量上进行序列分类。提供类别标签时计算损失，否则返回各类别分数。"

    def __init__(self, config, num_labels):

        super(BertForSequenceClassification, self).__init__(config)

        self.num_labels = num_labels

        self.bert = BertModel(config)

        self.dropout = nn.Dropout(config.hidden_dropout_prob)

        self.classifier = nn.Linear(config.hidden_size, num_labels)

        self.apply(self.init_bert_weights)


    def forward(self, input_ids, token_type_ids=None, attention_mask=None, labels=None):

        _, pooled_output = self.bert(input_ids, token_type_ids, attention_mask, output_all_encoded_layers=False)

        pooled_output = self.dropout(pooled_output)

        logits = self.classifier(pooled_output)


        if labels is not None:

            loss_fct = CrossEntropyLoss()

            loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))

            return loss

        else:

            return logits


class BertForMultipleChoice(BertPreTrainedModel):

    "BERT 多选任务头，对每个选项分别编码。提供正确选项时计算损失，否则返回选项分数。"

    def __init__(self, config, num_choices):

        super(BertForMultipleChoice, self).__init__(config)

        self.num_choices = num_choices

        self.bert = BertModel(config)

        self.dropout = nn.Dropout(config.hidden_dropout_prob)

        self.classifier = nn.Linear(config.hidden_size, 1)

        self.apply(self.init_bert_weights)


    def forward(self, input_ids, token_type_ids=None, attention_mask=None, labels=None):

        flat_input_ids = input_ids.view(-1, input_ids.size(-1))

        flat_token_type_ids = token_type_ids.view(-1, token_type_ids.size(-1)) if token_type_ids is not None else None

        flat_attention_mask = attention_mask.view(-1, attention_mask.size(-1)) if attention_mask is not None else None

        _, pooled_output = self.bert(flat_input_ids, flat_token_type_ids, flat_attention_mask, output_all_encoded_layers=False)

        pooled_output = self.dropout(pooled_output)

        logits = self.classifier(pooled_output)

        reshaped_logits = logits.view(-1, self.num_choices)


        if labels is not None:

            loss_fct = CrossEntropyLoss()

            loss = loss_fct(reshaped_logits, labels)

            return loss

        else:

            return reshaped_logits


class BertForTokenClassification(BertPreTrainedModel):

    "BERT 词元分类任务头。根据有效位置的词元标签计算损失，或返回逐词元类别分数。"

    def __init__(self, config, num_labels):

        super(BertForTokenClassification, self).__init__(config)

        self.num_labels = num_labels

        self.bert = BertModel(config)

        self.dropout = nn.Dropout(config.hidden_dropout_prob)

        self.classifier = nn.Linear(config.hidden_size, num_labels)

        self.apply(self.init_bert_weights)


    def forward(self, input_ids, token_type_ids=None, attention_mask=None, labels=None):

        sequence_output, _ = self.bert(input_ids, token_type_ids, attention_mask, output_all_encoded_layers=False)

        sequence_output = self.dropout(sequence_output)

        logits = self.classifier(sequence_output)


        if labels is not None:

            loss_fct = CrossEntropyLoss()

            # 只计算有效词元位置的损失。

            if attention_mask is not None:

                active_loss = attention_mask.view(-1) == 1

                active_logits = logits.view(-1, self.num_labels)[active_loss]

                active_labels = labels.view(-1)[active_loss]

                loss = loss_fct(active_logits, active_labels)

            else:

                loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))

            return loss

        else:

            return logits


class BertForQuestionAnswering(BertPreTrainedModel):

    "BERT 抽取式问答，预测答案起止位置。提供位置标签时计算损失，否则返回起止分数。"

    def __init__(self, config):

        super(BertForQuestionAnswering, self).__init__(config)

        self.bert = BertModel(config)

        # 此问答输出层与原 TensorFlow 实现一致，未加入额外随机丢弃。


        self.qa_outputs = nn.Linear(config.hidden_size, 2)

        self.apply(self.init_bert_weights)


    def forward(self, input_ids, token_type_ids=None, attention_mask=None, start_positions=None, end_positions=None):

        sequence_output, _ = self.bert(input_ids, token_type_ids, attention_mask, output_all_encoded_layers=False)

        logits = self.qa_outputs(sequence_output)

        start_logits, end_logits = logits.split(1, dim=-1)

        start_logits = start_logits.squeeze(-1)

        end_logits = end_logits.squeeze(-1)


        if start_positions is not None and end_positions is not None:

            # 多设备输入需要保留题目选项维度。

            if len(start_positions.size()) > 1:

                start_positions = start_positions.squeeze(-1)

            if len(end_positions.size()) > 1:

                end_positions = end_positions.squeeze(-1)

            # 忽略超出当前输入范围的答案起止位置。

            ignored_index = start_logits.size(1)

            start_positions.clamp_(0, ignored_index)

            end_positions.clamp_(0, ignored_index)


            loss_fct = CrossEntropyLoss(ignore_index=ignored_index)

            start_loss = loss_fct(start_logits, start_positions)

            end_loss = loss_fct(end_logits, end_positions)

            total_loss = (start_loss + end_loss) / 2

            return total_loss

        else:

            return start_logits, end_logits
