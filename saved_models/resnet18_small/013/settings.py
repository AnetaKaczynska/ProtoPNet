base_architecture = 'resnet18_small'
img_size = 28
prototype_shape = (10, 512, 1, 1)
num_classes = 2
prototype_activation_function = 'log'
add_on_layers_type = 'regular'

experiment_run = '013'

data_path = 'data/'
train_dir = data_path + 'train_cropped_augmented/'
test_dir = data_path + 'bagged/test/'
train_push_dir = data_path + 'train_cropped/'
train_batch_size = 1
test_batch_size = 1
train_push_batch_size = 1

joint_optimizer_lrs = {
    'features': 1e-4,
    'add_on_layers': 3e-3,
    'prototype_vectors': 3e-3
}
joint_lr_step_size = 5

warm_optimizer_lrs = {
    'add_on_layers': 3e-3,
    'prototype_vectors': 3e-3
}

last_layer_optimizer_lr = 1e-4

coefs = {
    'crs_ent': 1,
    'clst': 0.8,
    'sep': -0.08,
    'l1': 1e-4,
}

num_train_epochs = 31
num_warm_epochs = 1

push_start = 10
push_epochs = [i for i in range(num_train_epochs) if i % 10 == 0]
