import albumentations as A
from albumentations.pytorch import ToTensorV2
import torch.nn as nn
import torch.optim as optim
import torch
from data.datasets.oil_environment_dataset import get_loaders, OilEnvironmentDatasetClassificationAndEstimation
from model.unet_model_cascaded import SemanticSegmentationCascadedModel, DiceLoss
from model.unet_model import UNET
from model.unet_model_classification import UNETClassifier
from data.datasets.datasets_helpers import get_mean_and_std, get_max
from torch.utils.tensorboard import SummaryWriter

# Parameters
# ==================================================================================================================
LEARNING_RATE_COMBINED = 8e-4
LEARNING_RATE_ESTIMATOR = 1e-3
LEARNING_RATE_CLASSIFIER = 2e-4
DEVICE = "cpu"
COMPUTE_MEAN_AND_STD = False
NORMALIZE = True
BATCH_SIZE = 10
NUM_EPOCHS = 10
NUM_WORKERS = 0
IMAGE_HEIGHT = 80  # 1280 originally
IMAGE_WIDTH = 80  # 1918 originally
PIN_MEMORY = False
LOAD_MODEL_FROM_CHECKPOINT = False
SAVE = False
LOAD = True
COMBINED_LOSS = True
SAVE_PREDICTION_IMAGES = False
EVALUATE_METRICS = True
MODEL_CHECKPOINT = "my_checkpoint2.pth.tar"
TRAIN_IMG_DIR = "assets/generated_data/variance_0.02_windspeed_8/fluids_cascaded_9freq/training"
VAL_IMG_DIR = "assets/generated_data/variance_0.02_windspeed_8/fluids_cascaded_9freq/validation"
PRED_IMG_DIR = "assets/generated_data/variance_0.02_windspeed_8/fluids_cascaded_9freq/pred"
CLASSIFIER_MODEL_PATH = 'assets/generated_models/unet_highvariance_windspeed_8_cascaded_normalized_classifier_unified_loss_10epochs_9freq_lr8e-4.pkl'
ESTIMATOR_MODEL_PATH = 'assets/generated_models/unet_highvariance_windspeed_8_cascaded_normalized_estimator_unified_loss_10epochs_9freq_lr8e-4.pkl'
NUMBER_OF_FEATURES = 9
# ==================================================================================================================
writer = SummaryWriter("assets/logs/unet_highvariance_windspeed_8_cascaded_normalized_unified_loss_10epoch_9freq_lr8e-4")

classifier = UNETClassifier(in_channels=NUMBER_OF_FEATURES, out_channels=1, normalize_output=True, features=[64, 128, 256, 512]).to(
    DEVICE)
estimator = UNET(in_channels=NUMBER_OF_FEATURES+1, out_channels=11, normalize_output=False, features=[32, 64, 128, 256, 512]).to(
    DEVICE)
cascaded_model = SemanticSegmentationCascadedModel(classifier=classifier,
                                                   estimator=estimator)
train_transform = []
val_transform = []


if not COMPUTE_MEAN_AND_STD and NORMALIZE:
    # Variance 0.02
    # mean = [0.4678, 0.4022, 0.4325, 0.4570]
    # std = [0.1877, 0.1894, 0.1965, 0.1972]


    # Variance 0.02 Windspeed 8 - 17 freq
    # mean = [0.5395, 0.5235, 0.5126, 0.5078, 0.5045, 0.5041, 0.5041, 0.5045, 0.5033,
    #     0.5033, 0.5006, 0.4939, 0.4886, 0.4812, 0.4713, 0.4614, 0.4491]
    # std = [0.1906, 0.1972, 0.1983, 0.1949, 0.1925, 0.1906, 0.1885, 0.1875, 0.1870,
    #     0.1861, 0.1854, 0.1835, 0.1826, 0.1805, 0.1796, 0.1830, 0.1854]

    # Variance 0.02 Windspeed 8 - 9 freq
    mean = [0.5410, 0.5144, 0.5050, 0.5052, 0.5038, 0.4999, 0.4904, 0.4743, 0.4515]
    std = [0.1906, 0.1978, 0.1927, 0.1887, 0.1871, 0.1842, 0.1811, 0.1793, 0.1853]

    train_transform = A.Compose(
        [
            A.Normalize(
                mean=mean,
                std=std,
                max_pixel_value=1,
            )
        ],
        additional_targets={'mask1': 'mask',
                            'mask2': 'mask', }
    )
    val_transform = A.Compose(
        [
            A.Normalize(
                mean=mean,
                std=std,
                max_pixel_value=1,
            )
        ],
        additional_targets={'mask1': 'mask',
                            'mask2': 'mask', }
    )


# Set criterion
criterion_classifier = DiceLoss()
criterion_estimator = nn.CrossEntropyLoss()
# Set optimizers
opt_classifier = optim.Adam(classifier.parameters(), lr=LEARNING_RATE_CLASSIFIER)
opt_estimator = optim.Adam(estimator.parameters(), lr=LEARNING_RATE_ESTIMATOR)
opt_all = optim.Adam([
    {'params': classifier.parameters()},
    {'params': estimator.parameters()}
], lr=LEARNING_RATE_COMBINED)

train_loader, val_loader = get_loaders(
    TRAIN_IMG_DIR,
    VAL_IMG_DIR,
    BATCH_SIZE,
    train_transform,
    val_transform,
    OilEnvironmentDatasetClassificationAndEstimation,
    NUM_WORKERS,
    PIN_MEMORY,
)

if COMPUTE_MEAN_AND_STD:
    print(f"Training dataset mean and std {get_mean_and_std(train_loader)}")
    print(f"Validation dataset mean and std {get_mean_and_std(val_loader)}")
    print(f"Training dataset max {get_max(train_loader)}")
    print(f"Validation dataset max  {get_max(val_loader)}")

    exit()


def _evaluate_model(save_images=True):
    if EVALUATE_METRICS:
        cascaded_model.evaluate_metrics(val_loader, device=DEVICE)
    if SAVE_PREDICTION_IMAGES and save_images:
        cascaded_model.save_predictions_as_images(
            val_loader, folder=PRED_IMG_DIR, device=DEVICE
        )

if not LOAD:
    classifier.train()
    estimator.train()
    with torch.autograd.set_detect_anomaly(True):
        for epoch in range(NUM_EPOCHS):
            print(f"Starting epoch {epoch}")
            cascaded_model.train_fn(loader=train_loader,
                                    opt_classifier=opt_classifier,
                                    opt_estimator=opt_estimator,
                                    criterion_estimator=criterion_estimator,
                                    criterion_classifier=criterion_classifier,
                                    combined_loss=COMBINED_LOSS,
                                    summary_writer=writer,
                                    opt_all=opt_all,
                                    device=DEVICE)

            # # save model
            # checkpoint = {
            #     "state_dict": model.state_dict(),
            #     "optimizer": optimizer.state_dict(),
            # }
            # save_checkpoint(checkpoint)

            _evaluate_model(save_images=False)

        writer.flush()
        # Final evaluation
        _evaluate_model()



else:
    classifier = torch.load(CLASSIFIER_MODEL_PATH)
    estimator = torch.load(ESTIMATOR_MODEL_PATH)
    cascaded_model = SemanticSegmentationCascadedModel(classifier=classifier,
                                                       estimator=estimator)
    _evaluate_model()

if SAVE:
    torch.save(cascaded_model.classifier, CLASSIFIER_MODEL_PATH)
    torch.save(cascaded_model.estimator, ESTIMATOR_MODEL_PATH)
