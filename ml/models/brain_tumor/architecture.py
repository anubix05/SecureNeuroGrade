"""
SecureNeuroGrade — Brain Tumor Model Architecture
===================================================
CNN model architecture for brain tumor classification (Glioma, Meningioma, Pituitary, No Tumor).

Pipeline Position:
    ml/models/brain_tumor/architecture.py -> Checkpoint Loading -> Inference Service
"""

import logging

logger = logging.getLogger(__name__)

# Model input parameters
INPUT_SHAPE = (224, 224, 3)
NUM_CLASSES = 4
CLASSES = ['glioma', 'meningioma', 'pituitary', 'no_tumor']


# Setup Keras / TensorFlow registration for CAFNet custom layers
try:
    import keras
    from keras import layers, models
    _register_serializable = keras.saving.register_keras_serializable(package='CAFNet')
except Exception:
    try:
        import tensorflow as tf
        from tensorflow.keras import layers, models
        _register_serializable = tf.keras.utils.register_keras_serializable(package='CAFNet')
    except Exception:
        layers = None
        models = None
        def _register_serializable(cls):
            return cls


if layers is not None:
    @_register_serializable
    class PositionEmbedding(layers.Layer):
        """
        Learnable 1D positional embedding for patch tokens in CAFNet.
        Matches architecture defined in train_brain_tumorFixed.ipynb and cafnet_seminar.pptx.
        """
        def __init__(self, num_patches=196, projection_dim=128, **kwargs):
            super().__init__(**kwargs)
            self.num_patches = num_patches
            self.projection_dim = projection_dim

        def build(self, input_shape):
            self.pos_emb = self.add_weight(
                name='pos_emb',
                shape=(1, self.num_patches, self.projection_dim),
                initializer='zeros',
                trainable=True,
            )
            super().build(input_shape)

        def call(self, x):
            return x + self.pos_emb

        def get_config(self):
            config = super().get_config()
            config.update({
                'num_patches': self.num_patches,
                'projection_dim': self.projection_dim,
            })
            return config
else:
    class PositionEmbedding:
        pass


