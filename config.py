class Config:
    data_path = "/Users/jyon/Gatech/6240/Project1/GalaxyGAN_python"
    model_path = "" #"./datasets/facades/checkpoint/model_100.ckpt"
    output_path = "/Users/jyon/Gatech/6240/Project1/GalaxyGAN_python/output"

    img_size = 424
    adjust_size = 500
    train_size = 424
    img_channel = 3
    conv_channel_base = 64

    learning_rate = 0.02
    beta1 = 0.5
    max_epoch = 6
    L1_lambda = 100
    save_per_epoch=1
