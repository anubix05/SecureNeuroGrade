"""
SecureNeuroGrade — Classification Service (Module M3)
=====================================================
Converts raw model output into structured clinical-support results.

Pipeline position:
    Inference -> [M3 Classification] -> Risk Assessment -> Doctor Dashboard

Keeps the following concepts separate (per AGENTS.md §34):
    raw model output -> classification -> confidence -> risk assessment

IMPORTANT:
    - Confidence is NOT the same as probability of clinical truth
    - All output is decision support, NOT autonomous diagnosis
    - Risk levels are based on confidence thresholds, not clinical evidence
"""

import logging

from app.models.database_models import RiskLevel

logger = logging.getLogger(__name__)

# Confidence thresholds for risk assessment
# These are model-confidence-based thresholds for categorization,
# NOT clinical risk thresholds. They should be calibrated based on
# actual model evaluation metrics.
RISK_THRESHOLDS = {
    'HIGH_CONFIDENCE': 0.85,
    'MODERATE_CONFIDENCE': 0.60,
    'LOW_CONFIDENCE': 0.40,
}


def classify_result(inference_output):
    """
    Process raw inference output into a structured classification result.

    Args:
        inference_output: dict from inference_service.run_inference() with:
            - 'predictions': dict of class -> score
            - 'predicted_class': top class name
            - 'confidence': top confidence score
            - 'is_placeholder': whether this is a placeholder result
            - 'organ_type': organ type analyzed

    Returns:
        dict with:
            - 'prediction_class': the classified tumor type
            - 'confidence_score': model confidence (0.0 to 1.0)
            - 'risk_level': assessed risk level string
            - 'tumor_detected': boolean
            - 'all_predictions': full prediction breakdown
            - 'is_placeholder': whether this used placeholder inference
            - 'summary': human-readable summary for the doctor dashboard
    """
    predicted_class = inference_output['predicted_class']
    confidence = inference_output['confidence']
    all_predictions = inference_output.get('predictions', {})
    is_placeholder = inference_output.get('is_placeholder', False)
    organ_type = inference_output.get('organ_type', 'brain')

    # Determine if a tumor was detected
    tumor_detected = predicted_class.lower() not in ('no_tumor', 'normal', 'healthy')

    # Assess risk level based on confidence and tumor detection
    risk_level = assess_risk(predicted_class, confidence, tumor_detected)

    # Generate human-readable summary
    summary = _generate_summary(
        predicted_class, confidence, risk_level,
        tumor_detected, is_placeholder
    )

    return {
        'prediction_class': predicted_class,
        'confidence_score': confidence,
        'risk_level': risk_level,
        'tumor_detected': tumor_detected,
        'all_predictions': all_predictions,
        'is_placeholder': is_placeholder,
        'organ_type': organ_type,
        'summary': summary,
    }


def assess_risk(predicted_class, confidence, tumor_detected):
    """
    Assess risk level based on prediction and confidence.

    This is a model-confidence-based categorization, NOT a clinical
    risk assessment. The risk levels help prioritize doctor review.

    Args:
        predicted_class: The predicted tumor class.
        confidence: The model confidence score (0.0 to 1.0).
        tumor_detected: Whether a tumor was detected.

    Returns:
        str: One of RiskLevel constants.
    """
    if not tumor_detected:
        # No tumor detected — risk is based on how confident the model is
        if confidence >= RISK_THRESHOLDS['HIGH_CONFIDENCE']:
            return RiskLevel.LOW
        else:
            # Lower confidence in "no tumor" means higher uncertainty
            return RiskLevel.MODERATE

    # Tumor detected — higher confidence in tumor = higher clinical priority
    if confidence >= RISK_THRESHOLDS['HIGH_CONFIDENCE']:
        return RiskLevel.CRITICAL
    elif confidence >= RISK_THRESHOLDS['MODERATE_CONFIDENCE']:
        return RiskLevel.HIGH
    elif confidence >= RISK_THRESHOLDS['LOW_CONFIDENCE']:
        return RiskLevel.MODERATE
    else:
        return RiskLevel.LOW


def _generate_summary(predicted_class, confidence, risk_level,
                      tumor_detected, is_placeholder):
    """
    Generate a human-readable summary for doctor display.

    Uses careful language to avoid implying the AI is making a
    definitive diagnosis (per AGENTS.md §5).
    """
    placeholder_note = ''
    if is_placeholder:
        placeholder_note = (
            ' [PLACEHOLDER: This result was generated without a trained '
            'model and is not a real prediction.]'
        )

    if tumor_detected:
        summary = (
            f'Model prediction: {predicted_class}, '
            f'confidence: {confidence:.1%}. '
            f'Risk level: {risk_level}. '
            f'Clinical review recommended.'
            f'{placeholder_note}'
        )
    else:
        summary = (
            f'Model prediction: No tumor detected, '
            f'confidence: {confidence:.1%}. '
            f'Risk level: {risk_level}.'
            f'{placeholder_note}'
        )

    return summary
