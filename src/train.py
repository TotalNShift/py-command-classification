'''
Author: liziwei01
Date: 2022-11-08 12:31:40
LastEditors: liziwei01
LastEditTime: 2022-12-01 21:27:48
Description: file content
'''
import os
import time

import tensorflow as tf

import prepare

# three layer conv

# let's assume each command will not exceed 10 words. 
# Actually the most important word is the very first word.
# It may not be a big deal if we drop the last few words. 
# Then we assume each word in a command is no longer than 10 letters. 
# if not, we drop again
# we can change these numbers (10) at any time.

# now, a command like: `ping localhost` will form a matrix like
# [ping
# localhost
# 0
# 0
# 0
# 0
# 0
# 0
# 0
# 0]
# now we assume the command matrix to be an image input to the conv (CNN is originally developed for image)

### configurations
epoch = 15000
saveInterval = 5000
batchSize = 10
padding = "VALID"
checkpointDir = "data/checkpoint/"

# [width, depth, numberofInputChannels, numberofOutputChannels]
# [width, depth] is the shape of conv kernel
# numberofInputChannels means the number of matrix we use as an input of this conv kernel. Each time we have only one command as the first layer input so it's 1
# numberofOutputChannels means number of matrix generated by the conv kernel. the larger this number is, the more information we keep after the extraction (yes, conv action is actually losing informaion)
# now input is 13, 13
inputShape1 = [7, 7, 1, 64] # [7, 7]
inputShape2 = [5, 5, 64, 32] # [3, 3]
inputShape3 = [3, 3, 32, 1] # [1, 1]
# shapes above like [5, 5], [2, 2] can only be determined by experiment by now.
# we don't know which kind of combine of shapes and how many layers of conv (now we have 3) can lead to a better result
# what we can do is give it a try. train it for a while and see if it can pass our test
# each layer will make the matrix shrimp a little bit
# like [5, 5, 1, 16] will make a [10, 10] matrix become a [6, 6] matrix because the feature of kernel scanning

stddev = 1e-4
###

trainable = True
ReLU = "ReLU"
normalStrides = [1,1,1,1]
placeholderShape = [None, None, None, 1]

tf.compat.v1.disable_eager_execution()
Inputs = tf.compat.v1.placeholder(tf.float32, placeholderShape, name="inputs")
Labels = tf.compat.v1.placeholder(tf.float32, placeholderShape, name="labels")
weights = {
	"w1": tf.Variable(initial_value=tf.random.normal(inputShape1, stddev=stddev), trainable=trainable, name="w1"),
	"w2": tf.Variable(initial_value=tf.random.normal(inputShape2, stddev=stddev), trainable=trainable, name="w2"),
	"w3": tf.Variable(initial_value=tf.random.normal(inputShape3, stddev=stddev), trainable=trainable, name="w3"),
}
biases = {
	"b1": tf.Variable(initial_value=tf.zeros([inputShape1[len(inputShape1)-1]]), trainable=trainable , name="b1"),
	"b2": tf.Variable(initial_value=tf.zeros([inputShape2[len(inputShape2)-1]]), trainable=trainable , name="b2"),
	"b3": tf.Variable(initial_value=tf.zeros([inputShape3[len(inputShape3)-1]]), trainable=trainable , name="b3"),
}
# the length we want the conv kernel move
# like if our kernel is [3, 3, 3, 3] now and it does not perform good
# we may want the kernel move a little bit
# if the value is 0.1, it becomes like [2.9, 3, 3, 3]
# here is a trade
# if you set it a very large value, the training will fall into the optimal solution very soon
# but we don't know if it is the global optimal or just local optimal
# large value means faster training and larger chance to miss the global optimal
# so we may want a small value to try our best to reach the global optimal
optimizer = {
	"o1": tf.compat.v1.train.GradientDescentOptimizer(stddev),
	"o2": tf.compat.v1.train.GradientDescentOptimizer(stddev),
	"o3": tf.compat.v1.train.GradientDescentOptimizer(stddev)
}

def getLoss(labels, pred):
	# return tf.reduce_mean(input_tensor=tf.square(labels - pred))
	return tf.reduce_mean(input_tensor=tf.nn.sigmoid_cross_entropy_with_logits(labels=labels, logits=pred))

def get2DConv(idx, inputs, weights, biases, padding, strides=normalStrides, activation=ReLU):
	conv = tf.nn.conv2d(input=inputs, filters=weights["w"+idx], strides=strides, padding=padding) + biases["b"+idx]
	if activation == ReLU:
		conv = tf.nn.relu(conv)
	return conv

def train():
	trainingData, trainingLabel = prepare.GetH5File(fileName=prepare.PreparedTrainingH5Name)
	conv1 = get2DConv(idx="1", inputs=Inputs, weights=weights, biases=biases, padding=padding)
	conv2 = get2DConv(idx="2", inputs=conv1, weights=weights, biases=biases, padding=padding)
	conv3 = get2DConv(idx="3", inputs=conv2, weights=weights, biases=biases, padding=padding, activation=None)

	conv_out = conv3

	var_list1 = [weights["w1"], biases["b1"], weights["w2"], biases["b2"]]
	var_list2 = [weights["w3"], biases["b3"]]
	
	loss = getLoss(Labels, conv_out)
	grads = tf.gradients(ys=loss, xs=var_list1 + var_list2)
	grads1 = grads[:len(var_list1)]
	grads2 = grads[len(var_list1):]

	train_op1 = optimizer["o1"].apply_gradients(zip(grads1, var_list1))
	train_op2 = optimizer["o2"].apply_gradients(zip(grads2, var_list2))
	train_op = tf.group(train_op1, train_op2)

	counter = 0
	start_time = time.time()
	saver=tf.compat.v1.train.Saver(max_to_keep=5)

	with tf.compat.v1.Session() as sess:
		print("Training...")
		sess.run(tf.compat.v1.initialize_all_variables())
		ckpt = tf.train.get_checkpoint_state(checkpoint_dir=checkpointDir)
		if ckpt and ckpt.model_checkpoint_path:
			print("Continuing")
			saver.restore(sess, ckpt.model_checkpoint_path)
		
		for ep in range(epoch):
			# Run by batch to save some time
			batch_idxs = len(trainingData) // batchSize
			for idx in range(0, batch_idxs):
				batch_data = trainingData[idx*batchSize : (idx+1)*batchSize]
				batch_labels = trainingLabel[idx*batchSize : (idx+1)*batchSize]

				counter +=1
				_, err = sess.run(fetches=[train_op, loss], feed_dict={Inputs: batch_data, Labels: batch_labels})

				if counter % saveInterval == 0:
					print("Epoch: [%2d], step: [%2d], time: [%4.4f], loss: [%.8f]" % ((ep+1), counter, time.time()-start_time, err))
					saver.save(sess, os.path.join(checkpointDir, "cmd"), global_step=counter, write_meta_graph=False)

if __name__ == "__main__":
	train()
