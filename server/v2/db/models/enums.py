from __future__ import annotations

import enum

from model.hashable import Hashable


class Degree(Hashable, enum.Enum):
    BACHELORS = "bachelors"
    MASTERS = "masters"

    def hash(self):
        return Hashable.hash_data(self.value)


class UniversityRole(Hashable, enum.Enum):
    ORDINARY = "ordinary"
    ASSOCIATE = "associate"
    RESEARCHER = "researcher"
    UNSPECIFIED = "unspecified"

    @property
    def abbr(self):
        if self == UniversityRole.ORDINARY:
            return "PO"
        elif self == UniversityRole.ASSOCIATE:
            return "PA"
        elif self == UniversityRole.RESEARCHER:
            return "RIC"
        else:
            raise ValueError("Role not set.")

    def hash(self):
        return Hashable.hash_data(self.value)


class TimeAvailability(Hashable, enum.Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    ALWAYS = "always"
    SPLIT = "split"

    @property
    def available_morning(self):
        return self not in [TimeAvailability.AFTERNOON]

    @property
    def available_afternoon(self):
        return self not in [TimeAvailability.MORNING]

    def hash(self):
        return Hashable.hash_data(self.value)


class SolverEnum(Hashable, enum.Enum):
    CPLEX = 'cplex'
    GLPK = 'glpk'
    GUROBI = 'gurobi'

    def hash(self):
        return Hashable.hash_data(self.value)
