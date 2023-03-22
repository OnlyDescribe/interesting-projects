from copy import deepcopy
import torch
import os
import collections
from collections import OrderedDict
import tensorly as tl
import numpy as np
from tensorly.tt_tensor import validate_tt_rank,TTTensor

# SVD compress
def compress(to_compress,result = True,compress_rate = 0.7):
    U,S,V = torch.svd(to_compress)
    rank = S.shape.numel()
    k = rank
    for k in range(rank):
        if((S[:k].sum())/S.sum()>compress_rate):
            break
    U_p = U[:, :k]
    V_p = V[:, :k]
    S_p = S[:k]
    # print(rank,k)
    if result==True:
        result = torch.mm(torch.mm(U_p,torch.diag(S_p)),V_p.t())
        return result
    else:
        return U_p,V_p,S_p

preload = os.path.join('model', '3D', 'model_final_checkpoint.model')
# preload = os.path.join('results', 'best_metric_model_128.pth')
if preload is not None:
    checkpoint = torch.load(preload)['state_dict']

# Regex = re.compile(r'.*[^instnorm].weight')

def compress_conv(checkpoint,compress_rate=0.7,mode='maxmin'):
    i=0
    to_compress_checkpoint = deepcopy(checkpoint)
    for regex in checkpoint.keys():
        if regex[-6:]=="weight" and regex[-11:-6]!='norm.' and regex[0:11]!='seg_outputs':
                
                to_compress = to_compress_checkpoint[regex]
                shape = to_compress.shape
                # checkpoint[weight.group()] = compress(to_compress.view(-1,shape[0]*shape[2])).view(shape)
                if mode == 'max':
                    max = shape[0]
                    for s in shape:
                        if s > max:
                            max = s
                    U_p,V_p,S_p = compress(to_compress.view(-1,max),result=False,compress_rate=compress_rate)
                elif mode =='maxmin':
                    max = shape[0]
                    min = shape[0]
                    for s in shape:
                        if s > max:
                            max = s
                        if s < min:
                            min = s
                    U_p,V_p,S_p = compress(to_compress.view(-1,max*min),result=False,compress_rate=compress_rate)
                else:
                    U_p,V_p,S_p = compress(to_compress.view(-1,shape[0]*shape[2]),result=False,compress_rate=compress_rate)

                to_compress_checkpoint[regex] = [U_p,V_p,S_p]
                # print("finish",regex)
        # print(to_compress.shape)

    return to_compress_checkpoint

def compress_conv_(checkpoint,compress_rate=0.7, mode ='maxmin'):
    i=0
    to_compress_checkpoint = deepcopy(checkpoint)
    for regex in checkpoint.keys():
        if regex[-6:]=="weight" and regex[-11:-6]!='norm.' and regex[0:11]!='seg_outputs':
                
                to_compress = to_compress_checkpoint[regex]
                shape = to_compress.shape
                # checkpoint[weight.group()] = compress(to_compress.view(-1,shape[0]*shape[2])).view(shape)
                if mode == 'max':
                    max = shape[0]
                    for s in shape:
                        if s > max:
                            max = s
                    U_p,V_p,S_p = compress(to_compress.view(-1,max),result=False,compress_rate=compress_rate)
                elif mode =='maxmin':
                    max = shape[0]
                    min = shape[0]
                    for s in shape:
                        if s > max:
                            max = s
                        if s < min:
                            min = s
                    U_p,V_p,S_p = compress(to_compress.view(-1,max*min),result=False,compress_rate=compress_rate)
                else:
                    U_p,V_p,S_p = compress(to_compress.view(-1,shape[0]*shape[2]),result=False,compress_rate=compress_rate)

                to_compress_checkpoint[regex] = torch.mm(torch.mm(U_p,torch.diag(S_p)),V_p.t()).view(shape)
                # to_compress_checkpoint[regex] = (U_p,V_p,S_p)
                i = i + 1

        # print(to_compress.shape)

    return to_compress_checkpoint





# 计算模型大小
def cal_model_size(new_state_dict):
    size = 0
    for key,value in new_state_dict.items():
        if type(value) == collections.OrderedDict:
            for key,value in value.items():
                size += value.nelement() * value.element_size()
        elif type(value) == list:
            for i in value:
                size += i.nelement() * i.element_size()
        else:
            size += value.nelement() * value.element_size()
    return size


