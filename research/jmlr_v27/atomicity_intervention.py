"""Preregistered task-multiplicity intervention for JMLR Project Zero v27."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
import torch

@dataclass(frozen=True)
class InterventionMeta:
    arm: str
    parent_task: int
    clone_k: int
    clone_start: int
    clone_stop: int
    original_task_count: int
    exposed_task_count: int

def expose_homogeneous_clones(losses: torch.Tensor, parent_task: int, clone_k: int) -> Tuple[torch.Tensor, InterventionMeta]:
    if losses.ndim != 1: raise ValueError("losses must be a 1D semantic loss vector")
    t=int(losses.shape[0])
    if not (0 <= parent_task < t): raise IndexError(parent_task)
    if clone_k < 1: raise ValueError("clone_k must be >=1")
    parts: List[torch.Tensor]=[]
    clone_start=0
    for i in range(t):
        if i == parent_task:
            clone_start=len(parts); parts.extend([losses[i]]*clone_k)
        else: parts.append(losses[i])
    out=torch.stack(parts)
    meta=InterventionMeta("exposed",parent_task,clone_k,clone_start,clone_start+clone_k,t,t+clone_k-1)
    return out,meta

def canonicalize_exposed(exposed: torch.Tensor, meta: InterventionMeta) -> torch.Tensor:
    if exposed.ndim != 1 or int(exposed.shape[0]) != meta.exposed_task_count: raise ValueError("exposed vector does not match metadata")
    parent=exposed[meta.clone_start:meta.clone_stop].mean()
    before=[exposed[i] for i in range(meta.clone_start)]
    after=[exposed[i] for i in range(meta.clone_stop,meta.exposed_task_count)]
    return torch.stack(before+[parent]+after)

def transform_losses(losses: torch.Tensor, arm: str, parent_task: int, clone_k: int):
    if arm=="coarse":
        return losses,InterventionMeta("coarse",parent_task,clone_k,parent_task,parent_task+1,int(losses.shape[0]),int(losses.shape[0]))
    exposed,meta=expose_homogeneous_clones(losses,parent_task,clone_k)
    if arm=="exposed": return exposed,meta
    if arm=="canonicalized":
        return canonicalize_exposed(exposed,meta),InterventionMeta("canonicalized",meta.parent_task,meta.clone_k,meta.clone_start,meta.clone_stop,meta.original_task_count,meta.exposed_task_count)
    raise ValueError(f"unknown arm: {arm}")
