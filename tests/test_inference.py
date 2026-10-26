"""Tests for organ-specific model loading and inference."""

import json
import os
import sys
import tempfile
import types
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
from PIL import Image

from app.services import inference_service


LIVER_CLASSES = [
    'Angiosarcoma',
    'Cholangiocarcinoma',
    'Hemangioma',
    'Hepatocellular_Carcinoma',
    'Healthy',
]


class TestInferenceService(unittest.TestCase):
    """Verify liver artifacts use their own config and class mapping."""

    def setUp(self):
        inference_service._MODEL_CACHE.clear()
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.checkpoint_path = os.path.join(self.temp_directory.name, 'liver.keras')
        self.config_path = os.path.join(self.temp_directory.name, 'liver.json')
        with open(self.checkpoint_path, 'wb') as checkpoint_file:
            checkpoint_file.write(b'test checkpoint')
        with open(self.config_path, 'w', encoding='utf-8') as config_file:
            json.dump({'classes': LIVER_CLASSES}, config_file)

    def _loader_patches(self, output_shape):
        fake_model = SimpleNamespace(output_shape=output_shape)
        load_model_mock = Mock(return_value=fake_model)
        fake_keras = types.ModuleType('keras')
        fake_keras.models = SimpleNamespace(load_model=load_model_mock)
        fake_architecture = types.ModuleType('ml.models.brain_tumor.architecture')
        fake_architecture.PositionEmbedding = object
        return load_model_mock, patch.dict(
            sys.modules,
            {
                'keras': fake_keras,
                'ml.models.brain_tumor.architecture': fake_architecture,
            },
        )

    def test_load_model_uses_liver_config_and_custom_layer(self):
        load_model_mock, module_patch = self._loader_patches((None, 5))
        with module_patch, patch.dict(os.environ, {'KERAS_BACKEND': 'tensorflow'}), \
                patch.dict(inference_service.MODEL_PATHS, {
                    'liver': (self.checkpoint_path, self.config_path),
                }):
            self.assertTrue(inference_service.load_model(organ_type='liver'))

        loaded_entry = inference_service._MODEL_CACHE['liver']
        self.assertEqual(loaded_entry['config']['classes'], LIVER_CLASSES)
        self.assertEqual(loaded_entry['path'], self.checkpoint_path)
        custom_objects = load_model_mock.call_args.kwargs['custom_objects']
        self.assertIn('PositionEmbedding', custom_objects)
        self.assertIn('CAFNet>PositionEmbedding', custom_objects)

    def test_load_model_rejects_output_count_mismatch(self):
        _, module_patch = self._loader_patches((None, 4))
        with module_patch, patch.dict(os.environ, {'KERAS_BACKEND': 'tensorflow'}), \
                patch.dict(inference_service.MODEL_PATHS, {
                    'liver': (self.checkpoint_path, self.config_path),
                }):
            self.assertFalse(inference_service.load_model(organ_type='liver'))

        self.assertNotIn('liver', inference_service._MODEL_CACHE)

    def test_run_inference_maps_scores_to_liver_classes(self):
        model = Mock()
        model.predict.return_value = np.array([[0.05, 0.1, 0.15, 0.2, 0.5]])
        model_config = {
            'classes': LIVER_CLASSES,
            'preprocessing': {
                'resize': [224, 224],
                'normalize': True,
                'normalize_range': [0.0, 1.0],
                'color_mode': 'rgb',
            },
        }
        image_path = os.path.join(self.temp_directory.name, 'scan.png')
        Image.new('RGB', (224, 224)).save(image_path)
        model_entry = {'model': model, 'config': model_config, 'path': 'liver.keras'}

        with patch.dict(inference_service._MODEL_CACHE, {'liver': model_entry}, clear=True):
            result = inference_service.run_inference(image_path, organ_type='liver')

        self.assertEqual(list(result['predictions']), LIVER_CLASSES)
        self.assertEqual(result['predicted_class'], 'Healthy')
        self.assertEqual(result['confidence'], 0.5)
        self.assertFalse(result['is_placeholder'])
        self.assertEqual(model.predict.call_args.args[0].shape, (1, 224, 224, 3))

    def test_liver_placeholder_uses_configured_classes(self):
        image_path = os.path.join(self.temp_directory.name, 'scan.png')
        Image.new('RGB', (224, 224)).save(image_path)
        with patch.dict(inference_service.MODEL_PATHS, {
                'liver': (self.checkpoint_path, self.config_path),
        }), patch.object(inference_service, 'load_model', return_value=False):
            result = inference_service.run_inference(image_path, organ_type='liver')

        self.assertEqual(list(result['predictions']), LIVER_CLASSES)
        self.assertTrue(result['is_placeholder'])


if __name__ == '__main__':
    unittest.main()