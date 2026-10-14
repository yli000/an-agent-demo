# 上游许可及版权信息见本目录 NOTICE 和 LICENSE。
"BERT 优化器和学习率调度实现。"


import math

import torch

from torch.optim import Optimizer

from torch.optim.optimizer import required

from torch.nn.utils import clip_grad_norm_

import logging

import abc

import sys


logger = logging.getLogger(__name__)


if sys.version_info >= (3, 4):

    ABC = abc.ABC

else:

    ABC = abc.ABCMeta('ABC', (), {})


class _LRSchedule(ABC):

    "学习率调度接口，根据训练进度返回倍率。"

    warn_t_total = False        # 对不应超出总步数的学习率调度启用边界检查。

    def __init__(self, warmup=0.002, t_total=-1, **kw):

        "初始化对象，配置参数包括 warmup, t_total。"

        super(_LRSchedule, self).__init__(**kw)

        if t_total < 0:

            logger.warning("t_total value of {} results in schedule not being applied".format(t_total))

        if not 0.0 <= warmup < 1.0 and not warmup == -1:

            raise ValueError("Invalid warmup: {} - should be in [0.0, 1.0[ or -1".format(warmup))

        warmup = max(warmup, 0.)

        self.warmup, self.t_total = float(warmup), float(t_total)

        self.warned_for_t_total_at_progress = -1


    def get_lr(self, step, nowarn=False):

        "计算当前训练步数对应的学习率。"

        if self.t_total < 0:

            return 1.

        progress = float(step) / self.t_total

        ret = self.get_lr_(progress)

        # 线性调度超出预设总步数时发出提示。

        if not nowarn and self.warn_t_total and progress > 1. and progress > self.warned_for_t_total_at_progress:

            logger.warning(

                "Training beyond specified 't_total'. Learning rate multiplier set to {}. Please set 't_total' of {} correctly."

                    .format(ret, self.__class__.__name__))

            self.warned_for_t_total_at_progress = progress

        # 边界提示结束。

        return ret


    @abc.abstractmethod

    def get_lr_(self, progress):

        "根据归一化训练进度返回学习率倍率。"

        return 1.


class ConstantLR(_LRSchedule):

    def get_lr_(self, progress):

        return 1.


class WarmupCosineSchedule(_LRSchedule):

    "先线性预热，再按余弦曲线降低学习率。"

    warn_t_total = True

    def __init__(self, warmup=0.002, t_total=-1, cycles=.5, **kw):

        "初始化对象，配置参数包括 warmup, t_total, cycles。"

        super(WarmupCosineSchedule, self).__init__(warmup=warmup, t_total=t_total, **kw)

        self.cycles = cycles


    def get_lr_(self, progress):

        if progress < self.warmup:

            return progress / self.warmup

        else:

            progress = (progress - self.warmup) / (1 - self.warmup)   # 计算预热结束后的进度。

            return 0.5 * (1. + math.cos(math.pi * self.cycles * 2 * progress))


class WarmupCosineWithHardRestartsSchedule(WarmupCosineSchedule):

    "先预热，再使用周期性重启的余弦学习率。"

    def __init__(self, warmup=0.002, t_total=-1, cycles=1., **kw):

        super(WarmupCosineWithHardRestartsSchedule, self).__init__(warmup=warmup, t_total=t_total, cycles=cycles, **kw)

        assert(cycles >= 1.)


    def get_lr_(self, progress):

        if progress < self.warmup:

            return progress / self.warmup

        else:

            progress = (progress - self.warmup) / (1 - self.warmup)     # 计算预热结束后的进度。

            ret = 0.5 * (1. + math.cos(math.pi * ((self.cycles * progress) % 1)))

            return ret


class WarmupCosineWithWarmupRestartsSchedule(WarmupCosineWithHardRestartsSchedule):

    "在余弦学习率的重启周期中重新实施预热。"

    def __init__(self, warmup=0.002, t_total=-1, cycles=1., **kw):

        assert(warmup * cycles < 1.)

        warmup = warmup * cycles if warmup >= 0 else warmup

        super(WarmupCosineWithWarmupRestartsSchedule, self).__init__(warmup=warmup, t_total=t_total, cycles=cycles, **kw)


    def get_lr_(self, progress):

        progress = progress * self.cycles % 1.

        if progress < self.warmup:

            return progress / self.warmup

        else:

            progress = (progress - self.warmup) / (1 - self.warmup)     # 计算预热结束后的进度。

            ret = 0.5 * (1. + math.cos(math.pi * progress))

            return ret


class WarmupConstantSchedule(_LRSchedule):

    "线性预热后保持恒定学习率。"

    def get_lr_(self, progress):

        if progress < self.warmup:

            return progress / self.warmup

        return 1.


