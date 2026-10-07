"""Observation-only differentiable-minimalization research layer.

This package may optimize parameters of already-created primitives. It must not
generate replacement imagery or bypass the canonical Scene/VectorScene pipeline.
"""
from .objective import AcceptancePolicy, LossBreakdown, LossWeights, accept_candidate, cosine_loss, objective, palette_loss
from .constrained_diffvg import DiffvgTransaction, DiffvgTransactionPolicy, ProposalResult, run_constrained_diffvg
__all__=["AcceptancePolicy","LossBreakdown","LossWeights","accept_candidate","cosine_loss","objective","palette_loss","DiffvgTransaction","DiffvgTransactionPolicy","ProposalResult","run_constrained_diffvg"]
