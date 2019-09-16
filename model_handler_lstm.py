# LSTM model following the code of https://github.com/Louismac/MAGNet

import numpy as np
import tensorflow as tf
import tflearn
from tflearn.layers.recurrent import bidirectional_rnn, BasicLSTMCell, GRUCell
from tflearn.layers.core import dropout
from tflearn.layers.conv import conv_2d, max_pool_2d
from utils.audio_dataset_generator import AudioDatasetGenerator
import sys
import pywt

def conv_net(net, filters, kernels, non_linearity):
    """
    A quick function to build a conv net.
    At the end it reshapes the network to be 3d to work with recurrent units.
    """
    assert len(filters) == len(kernels)

    for i in range(len(filters)):
        net = conv_2d(net, filters[i], kernels[i], activation=non_linearity)
        net = max_pool_2d(net, 2)

    dim1 = net.get_shape().as_list()[1]
    dim2 = net.get_shape().as_list()[2]
    dim3 = net.get_shape().as_list()[3]
    return tf.reshape(net, [-1, dim1 * dim3, dim2])


def recurrent_net(net, rec_type, rec_size, return_sequence):
    """
    A quick if else block to build a recurrent layer, based on the type specified
    by the user.
    """
    if rec_type == 'lstm':
        net = tflearn.layers.recurrent.lstm(net, rec_size, return_seq=return_sequence)
    elif rec_type == 'gru':
        net = tflearn.layers.recurrent.gru(net, rec_size, return_seq=return_sequence)
    elif rec_type == 'bi_lstm':
        net = bidirectional_rnn(net,
                                BasicLSTMCell(rec_size),
                                BasicLSTMCell(rec_size),
                                return_seq=return_sequence)
    elif rec_type == 'bi_gru':
        net = bidirectional_rnn(net,
                                GRUCell(rec_size),
                                GRUCell(rec_size),
                                return_seq=return_sequence)
    else:
        raise ValueError('Incorrect rnn type passed. Try lstm, gru, bi_lstm or bi_gru.')
    return net


class ModelHandlerLSTM(object):
    """
    Will handle everything around the LSTM model.
    """

    def __init__(self):
        self.model = None

        # General Network
        self.learning_rate = 1e-3
        self.amount_epochs = 300
        self.batch_size = 64
        self.keep_prob = 0.2
        self.loss_type = "mean_square"
        self.activation = 'tanh'
        self.optimiser = 'adam'
        self.fully_connected_dim = 1024

        # Recurrent Neural Network
        self.rnn_type = "lstm"
        self.number_rnn_layers = 3
        self.rnn_number_units = 128

        # Convolutional Neural Network
        self.use_cnn = False
        self.number_filters = [32]
        self.filter_sizes = [3]

        # auto init?
        #self.model = create_model()

    def create_model(self, sequence_length = 40):
        self.sequence_length = sequence_length
        #self.sequence_length = 45
        # x data (22983, 40, 1025)
        # y data (22983, 1025)
        self.input_shapes = (None, self.sequence_length, 1025)
        self.output_shapes = (None, 1025)

        # Input
        if self.use_cnn:
            assert False
            #net = tflearn.input_data([None, self.input_shapes[1], self.input_shapes[2], self.input_shapes[3]
            #                          ], name="input_data0")
            #net = conv_net(net, self.number_filters, self.filter_sizes, self.activation)
        else:
            net = tflearn.input_data([None, self.input_shapes[1], self.input_shapes[2]
                                      ], name="input_data0")

            # Batch Norm
        net = tflearn.batch_normalization(net, name="batch_norm0")

        # Recurrent
        for layer in range(self.number_rnn_layers):
            return_sequence = False if layer == (self.number_rnn_layers - 1) else True
            net = recurrent_net(net, self.rnn_type, self.rnn_number_units, return_sequence)
            net = dropout(net, 1 - self.keep_prob) if self.keep_prob < 1.0 else net

            # Dense + MLP Out
        net = tflearn.fully_connected(net, self.output_shapes[1],
                                      activation=self.activation,
                                      regularizer='L2',
                                      weight_decay=0.001)

        net = tflearn.fully_connected(net, self.output_shapes[1],
                                      activation='linear')

        net = tflearn.regression(net, optimizer=self.optimiser, learning_rate=self.learning_rate,
                                 loss=self.loss_type)

        model = tflearn.DNN(net, tensorboard_verbose=1)

        self.model = model