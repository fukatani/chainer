from __future__ import print_function

import six

from chainer import cuda
from chainer.trainer import extension
from chainer import variable


class Evaluator(extension.Extension):

    """Trainer extension for evaluation on the validation set.

    TODO(beam2d): document it.

    """
    default_trigger = 1, 'epoch'
    default_name = 'validation'
    result_action = 'write'

    def __init__(self, dataset, target, lossfun=None, batchsize=1):
        self._dataset = dataset
        self._target = target
        self._lossfun = lossfun

    def __call__(self, epoch, t, trainer, **kwargs):
        lossfun = self._target if self._lossfun is None else self._lossfun

        accum = None
        it = dataset.get_batch_iterator(batchsize, repeat=False)
        for inputs in it:
            n = len(inputs[0])
            # TODO(beam2d): better device handling
            if trainer._device >= 0:
                with cuda.get_device(trainer._device):
                    inputs = tuple(cuda.to_gpu(x) for x in inputs)
            in_vars = tuple(variable.Variable(a) for a in inputs)
            loss = lossfun(*in_vars)
            result = {'loss': loss.data * n}
            for key, value in self._target.__dict__:
                if isinstance(value, variable.Variable):
                    result[key] = value.data * n
            if accum is None:
                accum = result
            else:
                for key in result:
                    accum[key] += result[key]

        N = len(self._dataset)
        return {key: value / N for key, value in six.iteritems(accum)}
