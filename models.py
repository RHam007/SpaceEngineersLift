from dataclasses import dataclass
from typing import List, Optional
import json

# Thruster specifications in Newtons
THRUSTER_SPECS = {
    'atmospheric': {
        'small': 82000,
        'large': 408000
    },
    'ion': {
        'small': 14400,
        'large': 172800
    },
    'hydrogen': {
        'small': 98400,
        'large': 478800
    }
}

@dataclass
class ThrusterCount:
    small: int = 0
    large: int = 0

    def calculate_thrust(self, thrust_type: str) -> float:
        specs = THRUSTER_SPECS[thrust_type]
        return (self.small * specs['small']) + (self.large * specs['large'])

    def to_dict(self) -> dict:
        return {
            'small': self.small,
            'large': self.large
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ThrusterCount':
        return cls(**data)

@dataclass
class GridSpecifications:
    mass: float
    gravity: float = 9.81  # Default Earth gravity
    atmospheric_thrusters: ThrusterCount = None
    ion_thrusters: ThrusterCount = None
    hydrogen_thrusters: ThrusterCount = None

    def __post_init__(self):
        self.atmospheric_thrusters = self.atmospheric_thrusters or ThrusterCount()
        self.ion_thrusters = self.ion_thrusters or ThrusterCount()
        self.hydrogen_thrusters = self.hydrogen_thrusters or ThrusterCount()

    def calculate_thrust_by_type(self) -> dict:
        return {
            'atmospheric': self.atmospheric_thrusters.calculate_thrust('atmospheric'),
            'ion': self.ion_thrusters.calculate_thrust('ion'),
            'hydrogen': self.hydrogen_thrusters.calculate_thrust('hydrogen')
        }

    def calculate_total_thrust(self) -> float:
        thrusts = self.calculate_thrust_by_type()
        return sum(thrusts.values())

    def calculate_lift_capacity(self) -> float:
        total_thrust = self.calculate_total_thrust()
        return (total_thrust - (self.mass * self.gravity)) / self.gravity

    def to_dict(self) -> dict:
        return {
            'mass': self.mass,
            'gravity': self.gravity,
            'atmospheric_thrusters': self.atmospheric_thrusters.to_dict(),
            'ion_thrusters': self.ion_thrusters.to_dict(),
            'hydrogen_thrusters': self.hydrogen_thrusters.to_dict()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GridSpecifications':
        specs_data = data.copy()
        specs_data['atmospheric_thrusters'] = ThrusterCount.from_dict(data['atmospheric_thrusters'])
        specs_data['ion_thrusters'] = ThrusterCount.from_dict(data['ion_thrusters'])
        specs_data['hydrogen_thrusters'] = ThrusterCount.from_dict(data['hydrogen_thrusters'])
        return cls(**specs_data)

@dataclass
class Preset:
    name: str
    specifications: GridSpecifications

    def save(self) -> str:
        return json.dumps({
            'name': self.name,
            'specifications': self.specifications.to_dict()
        })

    @classmethod
    def load(cls, data: str) -> 'Preset':
        parsed = json.loads(data)
        return cls(
            name=parsed['name'],
            specifications=GridSpecifications.from_dict(parsed['specifications'])
        )