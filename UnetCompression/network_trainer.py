import torch
from torch import nn
import numpy as np
from network.generic_UNet_modified import Generic_UNet, ConvDropoutNormNonlin

from network.initialization import InitWeights_He
from loss_functions.dice_loss import DC_and_CE_loss, MultipleOutputLoss2
from utilities.nd_softmax import softmax_helper


class NetworkTrainer(object):
    def __init__(self,num_classes=3, using_UNET_3D=True, epoch=0, deep_supervision=True):
        self.was_initialized = False

        # for network
        self.network = None
        self.num_classes = num_classes
        self.using_UNET_3D = using_UNET_3D
        self.device = torch.device("cuda" if torch.cuda.is_available()
                                   else "cpu")
        self.deep_supervision = deep_supervision
        self.conv_op = nn.Conv3d  # default: 3D Unet
        self.dropout_op = nn.Dropout3d
        self.norm_op = nn.InstanceNorm3d
        self.net_conv_kernel_sizes = [[1, 3, 3], [3, 3, 3], [
            3, 3, 3], [3, 3, 3], [3, 3, 3], [3, 3, 3]]
        self.net_num_pool_op_kernel_sizes = [[1, 2, 2], [
            2, 2, 2], [2, 2, 2], [2, 2, 2], [1, 2, 2]]

        # for training
        self.optimizer = None
        self.loss_function = None
        # self.initial_lr = self.lr_scheduler = 1e-2
        self.initial_lr = self.lr_scheduler = 2e-3

        self.weight_decay = 3e-5

        self.epoch = epoch
        # self.max_epochs = 600
        self.max_epochs = 300

    def initialize(self):
        if not self.was_initialized:
            self.initialize_network()
            self.initialize_optimizer_and_scheduler()

            self.was_initialized = True
        else:
            print('The network has been initialized!')

    def initialize_network(self):
        if(self.using_UNET_3D):
            self.conv_op = nn.Conv3d
            self.dropout_op = nn.Dropout3d
            self.norm_op = nn.InstanceNorm3d
            norm_op_kwargs = {'eps': 1e-5, 'affine': True}
            # self.norm_op = nn.GroupNorm
            # norm_op_kwargs = {'num_groups': 32, 'eps': 1e-5, 'affine': True}
            self.net_conv_kernel_sizes = [[1, 3, 3], [3, 3, 3], [
                3, 3, 3], [3, 3, 3], [3, 3, 3], [3, 3, 3]]
            self.net_num_pool_op_kernel_sizes = [[1, 2, 2], [
                2, 2, 2], [2, 2, 2], [2, 2, 2], [1, 2, 2]]
            
        else:
            self.conv_op = nn.Conv2d
            self.dropout_op = nn.Dropout2d
            self.norm_op = nn.InstanceNorm2d
            norm_op_kwargs = {'eps': 1e-5, 'affine': True}
            self.net_conv_kernel_sizes = [[3, 3], [3, 3], [
                3, 3], [3, 3], [3, 3], [3, 3], [3, 3], [3, 3]]
            self.net_num_pool_op_kernel_sizes = [
                [2, 2], [2, 2], [2, 2], [2, 2], [2, 2], [2, 2], [2, 2]]

        self.network = Generic_UNet(
            input_channels=1,
            base_num_features=32,
            num_classes=self.num_classes,
            num_pool=len(self.net_num_pool_op_kernel_sizes),

            num_conv_per_stage=2,
            feat_map_mul_on_downscale=2,

            conv_op=self.conv_op,
            norm_op=self.norm_op,
            norm_op_kwargs=norm_op_kwargs,
            dropout_op=self.dropout_op,
            dropout_op_kwargs={'p': 0, 'inplace': True},
            nonlin=nn.LeakyReLU,
            nonlin_kwargs={'negative_slope': 1e-2, 'inplace': True},

            deep_supervision=self.deep_supervision,

            dropout_in_localization=False,
            final_nonlin=lambda x: x,
            # final_nonlin=softmax_helper,
            weightInitializer=InitWeights_He(1e-2),

            pool_op_kernel_sizes=self.net_num_pool_op_kernel_sizes,
            conv_kernel_sizes=self.net_conv_kernel_sizes,

            upscale_logits=False,
            convolutional_pooling=True,
            convolutional_upsampling=True,

            # convolutional_pooling=False,
            # convolutional_upsampling=False,

            max_num_features=None, basic_block=ConvDropoutNormNonlin, seg_output_use_bias=False
        )
        self.network.set_device(self.device)

    def initialize_optimizer_and_scheduler(self):
        self.optimizer = torch.optim.SGD(self.network.parameters(
        ), self.initial_lr, weight_decay=self.weight_decay, momentum=0.99, nesterov=True)
        self.loss_function = DC_and_CE_loss(
            {'batch_dice': True, 'smooth': 1e-5, 'do_bg': False}, {})
        if self.deep_supervision == True:
            ################# Here we wrap the loss for deep supervision ############
            # we need to know the number of outputs of the network
            net_numpool = len(self.net_num_pool_op_kernel_sizes)

            # we give each output a weight which decreases exponentially (division by 2) as the resolution decreases
            # this gives higher resolution outputs more weight in the loss
            weights = np.array([1 / (2 ** i) for i in range(net_numpool)])

            # we don't use the lowest 2 outputs. Normalize weights so that they sum to 1
            mask = np.array([True] + [True if i < net_numpool -
                                      1 else False for i in range(1, net_numpool)])
            weights[~mask] = 0
            weights = weights / weights.sum()
            self.ds_loss_weights = weights
            # now wrap the loss
            self.loss_function = MultipleOutputLoss2(self.loss_function, self.ds_loss_weights)

    def poly_lr(self, epoch, exponent=0.9):
        return self.initial_lr * (1 - epoch / self.max_epochs)**exponent

    def update_lr(self, epoch=None):
        # (maybe_update_lr is called in on_epoch_end which is called before epoch is incremented.
        # herefore we need to do +1 here)
        if epoch is None:
            ep = self.epoch + 1
        else:
            ep = epoch

        # lr_scheduler_eps = 1e-3
        # lr_scheduler_patience = 30
        # lr_scheduler = lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.2,
        #                                                            patience=lr_scheduler_patience,
        #                                                            verbose=True, threshold=lr_scheduler_eps,
        #                                                            threshold_mode="abs")

        self.optimizer.param_groups[0]['lr'] = self.poly_lr(
            epoch=ep, exponent=0.9)
        print('learning rate = %.7f' % np.round(
            self.optimizer.param_groups[0]['lr'], decimals=6))

    # def on_epoch_end(self):

    #     self.update_lr()

    #     continue_training = self.epoch < self.max_epochs
    #     # it can rarely happen that the momentum of UNetTrainer is too high for some dataset. If at epoch 100 the
    #     # estimated validation Dice is still 0 then we reduce the momentum from 0.99 to 0.95
    #     return continue_training

    def predict(self, image, do_mirroring=False):
        self.network.inference_apply_nonlin = softmax_helper
        self.network.training = False
        # set deep_supervision=False
        self.do_ds = False
        predict = self.network.predict_3D(
            image[0],
            do_mirroring=do_mirroring, mirror_axes=(0, 1, 2),
            use_sliding_window=True, step_size=0.5,
            patch_size=(40, 224, 224), regions_class_order=(0, 1, 2),
            use_gaussian=True, pad_border_mode='constant',
            pad_kwargs={'constant_values': 0}, all_in_gpu=False, verbose=True,
            mixed_precision=True)
        return predict

    def load_state_dict(self, checkpoint):
        self.network.load_state_dict(checkpoint)
        print("model has been loaded")


# curr_state_dict_keys = list(self.network.state_dict().keys())
