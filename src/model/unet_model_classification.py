from model.base_image_segmentation_model import ImageSegmentationModel


class UNETClassifier(ImageSegmentationModel):

    def __init__(
            self, in_channels=3, out_channels=1, features=[64, 128, 256, 512], normalize_output=False
    ):
        super().__init__(in_channels, out_channels, features, normalize_output)

    def process_prediction(self, predictions):
        predictions = predictions.squeeze()
        return predictions
