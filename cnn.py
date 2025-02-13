import tensorflow as tf
import numpy as np

tf.compat.v1.disable_eager_execution()


class Cnn(object):

    def __init__(self, conv_layers, fc_layers, filters, learning_rate):
        self.__conv_layers = conv_layers
        self.__fc_layers = fc_layers
        self.__filters = filters
        self.__lr = learning_rate
        self.__keep_prob = tf.compat.v1.placeholder(tf.float32, name='keep_prob')

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

    @property
    def keep_prob(self):
        return self.__keep_prob

    def __variable_summaries(self, var):
        """
        Attach a lot of summaries to a Tensor (for TensorBoard visualization)
        :param var
        :return:
        """
        mean = tf.reduce_mean(var)
        tf.compat.v1.summary.scalar('mean_value', mean)
        with tf.compat.v1.name_scope('stddev'):
            stddev = tf.sqrt(tf.reduce_mean(tf.square(var - mean)))
        tf.compat.v1.summary.scalar('stddev_value', stddev)
        tf.compat.v1.summary.scalar('max_value', tf.reduce_max(var))
        tf.compat.v1.summary.scalar('min_value', tf.reduce_min(var))
        tf.compat.v1.summary.histogram('histogram', var)

    def initialize(self, n_w0, n_c0, n_y):
        """
        initialize the w, X, Y and forward options
        :param n_w0: width of the image data
        :param n_c0: depth of the image data
        :param n_y: number of the labels
        :return:
        """
        with tf.compat.v1.name_scope('input'):
            self.__x = tf.compat.v1.placeholder(tf.float32, (None, n_w0, n_c0), 'data_x')
            self.__y = tf.compat.v1.placeholder(tf.float32, (None, n_y), 'data_y')

        f = self.__filters
        convs = self.__conv_layers
        fcs = self.__fc_layers
        a_pre = self.__x

        # convolutional layers
        conv_index = 1
        shape = n_c0
        for i in range(len(convs)):
            if convs[i] == 0:
                with tf.compat.v1.name_scope('conv' + str(conv_index - 1) + '/'):
                    a = tf.nn.pool(a_pre, window_shape=[f[i][0]], padding=f[i][2], pooling_type="MAX")
                    a_pre = a
            elif convs[i] == -1:
                with tf.compat.v1.name_scope('conv' + str(conv_index - 1) + '/'):
                    a = tf.nn.dropout(a_pre, rate=1 - (self.__keep_prob))
                a_pre = a
            else:
                a = self.__conv_layer(a_pre, f[i][0], shape, convs[i], 'conv' + str(conv_index), stride=f[i][1],
                                      padding=f[i][2])
                shape = convs[i]
                a_pre = a
                conv_index += 1
        # flatten
        with tf.compat.v1.name_scope('flatten'):
            a_pre = tf.reshape(a, [-1, int(a_pre.shape[1]) * int(a_pre.shape[2])])

        # full connected forward
        i = 0
        for i in range(len(fcs)):
            a = self.__fc_layer(a_pre, int(a_pre.shape[1]), fcs[i], 'fc' + str(i + 1))
            a_pre = a
        a = self.__fc_layer(a_pre, int(a_pre.shape[1]), 1, 'fc' + str(i + 1), act=tf.identity)
        self.__a = a

    def __fc_layer(self, input_tensor, input_dim, output_dim, layer_name, act=tf.nn.relu):
        with tf.compat.v1.name_scope(layer_name):
            with tf.compat.v1.name_scope('weights'):
                initial = tf.random.truncated_normal([input_dim, output_dim], stddev=0.1)
                weights = tf.Variable(initial)
                self.__variable_summaries(weights)
            with tf.compat.v1.name_scope('biases'):
                initial = tf.constant(0.1, shape=[output_dim], dtype=float)
                biases = tf.Variable(initial)
                self.__variable_summaries(biases)
            with tf.compat.v1.name_scope('Wx_plus_b'):
                preactivate = tf.matmul(input_tensor, weights) + biases
                tf.compat.v1.summary.histogram('pre_activations', preactivate)
            activations = act(preactivate, name='activation')
            tf.compat.v1.summary.histogram('activations', activations)
            return activations

    def __conv_layer(self, input_tensor, kernel_size, input_dim, output_dim, layer_name, stride, padding,
                     act=tf.nn.relu):
        with tf.compat.v1.name_scope(layer_name):
            with tf.compat.v1.name_scope('weights'):
                initial = tf.random.truncated_normal([kernel_size, input_dim, output_dim], stddev=0.1)
                weights = tf.Variable(initial)
                self.__variable_summaries(weights)
            with tf.compat.v1.name_scope('biases'):
                initial = tf.constant(0.1, shape=[output_dim], dtype=float)
                biases = tf.Variable(initial)
                self.__variable_summaries(biases)
            with tf.compat.v1.name_scope('W_conv_x_plus_b'):
                preactivate = tf.nn.conv1d(input=input_tensor, filters=weights, stride=stride, padding=padding) + biases
            tf.compat.v1.summary.histogram('pre_activations', preactivate)
            activations = act(preactivate, name='activation')
            tf.compat.v1.summary.histogram('activations', activations)
            return activations

    def cost(self):
        with tf.compat.v1.name_scope("loss"):
            cost = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=self.__a, labels=self.__y))
            tf.compat.v1.summary.scalar("loss", cost)
        return cost

    def get_optimizer(self, cost):
        with tf.compat.v1.name_scope("train"):
            adam = tf.compat.v1.train.AdamOptimizer(self.__lr).minimize(cost)
        return adam

    def predict(self):
        with tf.compat.v1.name_scope("accuracy"):
            pre = tf.cast(tf.greater(self.__a, 0.5), dtype=float, name='predict')
            accuracy = tf.reduce_mean(tf.cast(tf.equal(pre, self.__y), "float"))
            tf.compat.v1.summary.scalar("accuracy", accuracy)
        return pre, accuracy
