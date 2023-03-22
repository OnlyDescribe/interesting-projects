from monai.transforms.croppad.array import (
    CropForeground,
)
import numpy as np
from typing import Any, Callable, Dict, Hashable, List, Mapping, Optional, Sequence, Tuple, Union
from monai.config import IndexSelection, KeysCollection

from monai.transforms.inverse import InvertibleTransform
from monai.transforms.transform import MapTransform, Randomizable
from utilities.downsampling import downsample_seg_for_ds_transform
from monai.transforms.utility.array import (
    ToNumpy,
    ToTensor,
)
from copy import deepcopy

class DownsampleSegForDSTransform(MapTransform):
    def __init__(self, keys: KeysCollection,deep_supervision_scales,allow_missing_keys: bool=False) -> None:
        super().__init__(keys, allow_missing_keys=allow_missing_keys)
        self.deep_supervision_scales = deep_supervision_scales

    def __call__(self, data):
        d = dict(data)
        for key in self.key_iterator(d):
            # dim 0 :channel
            d[key] = downsample_seg_for_ds_transform(d[key],ds_scales=self.deep_supervision_scales)
        return d


class MyCrop(MapTransform, InvertibleTransform):
    def __init__(
        self,
        keys: KeysCollection,
        source_key: str,
        select_fn: Callable = lambda x: x > 0,
        spatial_size: Union[Sequence[int], int]=(224,224,40),
        channel_indices: Optional[IndexSelection] = None,
        margin: int = 0,
        k_divisible: Union[Sequence[int], int] = 1,
        start_coord_key: str = "foreground_start_coord",
        end_coord_key: str = "foreground_end_coord",
        allow_missing_keys: bool = False,
    ) -> None:

        super().__init__(keys, allow_missing_keys)
        self.source_key = source_key
        self.start_coord_key = start_coord_key
        self.end_coord_key = end_coord_key
        self.spatial_size: Union[Tuple[int, ...], Sequence[int], int] = spatial_size
        self.cropper = CropForeground(
            select_fn=select_fn,
            channel_indices=channel_indices,
            margin=margin,
            k_divisible=k_divisible,
        )

    def __call__(self, data: Mapping[Hashable, np.ndarray]) -> Dict[Hashable, np.ndarray]:
        d = dict(data)
        box_start, box_end = self.cropper.compute_bounding_box(img=d[self.source_key])
        for coord in range(3):
            if (self.spatial_size[coord] > (box_end - box_start)[coord]):
                shift = (self.spatial_size[coord] - (box_end - box_start)[coord])//2 + 1 
                box_start[coord] -= shift
                box_end[coord] += shift
        # print(shift,box_start, box_end)

        d[self.start_coord_key] = box_start
        d[self.end_coord_key] = box_end
        for key in self.key_iterator(d):
            self.push_transform(d, key, extra_info={"box_start": box_start, "box_end": box_end})
            d[key] = self.cropper.crop_pad(d[key], box_start, box_end)
        return d

class MyToTensord(MapTransform, InvertibleTransform):
    """
    Dictionary-based wrapper of :py:class:`monai.transforms.ToTensor`.
    """

    def __init__(self, keys: KeysCollection, allow_missing_keys: bool = False) -> None:
        """
        Args:
            keys: keys of the corresponding items to be transformed.
                See also: :py:class:`monai.transforms.compose.MapTransform`
            allow_missing_keys: don't raise exception if key is missing.
        """
        super().__init__(keys, allow_missing_keys)
        self.converter = ToTensor()

    def __call__(self, data: Mapping[Hashable, Any]) -> Dict[Hashable, Any]:
        d = dict(data)
        for key in self.key_iterator(d):
            self.push_transform(d, key)
            for i in d[key]:
                i = self.converter(i)
        return d

    def inverse(self, data: Mapping[Hashable, Any]) -> Dict[Hashable, Any]:
        d = deepcopy(dict(data))
        for key in self.key_iterator(d):
            # Create inverse transform
            inverse_transform = ToNumpy()
            # Apply inverse
            for i in d[key]:
                i = inverse_transform(i)
            # Remove the applied transform
            self.pop_transform(d, key)
        return d