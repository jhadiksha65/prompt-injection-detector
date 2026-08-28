"""
Transformer Classifier

Small Transformer Encoder for binary prompt-injection detection.

Input:
    input_ids       [batch_size, sequence_length]
    attention_mask  [batch_size, sequence_length]

Output:
    logits          [batch_size]

Labels:
    0 = Benign
    1 = Malicious
"""

import torch
import torch.nn as nn


class PromptInjectionTransformer(nn.Module):
    """
    Lightweight Transformer Encoder for prompt-injection detection.
    """

    def __init__(
        self,
        vocab_size=24249,
        max_sequence_length=128,
        embedding_dim=128,
        num_heads=4,
        num_layers=2,
        feedforward_dim=256,
        dropout=0.2,
    ):
        super().__init__()

        self.vocab_size = vocab_size
        self.max_sequence_length = max_sequence_length
        self.embedding_dim = embedding_dim

        # ----------------------------------------------------
        # Token embedding
        # ----------------------------------------------------

        self.embedding = nn.Embedding(
            num_embeddings=vocab_size,
            embedding_dim=embedding_dim,
            padding_idx=0,
        )

        # ----------------------------------------------------
        # Positional embedding
        # ----------------------------------------------------

        self.position_embedding = nn.Embedding(
            num_embeddings=max_sequence_length,
            embedding_dim=embedding_dim,
        )

        # ----------------------------------------------------
        # Transformer encoder
        # ----------------------------------------------------

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embedding_dim,
            nhead=num_heads,
            dim_feedforward=feedforward_dim,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )

        self.encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers,
        )

        # ----------------------------------------------------
        # Classification head
        # ----------------------------------------------------

        self.dropout = nn.Dropout(dropout)

        self.classifier = nn.Linear(
            embedding_dim,
            1,
        )

    def forward(self, input_ids, attention_mask):
        """
        Forward pass.

        Args:
            input_ids:
                Tensor of shape [batch_size, sequence_length]

            attention_mask:
                Tensor of shape [batch_size, sequence_length]
                1 = real token
                0 = padding

        Returns:
            logits:
                Tensor of shape [batch_size]
        """

        batch_size, sequence_length = input_ids.shape

        if sequence_length > self.max_sequence_length:
            raise ValueError(
                f"Sequence length {sequence_length} exceeds "
                f"maximum supported length "
                f"{self.max_sequence_length}."
            )

        # ----------------------------------------------------
        # Position IDs
        # ----------------------------------------------------

        position_ids = torch.arange(
            sequence_length,
            device=input_ids.device,
        ).unsqueeze(0).expand(batch_size, -1)

        # ----------------------------------------------------
        # Token + positional embeddings
        # ----------------------------------------------------

        x = (
            self.embedding(input_ids)
            + self.position_embedding(position_ids)
        )

        # ----------------------------------------------------
        # Transformer encoder
        # ----------------------------------------------------

        # Transformer expects True for positions that should
        # be ignored. Our attention_mask uses:
        # 1 = real token
        # 0 = padding
        padding_mask = attention_mask == 0

        x = self.encoder(
            x,
            src_key_padding_mask=padding_mask,
        )

        # ----------------------------------------------------
        # Masked mean pooling
        # ----------------------------------------------------

        mask = attention_mask.unsqueeze(-1).float()

        masked_x = x * mask

        token_count = mask.sum(
            dim=1
        ).clamp(min=1.0)

        pooled = masked_x.sum(
            dim=1
        ) / token_count

        # ----------------------------------------------------
        # Classification
        # ----------------------------------------------------

        pooled = self.dropout(pooled)

        logits = self.classifier(
            pooled
        ).squeeze(-1)

        return logits


def create_model(vocab_size=24249):
    """
    Create the default Transformer Classification model.
    """

    return PromptInjectionTransformer(
        vocab_size=vocab_size,
        max_sequence_length=128,
        embedding_dim=128,
        num_heads=4,
        num_layers=2,
        feedforward_dim=256,
        dropout=0.2,
    )


if __name__ == "__main__":

    print("=" * 60)
    print("PROMPT INJECTION DETECTOR - TRANSFORMER MODEL TEST")
    print("=" * 60)

    # Create model
    model = create_model()

    # Count parameters
    total_parameters = sum(
        p.numel()
        for p in model.parameters()
    )

    trainable_parameters = sum(
        p.numel()
        for p in model.parameters()
        if p.requires_grad
    )

    print(f"Total parameters:      {total_parameters:,}")
    print(f"Trainable parameters:  {trainable_parameters:,}")

    # Dummy batch
    batch_size = 4
    sequence_length = 128

    input_ids = torch.randint(
        low=0,
        high=24249,
        size=(batch_size, sequence_length),
    )

    attention_mask = torch.ones(
        batch_size,
        sequence_length,
        dtype=torch.long,
    )

    # Add some padding to demonstrate mask handling
    attention_mask[0, 20:] = 0
    input_ids[0, 20:] = 0

    attention_mask[1, 50:] = 0
    input_ids[1, 50:] = 0

    # Forward pass
    logits = model(
        input_ids,
        attention_mask,
    )

    print("\nInput shape:")
    print(f"  input_ids: {tuple(input_ids.shape)}")

    print("\nOutput shape:")
    print(f"  logits:    {tuple(logits.shape)}")

    print("\nSample logits:")
    print(logits.detach())

    # Verify output
    assert logits.shape == (batch_size,)

    print("\nModel test completed successfully.")
