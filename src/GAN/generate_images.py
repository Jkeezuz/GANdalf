import os
import torch
from torch.autograd import Variable
import numpy as np
from torchvision.utils import save_image
from src.resources import constants as cnst
from src.GAN.Generator import Generator
import matplotlib.pyplot as plt
from torch import nn


# Create directories if they don't exist
if not os.path.exists(cnst.GAN_SAMPLES_DIR):
    os.makedirs(cnst.GAN_SAMPLES_DIR)

if not os.path.exists(cnst.GAN_SAVE_DIR):
    os.makedirs(cnst.GAN_SAVE_DIR)

# Import MNIST dataset
G = Generator(img_shape=(28, 28), n_classes=10, latent_dim=cnst.GAN_LATENT_SIZE).cuda()
FloatTensor = torch.cuda.FloatTensor
LongTensor = torch.cuda.LongTensor

G.load_state_dict(torch.load('G.ckpt'))

n_class = 10


z = FloatTensor(np.random.normal(0, 1, (10000, cnst.GAN_LATENT_SIZE)))
# Get labels ranging from 0 to n_classes for n rows
labels = np.array([num for _ in range(1000) for num in range(n_class)])

# This throws ValueError strides are negative (?????)
#one_hot_labels = np.arange(10)
#one_hot_labels = np.flipud(one_hot_labels)

one_hot_labels = np.zeros(10)
for i in range(0, 10):
    one_hot_labels[i] = i

print(one_hot_labels.reshape(1, -1))
G.train_one_hot(one_hot_labels)
gen_imgs = G(z, labels)

save_image(gen_imgs.reshape(gen_imgs.shape[0], 1, gen_imgs.shape[1], gen_imgs.shape[2]).data,
           os.path.join(cnst.GAN_SAMPLES_DIR, "generatedVIS3.png"), nrow=n_class, normalize=True)
save_image(gen_imgs.reshape(gen_imgs.shape[0], 1, gen_imgs.shape[1], gen_imgs.shape[2]).data,
           os.path.join(cnst.GAN_SAMPLES_DIR, "generatedVIS4.png"), nrow=n_class*10, normalize=True)
gen_imgs = gen_imgs.cpu().data.numpy()

# Move the data to CPU and then copy it to numpy array
np.save(file=os.path.join(cnst.GAN_DATA_DIR, "gan_images.npy"), arr=gen_imgs)
np.save(file=os.path.join(cnst.GAN_DATA_DIR, "gan_labels.npy"), arr=labels)



for i in range(n_class):
    plt.title('Label is {label}'.format(label=i))
    plt.imshow(gen_imgs[i], cmap='gray')
    plt.show()
print("")