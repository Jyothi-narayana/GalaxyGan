from config import Config as conf
from data import *
import scipy.misc
from model import CGAN
from utils import imsave
import tensorflow as tf
import numpy as np
import time
import sys
import matplotlib.pyplot as plt
import skimage.measure

def prepocess_train(img, cond,):
    img = scipy.misc.imresize(img, [conf.adjust_size, conf.adjust_size])
    cond = scipy.misc.imresize(cond, [conf.adjust_size, conf.adjust_size])
    h1 = int(np.ceil(np.random.uniform(1e-2, conf.adjust_size - conf.train_size)))
    w1 = int(np.ceil(np.random.uniform(1e-2, conf.adjust_size - conf.adjust_size)))
    img = img[h1:h1 + conf.train_size, w1:w1 + conf.train_size]
    cond = cond[h1:h1 + conf.train_size, w1:w1 + conf.train_size]
    if np.random.random() > 0.5:
        img = np.fliplr(img)
        cond = np.fliplr(cond)
    img = img/127.5 - 1.
    cond = cond/127.5 - 1.
    img = img.reshape(1, conf.img_size, conf.img_size, conf.img_channel)
    cond = cond.reshape(1, conf.img_size, conf.img_size, conf.img_channel)
    #viewer = ImageViewer(img)
    #viewer = ImageViewer(img)
    return img,cond

def prepocess_test(img, cond):

    img = scipy.misc.imresize(img, [conf.train_size, conf.train_size])
    cond = scipy.misc.imresize(cond, [conf.train_size, conf.train_size])
    img = img.reshape(1, conf.img_size, conf.img_size, conf.img_channel)
    cond = cond.reshape(1, conf.img_size, conf.img_size, conf.img_channel)
    img = img/127.5 - 1.
    cond = cond/127.5 - 1.
    return img,cond

def train():
    data = load_data()
    model = CGAN()

    d_opt = tf.train.AdamOptimizer(learning_rate=conf.learning_rate).minimize(model.d_loss, var_list=model.d_vars)
    g_opt = tf.train.AdamOptimizer(learning_rate=conf.learning_rate).minimize(model.g_loss, var_list=model.g_vars)

    saver = tf.train.Saver()

    counter = 0
    start_time = time.time()
    if not os.path.exists(conf.data_path + "/checkpoint"):
        os.makedirs(conf.data_path + "/checkpoint")
    if not os.path.exists(conf.output_path):
        os.makedirs(conf.output_path)

    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    mpsnr_img = []
    mpsnr_cond = []
    with tf.Session(config=config) as sess:
        if conf.model_path == "":
            sess.run(tf.initialize_all_variables())
        else:
            saver.restore(sess, conf.model_path)
        print conf.max_epoch
        for epoch in xrange(conf.max_epoch):
            train_data = data["train"]()
            for img, cond, name in train_data:
                img, cond = prepocess_train(img, cond)
                _, m = sess.run([d_opt, model.d_loss], feed_dict={model.image:img, model.cond:cond})
                _, m = sess.run([d_opt, model.d_loss], feed_dict={model.image:img, model.cond:cond})
                _, M = sess.run([g_opt, model.g_loss], feed_dict={model.image:img, model.cond:cond})
                counter += 1
                print "Iterate [%d]: time: %4.4f, d_loss: %.8f, g_loss: %.8f" \
                      % (counter, time.time() - start_time, m, M)
            if (epoch + 1) % conf.save_per_epoch == 0:
                save_path = saver.save(sess, conf.data_path + "/checkpoint/" + "model_%d.ckpt" % (epoch+1))
                print "Model saved in file: %s" % save_path
                mean_psnr_img = 0
                mean_psnr_cond = 0
                i = 0
                test_data = data["test"]()
                for img, cond, name in test_data:
                    pimg, pcond = prepocess_test(img, cond)
                    gen_img = sess.run(model.gen_img, feed_dict={model.image:pimg, model.cond:pcond})
                    gen_img = gen_img.reshape(gen_img.shape[1:])
                    gen_img = (gen_img + 1.) * 127.5
                    #print type(img), type(cond), type(gen_img), img.shape, cond.shape, gen_img.shape, img.dtype, cond.dtype, gen_img.dtype
                    mean_psnr_img = mean_psnr_img + skimage.measure.compare_psnr(img, gen_img.astype(np.uint8))
                    mean_psnr_cond = mean_psnr_cond + skimage.measure.compare_psnr(cond, gen_img.astype(np.uint8))
                    image = np.concatenate((gen_img, cond), axis=1).astype(np.int)
                    i = i + 1
                    imsave(image, conf.output_path + "/%s" % name)
                mean_psnr_img = mean_psnr_img/i
                mpsnr_img.append(mean_psnr_img)
                mean_psnr_cond = mean_psnr_cond/i
                mpsnr_cond.append(mean_psnr_cond)
        print mpsnr_cond
        print mpsnr_img
        plt.plot(mpsnr_cond)
        plt.show()
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'gpu=':
        os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"   # see issue #152
        os.environ["CUDA_VISIBLE_DEVICES"]=str(sys.argv[1][4:])
    else:
        os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"   # see issue #152
        os.environ["CUDA_VISIBLE_DEVICES"]=str(0)
    train()
