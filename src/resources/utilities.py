import datetime
import pandas as pd
from matplotlib import pylab

import src.resources.constants as cnst
import keras.utils
import os
from torchvision.utils import save_image
import torch
import imageio
import matplotlib.pyplot as plt

import numpy as np


def set_up_training_dirs(date):
    # Create directories if they don't exist
    if not os.path.exists(cnst.GAN_SAMPLES_DIR):
        os.makedirs(cnst.GAN_SAMPLES_DIR)

    if not os.path.exists(cnst.GAN_SAVE_DIR):
        os.makedirs(cnst.GAN_SAVE_DIR)

    if not os.path.exists(os.path.join(cnst.GAN_SAVE_DIR, date)):
        os.makedirs(os.path.join(cnst.GAN_SAVE_DIR, date))
    if not os.path.exists(os.path.join(cnst.GAN_SAMPLES_DIR, date)):
        os.makedirs(os.path.join(cnst.GAN_SAMPLES_DIR, date))
    if not os.path.exists(os.path.join(cnst.GAN_MODEL_DIR, date)):
        os.makedirs(os.path.join(cnst.GAN_MODEL_DIR, date))


def save_statistics(d_losses, g_losses, fake_scores, real_scores, path):
    np.save(os.path.join(path, 'd_losses.npy'), d_losses)
    np.save(os.path.join(path, 'g_losses.npy'), g_losses)
    np.save(os.path.join(path, 'fake_scores.npy'), fake_scores)
    np.save(os.path.join(path, 'real_scores.npy'), real_scores)

    plt.figure()
    pylab.xlim(0, cnst.GAN_NUM_EPOCHS + 1)
    plt.plot(range(1, cnst.GAN_NUM_EPOCHS + 1), d_losses, label='d loss')
    plt.plot(range(1, cnst.GAN_NUM_EPOCHS + 1), g_losses, label='g loss')
    plt.legend()
    plt.savefig(os.path.join(path, 'loss.png'))
    plt.close()

    plt.figure()
    pylab.xlim(0, cnst.GAN_NUM_EPOCHS + 1)
    pylab.ylim(0, 1)
    plt.plot(range(1, cnst.GAN_NUM_EPOCHS + 1), fake_scores, label='fake accuracy')
    plt.plot(range(1, cnst.GAN_NUM_EPOCHS + 1), real_scores, label='real accucary')
    plt.legend()
    plt.savefig(os.path.join(path, 'accuracy.png'))
    plt.close()


def fill_filenames_with_zeros(width):
    filenames = os.listdir(os.path.join(cnst.GAN_SAMPLES_DIR, "img"))
    for filename in filenames:
        filename_stripped = filename.strip('.png')
        filename_filled = filename_stripped.zfill(width)
        filename_filled += ".png"
        os.rename(os.path.join(cnst.GAN_SAMPLES_DIR, "img", filename),
                  os.path.join(cnst.GAN_SAMPLES_DIR, "img", filename_filled))


def generate_gif(filenames, save_path, read_path):
    with imageio.get_writer(os.path.join(save_path, "resultgif.gif"), mode='I', duration=0.5) as writer:
        for filename in filenames:
            image = imageio.imread(os.path.join(read_path, "img", filename))
            writer.append_data(image)


def denorm(x):
    out = (x + 1) / 2
    return out.clamp(0, 1)


def sample_image(G, n_row, name, path):
    """Saves a grid of generated digits ranging from 0 to n_classes"""
    # Sample noise
    z = torch.randn(n_row ** 2, cnst.GAN_LATENT_SIZE, 1, 1).cuda()  # Get labels ranging from 0 to n_classes for n rows
    # Get labels ranging from 0 to n_classes for n rows
    labels = np.array([num for _ in range(n_row) for num in range(n_row)])
    labels = torch.cuda.LongTensor(labels)
    gen_imgs = G(z, labels)
    if not os.path.exists(os.path.join(path, "img")):
        os.makedirs(os.path.join(path, "img"))
    save_image(gen_imgs.data,
               os.path.join(path, "img", name + ".png"), nrow=n_row, normalize=True)


def sample_same_label_image(G, available_labels, n_cols, name, path):
    """Saves a grid of generated digits ranging from 0 to n_classes"""
    # Sample noise
    z = torch.cuda.FloatTensor(np.random.normal(0, 1, (n_cols ** 2, cnst.GAN_LATENT_SIZE)))
    # Get labels ranging from 0 to n_classes for n rows
    labels = np.array([label for label in available_labels for _ in range(n_cols)])
    labels = torch.cuda.LongTensor(labels)
    gen_imgs = G(z, labels)
    if not os.path.exists(os.path.join(path, "img")):
        os.makedirs(os.path.join(path, "img"))
    save_image(gen_imgs.reshape(gen_imgs.shape[0], 1, gen_imgs.shape[1], gen_imgs.shape[2]).data,
               os.path.join(path, "img", name + ".png"), nrow=n_cols, normalize=True)


def check_for_gpu():
    # Make sure that we're using gpu
    from tensorflow.python.client import device_lib
    assert 'GPU' in str(device_lib.list_local_devices())

    # confirm Keras sees the GPU
    from keras import backend
    assert len(backend.tensorflow_backend._get_available_gpus()) > 0


