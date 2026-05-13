"""
Value Objects - Objetos inmutables con validación del dominio.
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self):
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", self.value):
            raise ValueError(f"Email inválido: {self.value}")


@dataclass(frozen=True)
class Pin:
    value: str

    def __post_init__(self):
        if not re.match(r"^\d{4,6}$", self.value):
            raise ValueError("El PIN debe ser de 4 a 6 dígitos")


@dataclass(frozen=True)
class MacAddress:
    value: str

    def __post_init__(self):
        pattern = r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$"
        if not re.match(pattern, self.value):
            raise ValueError(f"MAC address inválida: {self.value}")


@dataclass(frozen=True)
class UmbralOscuridad:
    value: int

    def __post_init__(self):
        if not 0 <= self.value <= 100:
            raise ValueError(f"El umbral debe estar entre 0 y 100, recibido: {self.value}")
