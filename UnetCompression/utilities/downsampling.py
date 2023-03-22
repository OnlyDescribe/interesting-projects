import torch
from torch.nn.functional import avg_pool2d, avg_pool3d
import numpy as np
from skimage.transform import resize

def convert_seg_image_to_one_hot_encoding_batched(image, classes=None):
    '''
    same as convert_seg_image_to_one_hot_encoding, but expects image to be (b, x, y, z) or (b, x, y)
    '''
    if classes is None:
        classes = np.unique(image)
    output_shape = [image.shape[0]] + [len(classes)] + list(image.shape[1:])
    out_image = np.zeros(output_shape, dtype=image.dtype)
    for b in range(image.shape[0]):
        for i, c in enumerate(classes):
            out_image[b, i][image[b] == c] = 1
    return out_image


def resize_segmentation(segmentation, new_shape, order=3, cval=0):
    '''
    Resizes a segmentation map. Supports all orders (see skimage documentation). Will transform segmentation map to one
    hot encoding which is resized and transformed back to a segmentation map.
    This prevents interpolation artifacts ([0, 0, 2] -> [0, 1, 2])
    :param segmentation:
    :param new_shape:
    :param order:
    :return:
    '''
    tpe = segmentation.dtype
    unique_labels = np.unique(segmentation)
    assert len(segmentation.shape) == len(new_shape), "new shape must have same dimensionality as segmentation"
    if order == 0:
        return resize(segmentation.astype(float), new_shape, order, mode="constant", cval=cval, clip=True, anti_aliasing=False).astype(tpe)
    else:
        reshaped = np.zeros(new_shape, dtype=segmentation.dtype)

        for i, c in enumerate(unique_labels):
            mask = segmentation == c
            reshaped_multihot = resize(mask.astype(float), new_shape, order, mode="edge", clip=True, anti_aliasing=False)
            reshaped[reshaped_multihot >= 0.5] = c
        return reshaped


def downsample_seg_for_ds_transform(seg, ds_scales=((1, 1, 1), (0.5, 0.5, 0.5), (0.25, 0.25, 0.25)), order=0, cval=0, axes=None):
    # (channel,H,W,S)
    if len(seg.shape)==4:
        if axes is None:
            # axes = list(range(2, len(seg.shape)))
            axes = list(range(1, len(seg.shape)))
        output = []
        for s in ds_scales:
            if all([i == 1 for i in s]):
                output.append(seg)
            else:
                new_shape = np.array(seg.shape).astype(float)
                for i, a in enumerate(axes):
                    new_shape[a] *= s[i]
                new_shape = np.round(new_shape).astype(int)
                out_seg = np.zeros(new_shape, dtype=seg.dtype)
                # for b in range(seg.shape[0]):
                for c in range(seg.shape[0]):
                    # out_seg[b, c] = resize_segmentation(seg[b, c], new_shape[2:], order, cval)
                    out_seg[c] = resize_segmentation(seg[c], new_shape[1:], order, cval)
                output.append(out_seg)
    elif len(seg.shape)==5:
        if axes is None:
            axes = list(range(2, len(seg.shape)))
            output = []
        for s in ds_scales:
            if all([i == 1 for i in s]):
                output.append(seg)
            else:
                new_shape = np.array(seg.shape).astype(float)
                for i, a in enumerate(axes):
                    new_shape[a] *= s[i]
                new_shape = np.round(new_shape).astype(int)
                out_seg = np.zeros(new_shape, dtype=seg.dtype)
                for b in range(seg.shape[0]):
                    for c in range(seg.shape[0]):
                        out_seg[b, c] = resize_segmentation(seg[b, c], new_shape[2:], order, cval)
                output.append(out_seg)
    return output



def downsample_seg_for_ds_transform_pool(seg, ds_scales=((1, 1, 1), (0.5, 0.5, 0.5), (0.25, 0.25, 0.25)), classes=None):
    output = []
    one_hot = torch.from_numpy(convert_seg_image_to_one_hot_encoding_batched(seg, classes)) # b, c,

    for s in ds_scales:
        if all([i == 1 for i in s]):
            output.append(torch.from_numpy(seg))
        else:
            kernel_size = tuple(int(1 / i) for i in s)
            stride = kernel_size
            pad = tuple((i-1) // 2 for i in kernel_size)

            if len(s) == 2:
                pool_op = avg_pool2d
            elif len(s) == 3:
                pool_op = avg_pool3d
            else:
                raise RuntimeError()

            pooled = pool_op(one_hot, kernel_size, stride, pad, count_include_pad=False, ceil_mode=False)

            output.append(pooled)
    return output