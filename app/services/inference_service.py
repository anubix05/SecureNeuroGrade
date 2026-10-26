"""
SecureNeuroGrade — Inference Service
====================================
Loads the trained ML model and runs inference on validated scans.

Pipeline position:
    Upload -> Encrypt -> Decrypt -> Quality Check -> [Inference] -> Classify

IMPORTANT (per AGENTS.md §12.2):
    - Training code is SEPARATE from inference code
    - Production code loads a trained model/checkpoint
    - Models are NEVER trained during a web request

Models are loaded per organ from their configured checkpoints. If a
checkpoint cannot be loaded, results are clearly labeled as placeholders.
"""

import json
import logging
import os

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

_MODEL_CACHE = {}

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DEFAULT_BRAIN_CHECKPOINT = os.path.join(
    PROJECT_ROOT,
    'ml', 'models', 'brain_tumor', 'checkpoints', 'brain_tumor_model.keras'
)
DEFAULT_BRAIN_CONFIG = os.path.join(
    PROJECT_ROOT,
    'ml', 'models', 'brain_tumor', 'config.json'
)
DEFAULT_LIVER_CHECKPOINT = os.path.join(
    PROJECT_ROOT, 'ml', 'models', 'liver_tumor', 'liver_model.keras'
)
DEFAULT_LIVER_CONFIG = os.path.join(
    PROJECT_ROOT, 'ml', 'configs', 'liver_tumor_config.json'
)
MODEL_PATHS = {
    'brain': (DEFAULT_BRAIN_CHECKPOINT, DEFAULT_BRAIN_CONFIG),
    'liver': (DEFAULT_LIVER_CHECKPOINT, DEFAULT_LIVER_CONFIG),
}


def load_model(checkpoint_path=None, organ_type='brain'):
    """
    Load a trained model checkpoint and its configuration.

    Args:
        checkpoint_path: Path to the model checkpoint file (.keras).
        organ_type: The organ type (e.g., 'brain', 'lung').

    Returns:
        True if the model was loaded successfully, False otherwise.
    """
    organ_type = organ_type.lower()
    if organ_type not in MODEL_PATHS:
        logger.warning('No model registered for organ_type=%s', organ_type)
        return False

    default_checkpoint, config_path = MODEL_PATHS[organ_type]
    checkpoint_path = checkpoint_path or default_checkpoint
    cached_model = _MODEL_CACHE.get(organ_type)
    if cached_model and cached_model['path'] == checkpoint_path:
        return True

    try:
        with open(config_path, 'r', encoding='utf-8') as config_file:
            model_config = json.load(config_file)
        classes = model_config.get('classes', [])
        if not classes:
            raise ValueError('Model configuration must define output classes.')
    except (OSError, json.JSONDecodeError, ValueError) as error:
        logger.error('Could not load model config for %s: %s', organ_type, error)
        return False

    if not os.path.isfile(checkpoint_path):
        logger.warning('Model checkpoint not found for %s: %s', organ_type, checkpoint_path)
        return False

    try:
        if 'KERAS_BACKEND' not in os.environ:
            os.environ['KERAS_BACKEND'] = 'tensorflow'
        import keras

        custom_objects = {}
        try:
            from ml.models.brain_tumor.architecture import PositionEmbedding
            custom_objects = {
                'PositionEmbedding': PositionEmbedding,
                'CAFNet>PositionEmbedding': PositionEmbedding,
            }
        except Exception as error:
            logger.debug('Could not import PositionEmbedding: %s', error)

        model = keras.models.load_model(
            checkpoint_path, custom_objects=custom_objects, compile=False
        )
        output_shape = model.output_shape
        if isinstance(output_shape, list) or output_shape[-1] != len(classes):
            raise ValueError(
                f'Model output count does not match configured classes for {organ_type}.'
            )
    except Exception as error:
        logger.error('Failed to load model for %s: %s', organ_type, error)
        _MODEL_CACHE.pop(organ_type, None)
        return False

    _MODEL_CACHE[organ_type] = {
        'model': model,
        'config': model_config,
        'path': checkpoint_path,
    }
    logger.info('Loaded %s model from %s', organ_type, checkpoint_path)
    return True