def convert_numpy(state_dict):
    new_state_dict = OrderedDict()
    for key,value in state_dict.items():
        if type(value) == collections.OrderedDict:
            for key,value in value.items():
                new_state_dict[key] = value.numpy()
        elif type(value) == list:
            new_state_dict[key] = []
            for i in value:
                new_state_dict[key].append(i.numpy())
        else:
            new_state_dict[key] = value.numpy()
    return new_state_dict


def my_tensor_train(input_tensor, compress_rate ,verbose=False):
    """TT decomposition via recursive SVD

        Decomposes `input_tensor` into a sequence of order-3 tensors (factors)
        -- also known as Tensor-Train decomposition [1]_.

    Parameters
    ----------
    input_tensor : tensorly.tensor
    verbose : boolean, optional
            level of verbosity

    Returns
    -------
    factors : TT factors
              order-3 tensors of the TT decomposition

    References
    ----------
    .. [1] Ivan V. Oseledets. "Tensor-train decomposition", SIAM J. Scientific Computing, 33(5):2295–2317, 2011.
    """
    rank = [1 for i in range(input_tensor.shape.__len__()+1)]
    tensor_size = input_tensor.shape
    n_dim = len(tensor_size)

    unfolding = input_tensor
    factors = [None] * n_dim

    # Getting the TT factors up to n_dim - 1
    for k in range(n_dim - 1):

        # Reshape the unfolding matrix of the remaining factors
        n_row = int(rank[k]*tensor_size[k])
        if(n_row<1):
            n_row = 1
        unfolding = tl.reshape(unfolding, (n_row, -1))

        # SVD of unfolding matrix
        (n_row, n_column) = unfolding.shape
        current_rank = min(n_row, n_column)

        U, S, V = tl.partial_svd(unfolding, current_rank)
        to_choose_rank = S.shape.numel()
        for choose_k in range(to_choose_rank):
            if((S[:choose_k].sum())/S.sum()>compress_rate):
                break
        choose_k = choose_k + 1
        U = U[:, :choose_k]
        V = V[:choose_k, :]
        S = S[:choose_k]

        rank[k+1] = choose_k

        # Get kth TT factor
        factors[k] = tl.reshape(U, (rank[k], tensor_size[k], rank[k+1]))

        if(verbose is True):
            print("TT factor " + str(k) + " computed with shape " + str(factors[k].shape))

        # Get new unfolding matrix for the remaining factors
        unfolding= tl.reshape(S, (-1, 1))*V

    # Getting the last factor
    (prev_rank, last_dim) = unfolding.shape
    factors[-1] = tl.reshape(unfolding, (prev_rank, last_dim, 1))

    if(verbose is True):
        print("TT factor " + str(n_dim-1) + " computed with shape " + str(factors[n_dim-1].shape))

    # return TTTensor(factors)
    return factors


def compress_conv_tt_(checkpoint,compress_rate=0.7):
    to_compress_checkpoint = deepcopy(checkpoint)
    for regex in checkpoint.keys():
        if regex[-6:]=="weight" and regex[-11:-6]!='norm.' and regex[0:11]!='seg_outputs':
                
                to_compress = to_compress_checkpoint[regex]
                # checkpoint[weight.group()] = compress(to_compress.view(-1,shape[0]*shape[2])).view(shape)
                tt = my_tensor_train(to_compress,compress_rate)

                to_compress_checkpoint[regex] = tl.tt_to_tensor(tt)
                # to_compress_checkpoint[regex] = (U_p,V_p,S_p)

        # print(to_compress.shape)

    return to_compress_checkpoint


def compress_conv_tt(checkpoint,compress_rate=0.7):
    to_compress_checkpoint = deepcopy(checkpoint)
    for regex in checkpoint.keys():
        if regex[-6:]=="weight" and regex[-11:-6]!='norm.' and regex[0:11]!='seg_outputs':
                
                to_compress = to_compress_checkpoint[regex]
                # checkpoint[weight.group()] = compress(to_compress.view(-1,shape[0]*shape[2])).view(shape)
                tt = my_tensor_train(to_compress,compress_rate)

                to_compress_checkpoint[regex] = tt
                # to_compress_checkpoint[regex] = (U_p,V_p,S_p)

        # print(to_compress.shape)

    return to_compress_checkpoint