class WarmupLinearSchedule(_LRSchedule):

    "线性预热后将学习率线性衰减。"

    warn_t_total = True

    def get_lr_(self, progress):

        if progress < self.warmup:

            return progress / self.warmup

        return max((progress - 1.) / (self.warmup - 1.), 0.)


SCHEDULES = {

    None:       ConstantLR,

    "none":     ConstantLR,

    "warmup_cosine": WarmupCosineSchedule,

    "warmup_constant": WarmupConstantSchedule,

    "warmup_linear": WarmupLinearSchedule

}


class BertAdam(Optimizer):

    "BERT 使用的 Adam 优化器，支持学习率预热、独立权重衰减和梯度裁剪。"

    def __init__(self, params, lr=required, warmup=-1, t_total=-1, schedule='warmup_linear',

                 b1=0.9, b2=0.999, e=1e-6, weight_decay=0.01, max_grad_norm=1.0, **kwargs):

        if lr is not required and lr < 0.0:

            raise ValueError("Invalid learning rate: {} - should be >= 0.0".format(lr))

        if not isinstance(schedule, _LRSchedule) and schedule not in SCHEDULES:

            raise ValueError("Invalid schedule parameter: {}".format(schedule))

        if not 0.0 <= b1 < 1.0:

            raise ValueError("Invalid b1 parameter: {} - should be in [0.0, 1.0[".format(b1))

        if not 0.0 <= b2 < 1.0:

            raise ValueError("Invalid b2 parameter: {} - should be in [0.0, 1.0[".format(b2))

        if not e >= 0.0:

            raise ValueError("Invalid epsilon value: {} - should be >= 0.0".format(e))

        # 初始化学习率调度对象。

        if not isinstance(schedule, _LRSchedule):

            schedule_type = SCHEDULES[schedule]

            schedule = schedule_type(warmup=warmup, t_total=t_total)

        else:

            if warmup != -1 or t_total != -1:

                logger.warning("warmup and t_total on the optimizer are ineffective when _LRSchedule object is provided as schedule. "

                               "Please specify custom warmup and t_total in _LRSchedule object.")

        defaults = dict(lr=lr, schedule=schedule,

                        b1=b1, b2=b2, e=e, weight_decay=weight_decay,

                        max_grad_norm=max_grad_norm)

        super(BertAdam, self).__init__(params, defaults)


    def get_lr(self):

        lr = []

        for group in self.param_groups:

            for p in group['params']:

                state = self.state[p]

                if len(state) == 0:

                    return [0]

                lr_scheduled = group['lr']

                lr_scheduled *= group['schedule'].get_lr(state['step'])

                lr.append(lr_scheduled)

        return lr


    def step(self, closure=None):

        "根据当前梯度更新参数，并执行可选的闭包。"

        loss = None

        if closure is not None:

            loss = closure()


        for group in self.param_groups:

            for p in group['params']:

                if p.grad is None:

                    continue

                grad = p.grad.data

                if grad.is_sparse:

                    raise RuntimeError('Adam does not support sparse gradients, please consider SparseAdam instead')


                state = self.state[p]


                # 初始化优化器状态。

                if len(state) == 0:

                    state['step'] = 0

                    # 更新梯度的一阶指数移动平均。

                    state['next_m'] = torch.zeros_like(p.data)

                    # 更新梯度平方的二阶指数移动平均。

                    state['next_v'] = torch.zeros_like(p.data)


                next_m, next_v = state['next_m'], state['next_v']

                beta1, beta2 = group['b1'], group['b2']


                # 对梯度范数进行裁剪。

                if group['max_grad_norm'] > 0:

                    clip_grad_norm_(p, group['max_grad_norm'])


                # 更新一阶、二阶动量的衰减系数。

                # 原地更新移动平均状态。


                next_m.mul_(beta1).add_(grad, alpha=1 - beta1)

                next_v.mul_(beta2).addcmul_(grad, grad, value=1 - beta2)

                update = next_m / (next_v.sqrt() + group['e'])


                # Adam 中的权重衰减不能简单等同于，

                # 将参数平方和加到损失中的 L2 正则；

                # 后者会与动量估计相互影响。


                # 直接对权重实施独立衰减，

                # 使其不改变一阶、二阶动量状态；

                # 在普通无动量梯度下降中，这与 L2 正则等价。

                if group['weight_decay'] > 0.0:

                    update += group['weight_decay'] * p.data


                lr_scheduled = group['lr']

                lr_scheduled *= group['schedule'].get_lr(state['step'])


                update_with_lr = lr_scheduled * update

                p.data.add_(-update_with_lr)


                state['step'] += 1


                # 不额外实施动量偏差修正。


        return loss