def run_inference(image_path, organ_type='brain'):
    """
    Run inference on a preprocessed scan image.

    Args:
        image_path: Path to the preprocessed image file.
        organ_type: The organ type being analyzed.

    Returns:
        dict with:
            - 'predictions': dict mapping class names to confidence scores
            - 'predicted_class': the top prediction class name
            - 'confidence': the top prediction confidence score
            - 'is_placeholder': True if using mock results
            - 'organ_type': the organ type analyzed

    Raises:
        FileNotFoundError: If the image file doesn't exist.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f'Image not found: {image_path}')

    organ_type = organ_type.lower()
    if organ_type not in _MODEL_CACHE:
        load_model(organ_type=organ_type)

    model_entry = _MODEL_CACHE.get(organ_type)
    if model_entry is None:
        return _run_placeholder_inference(image_path, organ_type)
    return _run_real_inference(image_path, organ_type, model_entry)


def _preprocess_image(image_path, target_size=(224, 224), preprocessing=None):
    """Preprocess MRI image for neural network input."""
    preprocessing = preprocessing or {}
    color_mode = preprocessing.get('color_mode', 'rgb').upper()
    img = Image.open(image_path).convert('RGB')
    img = img.resize(target_size, Image.Resampling.BILINEAR)
    arr = np.array(img, dtype=np.float32) / 255.0
    if preprocessing.get('normalize', True):
        low, high = preprocessing.get('normalize_range', [0.0, 1.0])
        arr = arr * (high - low) + low
    elif color_mode != 'RGB':
        logger.warning('Only RGB model input is currently supported.')
    # Add batch dimension: (1, 224, 224, 3)
    return np.expand_dims(arr, axis=0)


def _run_real_inference(image_path, organ_type, model_entry):
    """
    Run inference using the loaded model checkpoint.
    """
    model = model_entry['model']
    model_config = model_entry['config']
    classes = model_config['classes']
    target_size = (224, 224)
    preprocessing = model_config.get('preprocessing', {})
    target_size = tuple(preprocessing.get('resize', target_size))

    input_arr = _preprocess_image(
        image_path, target_size=target_size, preprocessing=preprocessing
    )
    raw_preds = np.asarray(model.predict(input_arr, verbose=0))
    if raw_preds.ndim != 2 or raw_preds.shape[0] != 1:
        raise ValueError('Model returned an unexpected prediction shape.')
    raw_preds = raw_preds[0]
    if len(raw_preds) != len(classes):
        raise ValueError('Model output count does not match configured classes.')

    predictions = {cls: float(raw_preds[index]) for index, cls in enumerate(classes)}
    predicted_class = max(predictions, key=predictions.get)
    confidence = float(predictions[predicted_class])

    return {
        'predictions': predictions,
        'predicted_class': predicted_class,
        'confidence': confidence,
        'is_placeholder': False,
        'organ_type': organ_type,
    }


def _run_placeholder_inference(image_path, organ_type):
    """
    Return placeholder results when no checkpoint is present.
    """
    classes = (
        ['glioma', 'meningioma', 'pituitary', 'no_tumor']
        if organ_type == 'brain'
        else ['tumor_detected', 'no_tumor']
    )
    model_paths = MODEL_PATHS.get(organ_type)
    if model_paths:
        try:
            with open(model_paths[1], 'r', encoding='utf-8') as config_file:
                configured_classes = json.load(config_file).get('classes', [])
            if configured_classes:
                classes = configured_classes
        except (OSError, json.JSONDecodeError) as error:
            logger.warning('Could not load placeholder classes for %s: %s', organ_type, error)

    seed = hash(os.path.basename(image_path)) % (2**32)
    rng = np.random.RandomState(seed)
    raw_scores = rng.dirichlet(np.ones(len(classes)))
    predictions = {cls: float(score) for cls, score in zip(classes, raw_scores)}

    predicted_class = max(predictions, key=predictions.get)
    confidence = predictions[predicted_class]

    return {
        'predictions': predictions,
        'predicted_class': predicted_class,
        'confidence': confidence,
        'is_placeholder': True,
        'organ_type': organ_type,
    }
