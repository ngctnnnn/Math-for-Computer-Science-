from d2l import tensorflow as d2l 
import tensorflow as tf
import numpy as np 
import matplotlib.pyplot as plt 
from IPython import display

#initialize 
batch_size = 256

x_train, x_test = d2l.load_data_fashion_mnist(batch_size)
#we load 256 input size from fashion mnist to get our dataset

input_number = 784
output_number = 10
#we construct our input dataset a 784 by 10 matrix 

w = tf.Variable(tf.random.normal(shape = (input_number, output_number), mean = 0, stddev = .01))
#our input variable w is generated by a Gaussian distribution with mean of 0
#and standard deviation of 0.01 

b = tf.Variable(tf.zeros(output_number))
#b is a 0 vector of size 10
w, b


def softmax(X):
    X_exp = tf.exp(X)
    partition = tf.reduce_sum(X_exp, 1, keepdims=True)
    return X_exp / partition
    #use above instead of below in order to avoid overflowing 
    #return tf.exp(x)/tf.reduce_sum(tf.exp(x), axis = 1, keepdims = True)

def cross_entropy(y_hat, y):
    return -tf.math.log(tf.boolean_mask(y_hat, tf.one_hot(y, depth = y_hat.shape[-1])))
    #since cross entropy is used to calculate the loss of 2 distribution (2 bool variables)


def neural_network(x):
    return softmax(tf.matmul(tf.reshape(x, shape = (-1, w.shape[0])), w) + b)
    #calculate the value of input with softmax function softmax

def accuracy(y_hat, y):
    if len(y_hat) > 1 and y_hat.shape[1] > 1:
        y_hat = tf.argmax(y_hat, axis = 1)
    #we assigned y_hat to the maximum value (argmax)
    
    cmp = tf.cast(y_hat, y.dtype) == y
    #tf.cast change the datatype of y_hat into y

    return float(tf.reduce_sum(tf.cast(cmp, y.dtype)))
    #change cmp datatype the same as y
    #sum up value of y
    #change the datatype of y into float

class Accumulator:
    #initialize class 
    def __init__(self, n): 
        self.data = [0, 0] * n 
    #make the data value 0 matrix 

    def add(self, *args):
    #we use *args since we are unsure about number of arguments to use in this function
    #use *args when our variable have non keywords arguments
        self.data = [a + float(b) for a, b in zip(self.data, args)]
    
    def reset(self):
        self.data = [0, 0] * len(self.data)
    #give back the data value back to the initialize one

    def __getitem__(self, idx):
        return self.data[idx]
    #get the data with the index number idx

def evaluate_accuracy(neural_network, x_test):
    metric = Accumulator(2)
    #sum over 2 variables

    for x, y in x_test:
        metric.add(accuracy(neural_network(x), y), tf.size(y).numpy())
        #add the accuracy between y_hat and y 
    return metric[0]/metric[1]

class update:
    def __init__(self, parameter, learning_rate):
        self.parameter = parameter 
        self.learning_rate = learning_rate
        #initialize update class 

    def __call__(self, batch_size, gradient):
        d2l.sgd(self.parameter, gradient, self.learning_rate, batch_size)
        #use stochastic gradient descent with a given learning_rate, batch_size and hyperparameter

def train_epoch(neural_network, x_train, loss, updater):
    metric = Accumulator(3)
    
    for x, y in x_train:
        with tf.GradientTape() as tape:
            #apply gradient descent 
            y_hat = neural_network(x)
            #attach our model into y_hat 

            if isinstance(loss, tf.keras.losses.Loss):
            #return true if cross_entropy the same type as Loss function 
                l = loss(y, y_hat)
            else:
                l = loss(y_hat, y)

        if isinstance(updater, tf.keras.optimizers.Optimizer):
            parameter = neural_network.trainable_variables
            gradient = tape.gradient(l, parameter)
            #do gradient descent with parameter to minimize l
            updater.apply_gradients(zip(gradient, parameter))
            #apply gradient with our gradient function 

        else:
            updater(x.shape[0], tape.gradient(l, updater.parameter))
        
        if isinstance(loss, tf.keras.losses.Loss):
            l_sum = l * float(tf.size(y))
        else:
            l_sum = tf.reduce_sum(l)
            #sum up add the loss value 

        metric.add(l_sum, accuracy(y_hat, y), tf.size(y))
    # Return training loss and training accuracy
    return metric[0] / metric[2], metric[1] / metric[2]

