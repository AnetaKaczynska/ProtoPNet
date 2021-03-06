"""Pytorch Dataset object that loads 27x27 patches that contain single cells."""

import os
import random

import numpy as np
import scipy.io
import torch
import torch.utils.data as data_utils
import torchvision.transforms as transforms
from skimage import io, color

import utils_augemntation


class ColonCancerBagsCross(data_utils.Dataset):
    def __init__(self, path, train_val_idxs=None, test_idxs=None, train=True, shuffle_bag=False,
                 data_augmentation=False, loc_info=False, push=False, nucleus_type=None):
        self.path = path
        self.train_val_idxs = train_val_idxs
        self.test_idxs = test_idxs
        self.train = train
        self.shuffle_bag = shuffle_bag
        self.data_augmentation = data_augmentation
        self.location_info = loc_info
        self.push = push
        self.nucleus_type = nucleus_type

        tr = [utils_augemntation.RandomHEStain(),
              utils_augemntation.HistoNormalize(),
              utils_augemntation.RandomRotate(),
              utils_augemntation.RandomVerticalFlip(),
              transforms.RandomHorizontalFlip(),
              transforms.ToTensor()
              ]
        tst = [utils_augemntation.HistoNormalize(),
               transforms.ToTensor()
               ]

        psh = [transforms.ToTensor()]

        self.data_augmentation_img_transform = transforms.Compose(tr)

        self.normalize_to_tensor_transform = transforms.Compose(tst)

        self.to_tensor_transform = transforms.Compose(psh)

        self.dir_list_train, self.dir_list_test = self.split_dir_list(self.path, self.train_val_idxs, self.test_idxs)
        if self.train:
            if nucleus_type:
                self.bag_list_train, self.labels_list_train = self.create_bags_one_type(self.dir_list_train)
            else:
                self.bag_list_train, self.labels_list_train = self.create_bags(self.dir_list_train)
        else:
            if nucleus_type:
                self.bag_list_test, self.labels_list_test = self.create_bags_one_type(self.dir_list_test)
            else:
                self.bag_list_test, self.labels_list_test = self.create_bags(self.dir_list_test)

    @staticmethod
    def split_dir_list(path, train_val_idxs, test_idxs):
        dirs = [x[0] for x in os.walk(path)]
        dirs.pop(0)
        dirs.sort()

        dir_list_train = list(sorted([dirs[i] for i in train_val_idxs]))
        dir_list_test = list(sorted([dirs[i] for i in test_idxs]))

        return dir_list_train, dir_list_test

    def create_bags_one_type(self, dir_list):
        """Create bags containing only one type of nucleus."""
        bag_list = []
        labels_list = []
        for dir in dir_list:
            # Get image name
            img_name = dir.split('/')[-1]

            # bmp to pillow
            img_dir = dir + '/' + img_name + '.bmp'
            img = io.imread(img_dir)

            if img.shape[2] == 4:
                img = color.rgba2rgb(img)

            if self.location_info:
                xs = np.arange(0, 500)
                xs = np.asarray([xs for i in range(500)])
                ys = xs.transpose()
                img = np.dstack((img, xs, ys))

            # crop nucleus_type cells
            dir_nucleus_type = dir + '/' + img_name + '_' + self.nucleus_type + '.mat'
            with open(dir_nucleus_type, 'rb') as f:
                mat_nucleus_type = scipy.io.loadmat(f)

            cropped_cells = []
            for (x, y) in mat_nucleus_type['detection']:
                x = np.round(x)
                y = np.round(y)

                if self.data_augmentation:
                    x = x + np.round(np.random.normal(0, 3, 1))
                    y = y + np.round(np.random.normal(0, 3, 1))

                if x < 13:
                    x_start = 0
                    x_end = 27
                elif x > 500 - 14:
                    x_start = 500 - 27
                    x_end = 500
                else:
                    x_start = x - 13
                    x_end = x + 14

                if y < 13:
                    y_start = 0
                    y_end = 27
                elif y > 500 - 14:
                    y_start = 500 - 27
                    y_end = 500
                else:
                    y_start = y - 13
                    y_end = y + 14

                cropped_cells.append(img[int(y_start):int(y_end), int(x_start):int(x_end)])

            # if image doesn't contain any specific type nucleus, move to the next image
            if cropped_cells == []:
                continue

            # generate bag
            bag = cropped_cells

            # store single cell labels
            if self.nucleus_type == 'epithelial':
                labels = np.ones(len(cropped_cells))
            else:
                labels = np.zeros(len(cropped_cells))

            # shuffle
            if self.shuffle_bag:
                zip_bag_labels = list(zip(bag, labels))
                random.shuffle(zip_bag_labels)
                bag, labels = zip(*zip_bag_labels)

            # append every bag two times if training
            if self.train:
                for _ in [0, 1]:
                    bag_list.append(bag)
                    labels_list.append(labels)
            else:
                bag_list.append(bag)
                labels_list.append(labels)

            # bag_list.append(bag)
            # labels_list.append(labels)

        return bag_list, labels_list

    def create_bags(self, dir_list):
        bag_list = []
        labels_list = []
        for dir in dir_list:
            # Get image name

            img_name = os.path.basename(dir)

            # bmp to pillow
            img_dir = os.path.join(dir, img_name + '.bmp')
            img = io.imread(img_dir)
            if img.shape[2] == 4:
                img = color.rgba2rgb(img)

            if self.location_info:
                xs = np.arange(0, 500)
                xs = np.asarray([xs for i in range(500)])
                ys = xs.transpose()
                img = np.dstack((img, xs, ys))

            # crop malignant cells
            dir_epithelial = os.path.join(dir, img_name + '_epithelial.mat')
            with open(dir_epithelial, 'rb') as f:
                mat_epithelial = scipy.io.loadmat(f)

            cropped_cells_epithelial = []
            for (x, y) in mat_epithelial['detection']:
                x = np.round(x)
                y = np.round(y)

                if self.data_augmentation:
                    x = x + np.round(np.random.normal(0, 3, 1))
                    y = y + np.round(np.random.normal(0, 3, 1))

                if x < 13:
                    x_start = 0
                    x_end = 27
                elif x > 500 - 14:
                    x_start = 500 - 27
                    x_end = 500
                else:
                    x_start = x - 13
                    x_end = x + 14

                if y < 13:
                    y_start = 0
                    y_end = 27
                elif y > 500 - 14:
                    y_start = 500 - 27
                    y_end = 500
                else:
                    y_start = y - 13
                    y_end = y + 14

                cropped_cells_epithelial.append(img[int(y_start):int(y_end), int(x_start):int(x_end)])

            # crop all other cells
            dir_inflammatory = os.path.join(dir, img_name + '_inflammatory.mat')
            dir_fibroblast = os.path.join(dir, img_name + '_fibroblast.mat')
            dir_others = os.path.join(dir, img_name + '_others.mat')

            with open(dir_inflammatory, 'rb') as f:
                mat_inflammatory = scipy.io.loadmat(f)
            with open(dir_fibroblast, 'rb') as f:
                mat_fibroblast = scipy.io.loadmat(f)
            with open(dir_others, 'rb') as f:
                mat_others = scipy.io.loadmat(f)

            all_coordinates = np.concatenate(
                (mat_inflammatory['detection'], mat_fibroblast['detection'], mat_others['detection']), axis=0)

            cropped_cells_others = []
            for (x, y) in all_coordinates:
                x = np.round(x)
                y = np.round(y)

                if self.data_augmentation:
                    x = x + np.round(np.random.normal(0, 3, 1))
                    y = y + np.round(np.random.normal(0, 3, 1))

                if x < 13:
                    x_start = 0
                    x_end = 27
                elif x > 500 - 14:
                    x_start = 500 - 27
                    x_end = 500
                else:
                    x_start = x - 13
                    x_end = x + 14

                if y < 13:
                    y_start = 0
                    y_end = 27
                elif y > 500 - 14:
                    y_start = 500 - 27
                    y_end = 500
                else:
                    y_start = y - 13
                    y_end = y + 14

                cropped_cells_others.append(img[int(y_start):int(y_end), int(x_start):int(x_end)])

            # generate bag
            bag = cropped_cells_epithelial + cropped_cells_others

            # store single cell labels
            labels = np.concatenate((np.ones(len(cropped_cells_epithelial)), np.zeros(len(cropped_cells_others))),
                                    axis=0)

            # shuffle
            if self.shuffle_bag:
                zip_bag_labels = list(zip(bag, labels))
                random.shuffle(zip_bag_labels)
                bag, labels = zip(*zip_bag_labels)

            # append every bag two times if training
            if self.train:
                for _ in [0, 1]:
                    bag_list.append(bag)
                    labels_list.append(labels)
            else:
                bag_list.append(bag)
                labels_list.append(labels)

            # bag_list.append(bag)
            # labels_list.append(labels)

        return bag_list, labels_list

    def transform_and_data_augmentation(self, bag, raw=False):
        if raw:
            img_transform = self.to_tensor_transform
        elif not raw and self.data_augmentation:
            img_transform = self.data_augmentation_img_transform
        else:
            img_transform = self.normalize_to_tensor_transform

        bag_tensors = []
        for img in bag:
            if self.location_info:
                bag_tensors.append(torch.cat(
                    (img_transform(img[:, :, :3].astype('uint8')),
                     torch.from_numpy(img[:, :, 3:].astype(float).transpose((2, 0, 1))).float(),
                     )))
            else:
                bag_tensors.append(img_transform(img))

        return torch.stack(bag_tensors)

    def __len__(self):
        if self.train:
            return len(self.labels_list_train)
        else:
            return len(self.labels_list_test)

    def __getitem__(self, index):
        if self.train:
            bag = self.bag_list_train[index]
            label = max(self.labels_list_train[index])
        else:
            bag = self.bag_list_test[index]
            label = max(self.labels_list_test[index])
        if self.push:
            return self.transform_and_data_augmentation(bag, raw=True), self.transform_and_data_augmentation(
                bag), torch.LongTensor([int(label)])
        else:
            return self.transform_and_data_augmentation(bag), torch.LongTensor([int(label)])
