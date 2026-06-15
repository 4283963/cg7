import numpy as np
from typing import Tuple


class CastiglianoEngine:
    """
    Castigliano's Second Theorem stress calculation engine for tenon-mortise joints.
    
    Based on Castigliano's theorem: displacement δ = ∂U/∂F
    where U is the total strain energy (bending + shear).
    
    For a cantilever beam with end load F:
    - Bending strain energy: U_b = ∫ M²(x)/(2EI) dx = F²L³/(6EI)
    - Shear strain energy: U_s = ∫ kV²(x)/(2GA) dx = kF²L/(2GA)
    - Total displacement: δ = ∂U/∂F = FL³/(3EI) + kFL/(GA)
    
    Given displacement δ, we reverse-solve for force F:
    F = δ / (L³/(3EI) + kL/(GA))
    Bending moment: M = F·L
    """
    
    SECTION_SHAPE_FACTOR_RECTANGLE = 6.0 / 5.0

    @staticmethod
    def moment_of_inertia(width: float, height: float) -> float:
        """
        Calculate moment of inertia for rectangular section.
        I = (b * h³) / 12
        """
        return (width * height ** 3) / 12.0

    @staticmethod
    def cross_section_area(width: float, height: float) -> float:
        """Calculate cross-sectional area."""
        return width * height

    @classmethod
    def calculate_stiffness(
        cls,
        beam_length: float,
        section_width: float,
        section_height: float,
        elastic_modulus: float,
        shear_modulus: float,
    ) -> Tuple[float, float]:
        """
        Calculate bending and shear stiffness coefficients.
        
        Returns:
            Tuple of (bending_stiffness_coeff, shear_stiffness_coeff)
            where displacement = F * (bending_coeff + shear_coeff)
        """
        I = cls.moment_of_inertia(section_width, section_height)
        A = cls.cross_section_area(section_width, section_height)
        
        bending_coeff = beam_length ** 3 / (3 * elastic_modulus * I)
        shear_coeff = cls.SECTION_SHAPE_FACTOR_RECTANGLE * beam_length / (shear_modulus * A)
        
        return bending_coeff, shear_coeff

    @classmethod
    def displacement_from_force(
        cls,
        force: float,
        beam_length: float,
        section_width: float,
        section_height: float,
        elastic_modulus: float,
        shear_modulus: float,
    ) -> float:
        """
        Forward calculation: given force F, compute end displacement δ.
        
        Args:
            force: Applied force in Newtons
            beam_length: Beam length in meters
            section_width: Section width in meters
            section_height: Section height in meters
            elastic_modulus: Elastic modulus in Pascals
            shear_modulus: Shear modulus in Pascals
            
        Returns:
            Displacement in meters
        """
        bending_coeff, shear_coeff = cls.calculate_stiffness(
            beam_length, section_width, section_height,
            elastic_modulus, shear_modulus
        )
        return force * (bending_coeff + shear_coeff)

    @classmethod
    def force_from_displacement(
        cls,
        displacement_um: float,
        beam_length: float,
        section_width: float,
        section_height: float,
        elastic_modulus: float,
        shear_modulus: float,
    ) -> Tuple[float, float]:
        """
        Reverse calculation (Castigliano inverse): given displacement δ,
        compute shear force F and bending moment M.
        
        Args:
            displacement_um: Relative displacement in micrometers
            beam_length: Beam length in meters
            section_width: Section width in meters
            section_height: Section height in meters
            elastic_modulus: Elastic modulus in Pascals
            shear_modulus: Shear modulus in Pascals
            
        Returns:
            Tuple of (shear_force_n, bending_moment_nm)
            - shear_force: Shear force in Newtons
            - bending_moment: Bending moment in Newton-meters
        """
        displacement_m = displacement_um * 1e-6
        
        bending_coeff, shear_coeff = cls.calculate_stiffness(
            beam_length, section_width, section_height,
            elastic_modulus, shear_modulus
        )
        
        total_compliance = bending_coeff + shear_coeff
        shear_force = displacement_m / total_compliance
        bending_moment = shear_force * beam_length
        
        return shear_force, bending_moment

    @classmethod
    def calculate_stress_level(
        cls,
        displacement_um: float,
        shear_force: float,
        bending_moment: float,
        displacement_warning: float = 300.0,
        displacement_danger: float = 500.0,
        shear_warning: float = 3000.0,
        shear_danger: float = 5000.0,
        moment_warning: float = 1200.0,
        moment_danger: float = 2000.0,
    ) -> str:
        """
        Determine stress level based on thresholds.
        
        Returns:
            'normal', 'warning', or 'danger'
        """
        is_danger = (
            abs(displacement_um) >= displacement_danger
            or abs(shear_force) >= shear_danger
            or abs(bending_moment) >= moment_danger
        )
        
        if is_danger:
            return "danger"
        
        is_warning = (
            abs(displacement_um) >= displacement_warning
            or abs(shear_force) >= shear_warning
            or abs(bending_moment) >= moment_warning
        )
        
        if is_warning:
            return "warning"
        
        return "normal"


class WoodMaterialProperties:
    """
    Material properties for common ancient Chinese architectural wood types.
    """
    
    WOOD_TYPES = {
        "pine": {
            "name": "松木",
            "elastic_modulus": 10.0e9,
            "shear_modulus": 0.62e9,
            "density": 500.0,
        },
        "fir": {
            "name": "杉木",
            "elastic_modulus": 9.0e9,
            "shear_modulus": 0.55e9,
            "density": 450.0,
        },
        "cypress": {
            "name": "柏木",
            "elastic_modulus": 12.0e9,
            "shear_modulus": 0.75e9,
            "density": 580.0,
        },
        "nanmu": {
            "name": "楠木",
            "elastic_modulus": 11.0e9,
            "shear_modulus": 0.68e9,
            "density": 610.0,
        },
        "oak": {
            "name": "柞木",
            "elastic_modulus": 14.0e9,
            "shear_modulus": 0.88e9,
            "density": 720.0,
        },
    }

    @classmethod
    def get_properties(cls, wood_type: str = "pine") -> dict:
        """Get material properties for a wood type."""
        return cls.WOOD_TYPES.get(wood_type, cls.WOOD_TYPES["pine"]).copy()
