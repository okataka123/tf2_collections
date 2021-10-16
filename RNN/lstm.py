#!/usr/bin/env python
# Tensorflow 2.0, Subclassing API

import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle
import tensorflow as tf
from tensorflow.keras import datasets
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, SimpleRNN, LSTM
from tensorflow.keras import optimizers
from tensorflow.keras import losses
from tensorflow.keras import metrics
from callbacks import EarlyStopping

class RNN(Model):
    def __init__(self, hidden_dim):
        super().__init__()
        self.l1 = LSTM(
                hidden_dim,
                activation='tanh',
                recurrent_activation='sigmoid',
                kernel_initializer='glorot_normal',
                recurrent_initializer='orthogonal',
        )
        self.l2 = Dense(1, activation='linear')

    def call(self, x):
        h = self.l1(x)
        y = self.l2(h)
        return y

def sin(x, T=100):
    return np.sin(2.0*np.pi*x/T) 

def toy_problem(T=100, ampl=0.05):
    x = np.arange(0, 2*T+1)
    noise = ampl * np.random.uniform(low=-1.0, high=1.0, size=len(x))
    return sin(x) + noise

T = 100
f = toy_problem(T).astype(np.float32)
length_of_sequences = len(f)

def visualize():
    fig, ax = plt.subplots()
    ax.plot(np.arange(0, 2*T+1), f)
    plt.show()

# data split
maxlen = 25

x = []
t = []

for i in range(len(f)-maxlen):
    x.append(f[i:i+maxlen])
    t.append(f[i+maxlen])

x = np.array(x).reshape(-1, maxlen, 1)
t = np.array(t).reshape(-1, 1)

x_train, x_val, t_train, t_val = train_test_split(x, t, test_size=0.2, shuffle=False)

model = RNN(50)

# 学習
criterion = losses.MeanSquaredError()
optimizer = optimizers.Adam(
        learning_rate=0.001,
        beta_1=0.9,
        beta_2=0.999,
        amsgrad=True,
)

train_loss = metrics.Mean()
val_loss = metrics.Mean()

def compute_loss(t, y):
    return criterion(t, y)

def train_step(x, t):
    # back propergation
    with tf.GradientTape() as tape:
        preds = model(x)
        loss = compute_loss(t, preds)
    grads = tape.gradient(loss, model.trainable_variables)
    optimizer.apply_gradients(zip(grads, model.trainable_variables))
    train_loss(loss)
    return loss

def val_step(x, t):
    preds = model(x)
    loss = compute_loss(t, preds)
    val_loss(loss)

# main
epochs = 1000
batch_size = 100
n_batches_train = x_train.shape[0] // batch_size + 1
n_batches_val = x_val.shape[0] // batch_size + 1

hist = {'loss': [], 'val_loss': []}
es = EarlyStopping(patience=10, verbose=1)

for epoch in range(epochs):
    x_, t_ = shuffle(x_train, t_train)

    for batch in range(n_batches_train):
        start = batch * batch_size
        end = start + batch_size
        train_step(x_[start:end], t_[start:end])

    for batch in range(n_batches_val):
        start = batch * batch_size
        end = start + batch_size
        val_step(x_val[start:end], t_val[start:end])

    hist['loss'].append(train_loss.result())
    hist['val_loss'].append(val_loss.result())

    print('epoch: {}, loss: {:.3}, val_loss: {:.3f}'.format(epoch+1, train_loss.result(), val_loss.result()))

    if es(val_loss.result()):
        break

"""
evaluate the model
"""
sin = toy_problem(T, ampl=0.) # noiseなし
gen = [None for i in range(maxlen)] # 予測値を時系列で保持するためのリスト

z = x[:1] # 予測用に元データの最初の部分だけ用いる。

for i in range(length_of_sequences - maxlen):
    preds = model.predict(z[-1:]) # 次の1点を予測
    z = np.append(z, preds)[1:]   # 予測値を含んだ次の入力
    z = z.reshape(-1, maxlen, 1)  # np.append()により変わったshapeの調整
    gen.append(preds[0, 0])

# 予測値を可視化
fig = plt.figure()
plt.rc('font', family='serif')
plt.xlim([0, 2*T])
plt.ylim([-1.5, 1.5])
plt.plot(range(len(f)), sin, color='gray', linestyle='--', linewidth=0.5)
plt.plot(range(len(f)), gen, color='black', linewidth=1, marker='o', 
        markersize=1, markerfacecolor='black', markeredgecolor='black')
plt.show()