class Animation:
    #animate training process 
    def __init__(self, xlabel = None, ylabel = None, legend = None, xlim = None, ylim = None, xscale = 'linear', yscale = 'linear', 
                 fmts = ('-', 'm--', 'g-.', 'r:'), nrows = 1, ncols = 1,
                 figsize = (3.5, 2.5)):
        
        #initialize points array 
        if legend is None:
            legend = []

        d2l.use_svg_display()
        #svg stands for scalable vector graphics 
        #visualize svg figures for a sharper figure 

        self.fig, self.axes = d2l.plt.subplots(nrows, ncols, figsize = figsize)
        if nrows * ncols == 1:
            self.axes = [self.axes, ]

        self.config_axes = lambda: d2l.set_axes(
            self.axes[0], xlabel, ylabel, xlim, ylim, xscale, yscale, legend)
        #lambda function is used the same as loop 
    
        self.X, self.Y, self.fmts = None, None, fmts

    def add(self, x, y):
        # Add multiple data points into the figure
        if not hasattr(y, "__len__"):
            y = [y]
            
        n = len(y)
        
        if not hasattr(x, "__len__"):
            #hasattr can be understood as "has attribute"
            #used to check whether class x has the attribute of __len__
            x = [x] * n

        if not self.X:
            self.X = [[] for _ in range(n)]
        if not self.Y:
            self.Y = [[] for _ in range(n)]

        for i, (a, b) in enumerate(zip(x, y)):
            if a is not None and b is not None:
                self.X[i].append(a)
                self.Y[i].append(b)

        self.axes[0].cla()
        #cla or can be called clear axis 

        for x, y, fmt in zip(self.X, self.Y, self.fmts):
            self.axes[0].plot(x, y, fmt)

        self.config_axes()
        display.display(self.fig)
        display.clear_output(wait = True)

def training(neural_network, x_train, x_test, loss, num_epoch, update): 
    animator = Animation(xlabel = 'epoch', xlim = [1, num_epoch], ylim = [0.3, 0.9],
                        legend = ['Train_loss', 'Train_accuracy', 'Test_accuracy'])
    #animate training process 
    
    for epoch in range(num_epoch):
        #divide dataset into epochs and train individually
        train_metrics = train_epoch(neural_network, x_train, loss, update)
        #loop training process 

        test_accuracy = evaluate_accuracy(neural_network, x_test)
        #evaluate accuracy number to draw plot

        animator.add(epoch + 1, train_metrics + (test_accuracy, ))
        #draw plot throughout training 
    train_loss, train_accuracy = train_metrics
    print('train_loss = ' + str(train_loss) + '\n' + 'train_accuracy = ' +  str(train_accuracy))
    # assert train_loss < 0.5, train_loss
    # assert train_accuracy <= 1 and train_accuracy > 0.7, train_accuracy
    # assert test_accuracy <= 1 and test_accuracy > 0.7, test_accuracy
    #conditional sentences 
    #if the previous false, then assert the value of the following

updater = update([w, b], learning_rate = 0.5)
updater

num_epochs = 100
training(neural_network, x_train, x_test, cross_entropy, num_epochs, updater)

def predict(neural_network, x_test, data_size):
    for x, y in x_test:
        break
    x_test = d2l.get_fashion_mnist_labels(y)
    prediction = d2l.get_fashion_mnist_labels(tf.argmax(neural_network(x), axis = 1))

    #embed code
    #titles = ['corr: ' + true +'\n' + 'pred: ' + pred + '\n' for true, pred in zip(x_test, prediction)]
    #for _ in range(data_size):
    #d2l.show_images(tf.reshape(x[_]), 1, _, titles = titles[_])
    #

    titles = [true + '\n' + 'pred: ' + pred + '\n' for true, pred in zip(x_test, prediction)]
    d2l.show_images(tf.reshape(x[0 : data_size], (data_size, 28, 28)), 1, data_size, titles = titles[0 : data_size], scale = 3)

data_size = 20
predict(neural_network, x_test, data_size)
