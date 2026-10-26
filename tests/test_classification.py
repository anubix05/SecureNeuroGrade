"""
Unit tests for SecureNeuroGrade Classification Service (Module M3).
"""

import unittest
from app.models.database_models import RiskLevel
from app.services.classification_service import classify_result, assess_risk


class TestClassificationService(unittest.TestCase):
    """Tests for classification and decision-support risk categorization."""

    def test_classify_tumor_positive_high_confidence(self):
        """Test tumor detection with high confidence yields CRITICAL risk."""
        mock_output = {
            'predicted_class': 'glioma',
            'confidence': 0.94,
            'predictions': {
                'glioma': 0.94,
                'meningioma': 0.03,
                'pituitary': 0.02,
                'no_tumor': 0.01,
            },
            'is_placeholder': False,
            'organ_type': 'brain'
        }
        res = classify_result(mock_output)
        self.assertTrue(res['tumor_detected'])
        self.assertEqual(res['prediction_class'], 'glioma')
        self.assertEqual(res['risk_level'], RiskLevel.CRITICAL)
        self.assertIn('Clinical review recommended', res['summary'])

    def test_classify_no_tumor_high_confidence(self):
        """Test no_tumor detection with high confidence yields LOW risk."""
        mock_output = {
            'predicted_class': 'no_tumor',
            'confidence': 0.96,
            'predictions': {
                'glioma': 0.01,
                'meningioma': 0.01,
                'pituitary': 0.02,
                'no_tumor': 0.96,
            },
            'is_placeholder': False,
            'organ_type': 'brain'
        }
        res = classify_result(mock_output)
        self.assertFalse(res['tumor_detected'])
        self.assertEqual(res['prediction_class'], 'no_tumor')
        self.assertEqual(res['risk_level'], RiskLevel.LOW)

    def test_classify_liver_healthy_class(self):
        """The liver model's Healthy class must not be classified as tumor."""
        mock_output = {
            'predicted_class': 'Healthy',
            'confidence': 0.92,
            'predictions': {'Healthy': 0.92, 'Angiosarcoma': 0.02},
            'is_placeholder': False,
            'organ_type': 'liver',
        }
        res = classify_result(mock_output)
        self.assertFalse(res['tumor_detected'])
        self.assertEqual(res['prediction_class'], 'Healthy')
        self.assertEqual(res['risk_level'], RiskLevel.LOW)

    def test_assess_risk_thresholds(self):
        """Verify the confidence boundaries map accurately to risk levels."""
        self.assertEqual(assess_risk('meningioma', 0.90, tumor_detected=True), RiskLevel.CRITICAL)
        self.assertEqual(assess_risk('meningioma', 0.75, tumor_detected=True), RiskLevel.HIGH)
        self.assertEqual(assess_risk('meningioma', 0.50, tumor_detected=True), RiskLevel.MODERATE)
        self.assertEqual(assess_risk('meningioma', 0.30, tumor_detected=True), RiskLevel.LOW)


if __name__ == "__main__":
    unittest.main()
