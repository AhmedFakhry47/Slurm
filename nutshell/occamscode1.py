"""
Exponential Decay Trial
"""


# Commented out IPython magic to ensure Python compatibility.
# %%capture
# !pip install git+https://github.com/taehoonlee/tensornets.git
# !pip install ipynb
# !pip install wget
# !pip install messages

#import libraries
import tensorflow as tf
import tensornets as nets
import voc
import numpy as np
import matplotlib.pyplot as plt
import math
from IPython.display import clear_output
import random
import cv2
from copy import copy, deepcopy
from pathlib import Path
import os
import time 
from datetime import timedelta
from tqdm import tqdm
#import zipfile
import tarfile
import shutil
import wget
import sys


class ContIt(Exception): pass  # a class to continue nested loop

data_dir = "/home/alex054u4/data/nutshell/newdata/"
subject= "Trial 1 on server- Occam's Code NOT -Separable"
emails_list=['ahmedfakhry805@gmail.com', 'ahmadadelattia@gmail.com']
#Create data folder
if not os.path.exists(data_dir): os.makedirs(data_dir)

#In case of VOC
urls = ['http://host.robots.ox.ac.uk/pascal/VOC/voc2012/VOCtrainval_11-May-2012.tar','http://host.robots.ox.ac.uk/pascal/VOC/voc2007/VOCtrainval_06-Nov-2007.tar','http://host.robots.ox.ac.uk/pascal/VOC/voc2007/VOCtest_06-Nov-2007.tar']

for root, dirs, files in os.walk("/home/alex054u4/data/nutshell/", topdown=True):
  for dir in dirs:
    if ((dir == 'VOC2012' or dir =='VOC2007') and len(urls) != 0):
      for url in urls:
        if (url.find(dir.lower())): 
          urls.remove(url)

for url in tqdm(urls):
  wget.download(url)
  shutil.move('/home/alex054u4/data/nutshell/'+url.split('/')[-1], data_dir+url.split('/')[-1])
  with tarfile.open(data_dir+url.split('/')[-1]) as zipped:
    zipped.extractall(data_dir)
    os.unlink(data_dir+url.split('/')[-1])

C1=[238, 72, 58, 24, 203, 230, 54, 167, 246, 136, 106, 95, 226, 171, 43, 159, 231, 101, 65, 157]
C2=[122, 71, 173, 32, 147, 241, 53, 197, 228, 164, 4, 209, 175, 223, 176, 182, 48, 3, 70, 13]
C3=[148, 69, 133, 41, 157, 137, 125, 245, 89, 85, 162, 43, 16, 178, 197, 150, 13, 140, 177, 224]
idx_to_labels=['aeroplane','bicycle','bird','boat','bottle','bus','car','cat','chair','cow','diningtable','dog','horse','motorbike','person','pottedplant','sheep','sofa','train','tvmonitor']
def visualize_img(img,bboxes,thickness,name):
  img=img.reshape(img.shape[1],img.shape[1],3)
  for c, boxes_c in enumerate(bboxes):
    for b in boxes_c:
      ul_x, ul_y=b[0]-b[2]/2.0, b[1]-b[3]/2.0
      br_x, br_y=b[0]+b[2]/2.0, b[1]+b[3]/2.0

      ul_x, ul_y=(min(max(int(ul_x),0),415),min(max(int(ul_y),0),415))
      br_x, br_y=(min(max(int(br_x),0),415),min(max(int(br_y),0),415))

      color_class=(C1[c], C2[c], C3[c])
      img=cv2.rectangle(img, (ul_x, ul_y), (br_x, br_y), color=color_class, thickness=3) 
      label = '%s: %.2f' % (idx_to_labels[c], b[-1]) 
      labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1) 
      ul_y = max(ul_y, labelSize[1]) 
      img=cv2.rectangle(img, (ul_x, ul_y - labelSize[1]), (ul_x + labelSize[0], ul_y + baseLine),color_class, cv2.FILLED) 
      img=cv2.putText(img, label, (ul_x, ul_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0)) 

  cv2.imwrite(name+'.jpg', img)
  return img 

voc_dir = '/home/alex054u4/data/nutshell/newdata/VOCdevkit/VOC%d'

# Define the model hyper parameters
is_training = tf.placeholder(tf.bool)
N_classes=20
x = tf.placeholder(tf.float32, shape=(None, 416, 416, 3), name='input_x')
yolo=nets.YOLOv2(x, nets.MobileNet25, is_training=True, classes=N_classes)
# Define an optimizer
step = tf.Variable(0, trainable=False)
lr   = tf.Variable(1e-3,trainable=False,dtype=tf.float32)
decay_op = tf.math.multiply(tf.math.pow(0.935,tf.cast(step,tf.float32)),1e-3)  
train    = tf.train.AdamOptimizer(learning_rate=lr,beta1=0.9,beta2=0.99,epsilon=1e-8).minimize(yolo.loss,global_step=step)


#Check points
checkpoint_path   = "/home/alex054u4/data/nutshell/training_trial33"
checkpoint_prefix = os.path.join(checkpoint_path,"ckpt")
if not os.path.exists(checkpoint_path):
  os.mkdir(checkpoint_path)

init_op     = tf.global_variables_initializer()
train_saver = tf.train.Saver(max_to_keep=2)


def evaluate_accuracy(data_type='tr'):
  if (data_type  == 'tr'): acc_data  = voc.load(voc_dir % 2012,'trainval',total_num =48)
  elif(data_type == 'te') : acc_data  = voc.load(voc_dir % 2007, 'test', total_num=48)
  
  #print('Train Accuracy: ',voc.evaluate(boxes, voc_dir % 2007, 'trainval'))
  results = []
  for i,(img,_) in enumerate(acc_data):
    acc_outs = sess.run(yolo, {x: yolo.preprocess(img),is_training: False})
    boxes=yolo.get_boxes(acc_outs, img.shape[1:3])
    results.append(boxes)
  if (data_type  =='tr'):return voc.evaluate(results, voc_dir % 2012, 'trainval')
  elif (data_type=='te'):return voc.evaluate(results, voc_dir % 2007, 'test')


with tf.Session() as sess:
  ckpt_files = [f for f in os.listdir(checkpoint_path) if os.path.isfile(os.path.join(checkpoint_path, f)) and 'ckpt' in f]
  if (len(ckpt_files)!=0):
    train_saver.restore(sess,checkpoint_prefix)
  else:
    sess.run(init_op)
    sess.run(yolo.stem.pretrained())

  losses = []
  for i in range(step.eval(),233):
    print(" \n Epoch", i, "starting...")
    # Iterate on VOC07+12 trainval once

    trains = voc.load_train([voc_dir % 2012, voc_dir % 2007],'trainval', batch_size=48)

    #Update LR before evaluation
    sess.run(step.assign(i))
    sess.run(lr.assign(decay_op))
    
    pbar = tqdm(total = 344) 
    for (imgs, metas) in trains:
      # `trains` returns None when it covers the full batch once
      if imgs is None:break

      metas.insert(0, yolo.preprocess(imgs))  # for `inputs`
      metas.append(True)                      # for `is_training`
      outs= sess.run([train, yolo.loss],dict(zip(yolo.inputs, metas)))
      losses.append(outs[-1])
      pbar.update(1)

    pbar.close()
    print_out='epoch:'+str(i)+'lr: '+str(lr.eval())+'loss:'+str(losses[-1])
    print(print_out)
    print(evaluate_accuracy('tr'))
    print(evaluate_accuracy('te'))

    train_saver.save(sess,checkpoint_prefix)

