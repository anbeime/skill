"""Baseline doctor agent package."""

from .memory import build_memory

__all__ = ["MyDoctorAgent", "build_memory"]


def __getattr__(name: str):
    if name == "MyDoctorAgent":
        from .agent import MyDoctorAgent

        return MyDoctorAgent
    raise AttributeError(name)
