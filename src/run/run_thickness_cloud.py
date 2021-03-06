from data.data_loader import DataLoader
from visualization import points_cloud
from model.nn_model import NNModel

# Parameters
# ==================================================================================================================
FILE_NAME = 'thickness-smallstep_9freqs-variance0.001-'
MODEL_NAME = 'WITHOUT0-nn-v13-2outputs-thickness-9freqs-variance0.001-10000'
THICKNESS_INDEX = 1
PERMITTIVITY_INDEX = 0
NEW_MODEL = False

network_layers = [
    ["Input", 9],
    ["Dense", 12, "relu"],
    ["Dense", 16, "relu"],
    ["Dense", 12, "relu"],
    ["Dense", 2, "linear"]
]
# ==================================================================================================================

loader = DataLoader()
loader.load_data_from_file(
    file_name=f"generated_data/{FILE_NAME}",
    file_format="{}permittivity{}-{}.txt",
    possible_output_values=[(2.8, 3.3, 0.1), (1, 10, 0.1)],
    max_number_of_rows=1000)

model = NNModel(data_loader=loader, network_layers=network_layers, loss='mean_squared_error', print_summary=True)
model.load_model_data(test_size=0.2, is_classification_problem=False, normalize_output=False)
if NEW_MODEL:
    model.train_model(output_file_name=MODEL_NAME, save_file=True, epochs=15)
else:
    model.load_model(f"generated_models/{MODEL_NAME}")

save_figs = True

observed_values = model.y_test[:, THICKNESS_INDEX]
predicted_values = model.y_pred[:, THICKNESS_INDEX]
points_cloud.plot_cloud(observed_values, predicted_values, save_fig=True, output_file_name="ThicknessCloud")