def build_cafnet_model(
    input_shape=INPUT_SHAPE,
    num_classes=NUM_CLASSES,
    patch_size=16,
    projection_dim=128,
    num_heads=4,
    transformer_layers=2,
    mlp_dim=256
):
    """
    Constructs CAFNet: Hybrid CNN-ViT Framework with Cross-Attention Fusion.
    Reference: Jayaraman et al., Scientific Reports 15:45769 (2025) / cafnet_seminar.pptx
    """
    if models is None or layers is None:
        logger.info("Keras/TensorFlow not installed — returning placeholder architecture.")
        return None

    try:
        from tensorflow.keras.applications import EfficientNetB0
    except ImportError:
        try:
            from keras.applications import EfficientNetB0
        except ImportError:
            EfficientNetB0 = None

    inputs = layers.Input(shape=input_shape, name="mri_input")

    # CNN Branch
    cnn_in = layers.Rescaling(255.0, name="cnn_rescaling")(inputs)
    if EfficientNetB0 is not None:
        base_cnn = EfficientNetB0(weights=None, include_top=False, input_shape=input_shape)
        cnn_feat = base_cnn(cnn_in)
    else:
        cnn_feat = layers.Conv2D(1280, (7, 7), activation="relu", padding="same")(cnn_in)

    cnn_proj = layers.Conv2D(projection_dim, kernel_size=1, padding="same", name="cnn_proj_1x1")(cnn_feat)
    cnn_tokens = layers.Reshape((49, projection_dim), name="cnn_spatial_tokens")(cnn_proj)
    cnn_tokens = layers.LayerNormalization(epsilon=1e-6, name="cnn_token_norm")(cnn_tokens)

    # ViT Branch
    num_patches = (input_shape[0] // patch_size) * (input_shape[1] // patch_size)
    vit_patches = layers.Conv2D(
        filters=projection_dim,
        kernel_size=patch_size,
        strides=patch_size,
        padding="valid",
        name="vit_patch_proj"
    )(inputs)
    vit_tokens = layers.Reshape((num_patches, projection_dim), name="vit_tokens_flat")(vit_patches)
    vit_x = PositionEmbedding(num_patches=num_patches, projection_dim=projection_dim, name="vit_pos_embed")(vit_tokens)

    for i in range(transformer_layers):
        norm_sa = layers.LayerNormalization(epsilon=1e-6, name=f"vit_norm_sa_{i+1}")(vit_x)
        sa = layers.MultiHeadAttention(
            num_heads=num_heads,
            key_dim=projection_dim // num_heads,
            name=f"vit_self_attn_{i+1}"
        )(norm_sa, norm_sa)
        vit_x = layers.Add(name=f"vit_res_sa_{i+1}")([sa, vit_x])

        norm_ffn = layers.LayerNormalization(epsilon=1e-6, name=f"vit_norm_ffn_{i+1}")(vit_x)
        ffn = layers.Dense(mlp_dim, activation="gelu", name=f"vit_ffn1_{i+1}")(norm_ffn)
        ffn = layers.Dropout(0.1, name=f"vit_drop_{i+1}")(ffn)
        ffn = layers.Dense(projection_dim, name=f"vit_ffn2_{i+1}")(ffn)
        vit_x = layers.Add(name=f"vit_res_ffn_{i+1}")([ffn, vit_x])

    vit_global = layers.LayerNormalization(epsilon=1e-6, name="vit_global_norm")(vit_x)

    # Cross-Attention Fusion (CAF)
    caf_cross_attn = layers.MultiHeadAttention(
        num_heads=num_heads,
        key_dim=projection_dim // num_heads,
        name="caf_cross_attention"
    )(query=vit_global, key=cnn_tokens, value=cnn_tokens)

    caf_x = layers.Add(name="caf_res_cross")([caf_cross_attn, vit_global])
    caf_x = layers.LayerNormalization(epsilon=1e-6, name="caf_norm_cross")(caf_x)

    caf_ffn = layers.Dense(mlp_dim, activation="gelu", name="caf_ffn_dense1")(caf_x)
    caf_ffn = layers.Dropout(0.2, name="caf_ffn_drop")(caf_ffn)
    caf_ffn = layers.Dense(projection_dim, name="caf_ffn_dense2")(caf_ffn)
    caf_fused = layers.Add(name="caf_res_ffn")([caf_ffn, caf_x])
    caf_fused = layers.LayerNormalization(epsilon=1e-6, name="caf_norm_fused")(caf_fused)

    # Classification Head
    fused_pool = layers.GlobalAveragePooling1D(name="caf_gap_1d")(caf_fused)
    cnn_pool = layers.GlobalAveragePooling2D(name="cnn_gap_2d")(cnn_feat)
    cnn_pool_proj = layers.Dense(projection_dim, activation="relu", name="cnn_pool_proj")(cnn_pool)

    combined = layers.Concatenate(name="fusion_concat")([fused_pool, cnn_pool_proj])

    x = layers.Dense(128, activation="relu", name="head_dense")(combined)
    x = layers.BatchNormalization(name="head_bn")(x)
    x = layers.Dropout(0.3, name="head_dropout")(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="probs")(x)

    model = models.Model(inputs=inputs, outputs=outputs, name="SecureNeuroGrade_BrainTumor_CAFNet")
    return model


def build_brain_tumor_model(input_shape=INPUT_SHAPE, num_classes=NUM_CLASSES):
    """
    Construct CNN baseline architecture for brain tumor classification.
    """
    if models is None or layers is None:
        logger.info("TensorFlow/Keras not installed — returning placeholder architecture.")
        return None

    model = models.Sequential([
        layers.Input(shape=input_shape),
        layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),

        layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),

        layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),

        layers.Flatten(),
        layers.Dense(256, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation='softmax')
    ])
    logger.info("Successfully constructed TensorFlow Keras Brain Tumor CNN model.")
    return model

