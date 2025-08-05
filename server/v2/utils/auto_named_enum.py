import enum
import sqlalchemy as sa
import re
from typing import Type


def auto_named_enum(enum_class: Type[enum.Enum], **kwargs) -> sa.Enum:
    """
    Create a SQLAlchemy Enum with automatic naming convention.

    This factory is intended to have a custom naming convention that is uniform across the whole project.
    """
    if 'name' not in kwargs:
        # Generate name from enum class
        name = enum_class.__name__

        # Remove 'Enum' suffix if present
        if name.endswith('Enum'):
            name = name[:-4]

        # Convert CamelCase to snake_case
        snake_case = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
        snake_case = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', snake_case)
        kwargs['name'] = f"{snake_case.lower()}_enum"

    return sa.Enum(enum_class, **kwargs)
