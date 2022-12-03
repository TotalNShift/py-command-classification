'''
Author: liziwei01
Date: 2022-12-03 00:46:19
LastEditors: liziwei01
LastEditTime: 2022-12-03 02:36:08
Description: file content
'''
"""Tests model on testing data."""
from config import config
import prepare
import base_test

def test():
	testing_data, testing_labels = prepare.GetH5File(config.TrainH5FileName)
	correct = 0
	incorrect = 0

	for i in range(len(testing_data)):
		print("Testing {} of {}".format(i + 1, len(testing_data)), end="\r")
		predicted = base.predict_is_ci(testing_data[i])
		if predicted == (testing_labels[i][0] == 1):
			correct += 1
		else:
			incorrect += 1

	print("\nCorrect: {}/{} ({}%)".format(correct, correct + incorrect, correct/(correct + incorrect) * 100))

if __name__ == "__main__":
	test()