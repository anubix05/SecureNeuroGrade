from pathlib import Path
import json

import numpy as np
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "ml" / "configs" / "liver_tumor_config.json"


def load_config():
	"""Load the liver model configuration."""
	with CONFIG_PATH.open("r", encoding="utf-8") as file:
		return json.load(file)


def preprocess_image(image_path):
	"""Prepare a liver scan for the trained model."""
	config = load_config()
	width, height = config["preprocessing"]["resize"]

	with Image.open(image_path) as image:
		image = image.convert(config["preprocessing"]["color_mode"].upper())
		image = image.resize((width, height))
		image_array = np.asarray(image, dtype=np.float32)

	if config["preprocessing"]["normalize"]:
		low, high = config["preprocessing"]["normalize_range"]
		image_array = image_array / 255.0 * (high - low) + low

	return np.expand_dims(image_array, axis=0)


def predict_liver_tumor(image_path, model_path):
	"""Run prediction using a trained Keras model.

	The model must be trained for liver images, and its output classes must
	match the configured class order.
	"""
	import tensorflow as tf

	model_file = Path(model_path)
	if not model_file.is_file():
		raise FileNotFoundError(f"Trained model not found: {model_file}")

	model = tf.keras.models.load_model(model_file)
	image_array = preprocess_image(image_path)
	predictions = model.predict(image_array, verbose=0)[0]
	classes = load_config()["classes"]

	if len(predictions) != len(classes):
		raise ValueError("Model output count does not match configured classes.")

	predicted_index = int(np.argmax(predictions))
	return {
		"predicted_class": classes[predicted_index],
		"confidence": float(predictions[predicted_index]),
		"all_scores": {
			name: float(score)
			for name, score in zip(classes, predictions)
		},
	}