def save_predictions(predictions, filenames, result_name):
    pred_vec = []
    # Get classes predicted with highest probability for every image
    for prediction in predictions:
        idx = np.argmax(prediction)
        pred_vec.append(idx)

    images = filenames
    # Strip images to only contain names of files
    for i in range(0, len(filenames)):
        filenames[i] = filenames[i].replace('/', '\\').split('\\')[1]

    # Save image names and predictions to dictionary
    savedictfinal = {'image': [], 'class': []}
    for image, pred in zip(images, pred_vec):
        savedictfinal['image'].append(image)
        savedictfinal['class'].append(pred)

    # Save te dictionary to csv in RES_DIR in format MONTH-DAY-HOUR-MINUTE-RESULT_NAME
    date = datetime.datetime.now().strftime("%m-%d-%H-%M-")
    save_df = pd.DataFrame.from_dict(data=savedictfinal)
    save_df.to_csv(os.path.join(cnst.RES_DIR, date + result_name), index=False)


def load_data(imgs_amount, val_split):
    # Load data
    import gzip
    import sys
    import pickle
    f = gzip.open("./data/mnist.pkl.gz", 'rb')
    if sys.version_info < (3,):
        data = pickle.load(f)
    else:
        data = pickle.load(f, encoding='bytes')
    f.close()

    (x_train, y_train), (x_test, y_test) = data

    # Pick only imgs_amount of images
    if val_split == 0:
        x_train = x_train[:imgs_amount]
        y_train = y_train[:imgs_amount]
        x_test = None
        y_test = None
    else:
        x_train = x_train[:imgs_amount - int(imgs_amount * val_split)]
        y_train = y_train[:imgs_amount - int(imgs_amount * val_split)]
        x_test = x_test[:int(imgs_amount * val_split)]
        y_test = y_test[:int(imgs_amount * val_split)]

        x_test = x_test.reshape(x_test.shape[0], 28, 28, 1)
        x_test = x_test.astype('float32')
        x_test /= 255
        y_test = keras.utils.to_categorical(y_test)

    x_train = x_train.reshape(x_train.shape[0], 28, 28, 1)

    # Making sure that the values are float so that we can get decimal points after division
    x_train = x_train.astype('float32')

    # Normalizing the RGB codes by dividing it to the max RGB value.
    x_train /= 255

    # Convert labels to one-hot encoding
    y_train = keras.utils.to_categorical(y_train)

    return (x_train, y_train), (x_test, y_test)

    # Change from matrix to array of dimension 28x28 to array of dimension 784


def load_data_flat(imgs_amount, val_split):
    # Loads the images and flattens them to arrays
    (x_train, y_train), (x_test, y_test) = load_data(imgs_amount, val_split)
    dimData = np.prod(x_train.shape[1:])
    x_train = x_train.reshape(x_train.shape[0], dimData)
    x_test = x_test.reshape(x_test.shape[0], dimData)
    return (x_train, y_train), (x_test, y_test)


def load_GAN_data_flat(imgs_amount, val_split):
    # Loads the images and flattens them to arrays
    (x_train, y_train), (x_test, y_test) = load_GAN_data(imgs_amount, val_split)
    dimData = np.prod(x_train.shape[1:])
    x_train = x_train.reshape(x_train.shape[0], dimData)
    x_test = x_test.reshape(x_test.shape[0], dimData)
    return (x_train, y_train), (x_test, y_test)


def load_GAN_data(imgs_amount, val_split):
    # Load data
    data = np.load(os.path.join(cnst.GAN_DIR, "gan_images.npy"))
    labels = np.load(os.path.join(cnst.GAN_DIR, "gan_labels.npy"))

    # Pick only imgs_amount of images
    if val_split == 0:
        x_train = data[:imgs_amount]
        y_train = labels[:imgs_amount]
        x_test = None
        y_test = None
    else:
        x_train = data[:imgs_amount - int(imgs_amount * val_split)]
        y_train = labels[:imgs_amount - int(imgs_amount * val_split)]
        x_test = data[:int(imgs_amount * val_split)]
        y_test = labels[:int(imgs_amount * val_split)]

        x_test = x_test.reshape(x_test.shape[0], 28, 28, 1)
        x_test = x_test.astype('float32')
        x_test /= 255
        y_test = keras.utils.to_categorical(y_test)

    x_train = x_train.reshape(x_train.shape[0], 28, 28, 1)

    # Making sure that the values are float so that we can get decimal points after division
    x_train = x_train.astype('float32')

    # Normalizing the RGB codes by dividing it to the max RGB value.
    x_train /= 255

    # Convert labels to one-hot encoding
    y_train = keras.utils.to_categorical(y_train)

    return (x_train, y_train), (x_test, y_test)


def save_info(path, epochs, batch, dis_feature_maps, gen_feature_maps):
    with open(path, 'w+') as file:
        lines = ["EPOCHS: "+str(epochs)+"\n","BATCH_SIZE: "+str(batch)+"\n",
                 "DIS_FEAT_MAPS: "+str(dis_feature_maps)+"\n","GEN_FEAT_MAPS: "+str(gen_feature_maps)+"\n"]
        file.writelines(lines)



