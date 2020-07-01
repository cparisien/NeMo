# =============================================================================
# Copyright 2020 NVIDIA. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================

from collections import OrderedDict

import torch

from nemo.core.classes import NeuralModule, typecheck
from nemo.core.neural_types import LabelsType, LogitsType, LossType, MaskType, NeuralType
from nemo.utils.decorators import experimental


@experimental
class CrossEntropyLoss(NeuralModule):
    """
    CrossEntropyLoss
    Args:
        logits_ndim (int): number of dimensions (or rank) of the logits tensor
        weight (list): list of rescaling weight given to each class
        reduction (str): type of the reduction over the batch
    """

    @property
    # @add_port_docs()
    def input_ports(self):
        """Returns definitions of module input ports.
        """
        return OrderedDict(
            {
                "logits": NeuralType(['B'] + ['ANY'] * (self._logits_dim - 1), LogitsType()),
                "labels": NeuralType(['B'] + ['ANY'] * (self._logits_dim - 2), LabelsType()),
                "loss_mask": NeuralType(['B'] + ['ANY'] * (self._logits_dim - 2), MaskType(), optional=True),
            }
        )

    @property
    # @add_port_docs()
    def output_ports(self):
        """Returns definitions of module output ports.
        loss:
            NeuralType(None)
        """
        return OrderedDict({"loss": NeuralType(elements_type=LossType())})

    def __init__(self, logits_ndim=2, weight=None, reduction='mean'):
        super().__init__()

        if weight:
            weight = torch.FloatTensor(weight).to(self._device)
        self._criterion = torch.nn.CrossEntropyLoss(weight=weight, reduction=reduction)
        self._logits_dim = logits_ndim

    @typecheck()
    def forward(self, logits, labels, loss_mask=None):
        """
        Args:
            logits (float): output of the classifier
            labels (long): ground truth labels
            loss_mask (bool/float/int): tensor to specify the masking
        """
        logits_flatten = torch.flatten(logits, start_dim=0, end_dim=-2)
        labels_flatten = torch.flatten(labels, start_dim=0, end_dim=-1)

        if loss_mask is not None:
            if loss_mask.dtype is not torch.bool:
                loss_mask = loss_mask > 0.5
            loss_mask_flatten = torch.flatten(loss_mask, start_dim=0, end_dim=-1)
            logits_flatten = logits_flatten[loss_mask_flatten]
            labels_flatten = labels_flatten[loss_mask_flatten]

        if len(labels_flatten) == 0:
            return self._criterion(logits, torch.argmax(logits, dim=-1))

        loss = self._criterion(logits_flatten, labels_flatten)
        return loss

    @classmethod
    def save_to(self, save_path: str):
        pass

    @classmethod
    def restore_from(cls, restore_path: str):
        pass