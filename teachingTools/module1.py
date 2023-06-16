# example taken from https://wellsr.com/python/how-to-create-custom-modules-in-python/
import numpy as np

def print_text():
    print("This message is from an external module")


def find_log(num):
    return np.log(num)

def find_exp(num):
    return np.exp(num)