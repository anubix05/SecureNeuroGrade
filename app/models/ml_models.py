"""
SecureNeuroGrade — ML Model Utilities
=====================================
Model registry and loading utilities for the inference pipeline.

Designed for multi-organ extensibility: new organ models can be
registered without modifying core inference logic.

Note: Actual model loading (TensorFlow/PyTorch) will be implemented
when the trained model checkpoint is available.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Registry for managing ML model configurations and loading.

    Supports multiple organ types and model versions. The active model
    for each organ type is determined by the ModelVersion database record
    with is_active=True.

    Example config (ml/configs/brain_tumor_config.json):
        {
            "organ_type": "brain",
            "model_name": "brain-tumor-cnn",
            "input_shape": [224, 224, 3],
            "classes": ["glioma", "meningioma", "pituitary", "no_tumor"],
            "preprocessing": { ... }
        }
    """

    def __init__(self, config_dir=None):
        """
        Args:
            config_dir: Path to the ML config directory.
                        Defaults to ml/configs/ relative to project root.
        """
        if config_dir is None:
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            config_dir = os.path.join(project_root, 'ml', 'configs')

        self.config_dir = config_dir
        self._configs = {}
        self._models = {}

    def load_config(self, organ_type):
        """
        Load the model configuration for a given organ type.

        Args:
            organ_type: e.g., 'brain', 'lung', 'liver'

        Returns:
            dict with model configuration, or None if not found.
        """
        if organ_type in self._configs:
            return self._configs[organ_type]

        # 1. Primary: check disease-sorted folder structure under ml/models/<organ>_tumor/config.json
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        disease_folder = f'{organ_type}_tumor' if not organ_type.endswith('_tumor') else organ_type
        disease_config_path = os.path.join(project_root, 'ml', 'models', disease_folder, 'config.json')

        # 2. Fallback: check ml/configs/<organ>_tumor_config.json
        fallback_config_path = os.path.join(self.config_dir, f'{organ_type}_tumor_config.json')

        config_path = disease_config_path if os.path.exists(disease_config_path) else fallback_config_path

        if not os.path.exists(config_path):
            logger.warning(
                'No model config found for organ type: %s (checked %s and %s)',
                organ_type, disease_config_path, fallback_config_path
            )
            return None

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            self._configs[organ_type] = config
            logger.info('Loaded model config for organ type %s from %s', organ_type, config_path)
            return config
        except (json.JSONDecodeError, OSError) as e:
            logger.error(
                'Failed to load model config for %s: %s', organ_type, e
            )
            return None

    def get_classes(self, organ_type):
        """Get the list of prediction classes for an organ type."""
        config = self.load_config(organ_type)
        if config is None:
            return []
        return config.get('classes', [])

    def get_input_shape(self, organ_type):
        """Get the expected input shape for an organ type's model."""
        config = self.load_config(organ_type)
        if config is None:
            return None
        return config.get('input_shape')


# Module-level singleton
model_registry = ModelRegistry()
