import numpy as np
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class CastiglianoCalculationError(Exception):
    """Raised when Castigliano calculation fails due to invalid parameters."""
    pass


class InvalidMaterialPropertyError(CastiglianoCalculationError):
    """Raised when material properties are invalid."""
    pass


class InvalidGeometryError(CastiglianoCalculationError):
    """Raised when geometric parameters are invalid."""
    pass


class NumericalInstabilityError(CastiglianoCalculationError):
    """Raised when numerical instability is detected."""
    pass


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
    
    **Safety Features**:
    - All parameters validated before calculation
    - Minimum value checks for material and geometric properties
    - Denominator zero-defense before every division
    - Numerical instability detection
    """
    
    SECTION_SHAPE_FACTOR_RECTANGLE = 6.0 / 5.0
    
    MIN_BEAM_LENGTH = 0.01
    MIN_SECTION_DIMENSION = 0.001
    MIN_ELASTIC_MODULUS = 1e6
    MIN_SHEAR_MODULUS = 1e5
    MIN_DISPLACEMENT_UM = -10000.0
    MAX_DISPLACEMENT_UM = 10000.0
    MIN_TOTAL_COMPLIANCE = 1e-15

    @classmethod
    def _validate_geometric_parameters(
        cls,
        beam_length: float,
        section_width: float,
        section_height: float,
    ) -> None:
        """Validate geometric parameters before calculation."""
        if not np.isfinite(beam_length) or beam_length <= 0:
            raise InvalidGeometryError(
                f"Beam length must be positive and finite, got {beam_length}"
            )
        if beam_length < cls.MIN_BEAM_LENGTH:
            raise InvalidGeometryError(
                f"Beam length {beam_length}m is below minimum {cls.MIN_BEAM_LENGTH}m"
            )
        
        if not np.isfinite(section_width) or section_width <= 0:
            raise InvalidGeometryError(
                f"Section width must be positive and finite, got {section_width}"
            )
        if section_width < cls.MIN_SECTION_DIMENSION:
            raise InvalidGeometryError(
                f"Section width {section_width}m is below minimum {cls.MIN_SECTION_DIMENSION}m"
            )
        
        if not np.isfinite(section_height) or section_height <= 0:
            raise InvalidGeometryError(
                f"Section height must be positive and finite, got {section_height}"
            )
        if section_height < cls.MIN_SECTION_DIMENSION:
            raise InvalidGeometryError(
                f"Section height {section_height}m is below minimum {cls.MIN_SECTION_DIMENSION}m"
            )

    @classmethod
    def _validate_material_properties(
        cls,
        elastic_modulus: float,
        shear_modulus: float,
    ) -> None:
        """Validate material properties before calculation."""
        if not np.isfinite(elastic_modulus) or elastic_modulus <= 0:
            raise InvalidMaterialPropertyError(
                f"Elastic modulus must be positive and finite, got {elastic_modulus}"
            )
        if elastic_modulus < cls.MIN_ELASTIC_MODULUS:
            raise InvalidMaterialPropertyError(
                f"Elastic modulus {elastic_modulus}Pa is below minimum {cls.MIN_ELASTIC_MODULUS}Pa"
            )
        
        if not np.isfinite(shear_modulus) or shear_modulus <= 0:
            raise InvalidMaterialPropertyError(
                f"Shear modulus must be positive and finite, got {shear_modulus}"
            )
        if shear_modulus < cls.MIN_SHEAR_MODULUS:
            raise InvalidMaterialPropertyError(
                f"Shear modulus {shear_modulus}Pa is below minimum {cls.MIN_SHEAR_MODULUS}Pa"
            )

    @classmethod
    def _validate_displacement(cls, displacement_um: float) -> None:
        """Validate displacement input."""
        if not np.isfinite(displacement_um):
            raise NumericalInstabilityError(
                f"Displacement must be finite, got {displacement_um}"
            )
        if displacement_um < cls.MIN_DISPLACEMENT_UM or displacement_um > cls.MAX_DISPLACEMENT_UM:
            logger.warning(
                f"Displacement {displacement_um}μm is outside typical range "
                f"[{cls.MIN_DISPLACEMENT_UM}, {cls.MAX_DISPLACEMENT_UM}]μm"
            )

    @staticmethod
    def moment_of_inertia(width: float, height: float) -> float:
        """
        Calculate moment of inertia for rectangular section.
        I = (b * h³) / 12
        
        Raises:
            InvalidGeometryError: if width or height is invalid
        """
        if not np.isfinite(width) or width <= 0:
            raise InvalidGeometryError(
                f"Width must be positive and finite, got {width}"
            )
        if width < CastiglianoEngine.MIN_SECTION_DIMENSION:
            raise InvalidGeometryError(
                f"Width {width}m is below minimum {CastiglianoEngine.MIN_SECTION_DIMENSION}m"
            )
        
        if not np.isfinite(height) or height <= 0:
            raise InvalidGeometryError(
                f"Height must be positive and finite, got {height}"
            )
        if height < CastiglianoEngine.MIN_SECTION_DIMENSION:
            raise InvalidGeometryError(
                f"Height {height}m is below minimum {CastiglianoEngine.MIN_SECTION_DIMENSION}m"
            )
        
        denominator = 12.0
        if abs(denominator) < 1e-12:
            raise NumericalInstabilityError(
                "Denominator too small in moment of inertia calculation"
            )
        
        result = (width * height ** 3) / denominator
        
        if not np.isfinite(result) or result <= 0:
            raise NumericalInstabilityError(
                f"Invalid moment of inertia result: {result}"
            )
        
        return result

    @staticmethod
    def cross_section_area(width: float, height: float) -> float:
        """Calculate cross-sectional area with validation."""
        if not np.isfinite(width) or width <= 0:
            raise InvalidGeometryError(
                f"Width must be positive and finite, got {width}"
            )
        if width < CastiglianoEngine.MIN_SECTION_DIMENSION:
            raise InvalidGeometryError(
                f"Width {width}m is below minimum {CastiglianoEngine.MIN_SECTION_DIMENSION}m"
            )
        
        if not np.isfinite(height) or height <= 0:
            raise InvalidGeometryError(
                f"Height must be positive and finite, got {height}"
            )
        if height < CastiglianoEngine.MIN_SECTION_DIMENSION:
            raise InvalidGeometryError(
                f"Height {height}m is below minimum {CastiglianoEngine.MIN_SECTION_DIMENSION}m"
            )
        
        result = width * height
        
        if not np.isfinite(result) or result <= 0:
            raise NumericalInstabilityError(
                f"Invalid cross-sectional area result: {result}"
            )
        
        return result

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
        Calculate bending and shear stiffness coefficients with full validation.
        
        Returns:
            Tuple of (bending_stiffness_coeff, shear_stiffness_coeff)
            where displacement = F * (bending_coeff + shear_coeff)
            
        Raises:
            InvalidGeometryError: if geometric parameters are invalid
            InvalidMaterialPropertyError: if material properties are invalid
            NumericalInstabilityError: if calculation becomes unstable
        """
        cls._validate_geometric_parameters(
            beam_length, section_width, section_height
        )
        cls._validate_material_properties(
            elastic_modulus, shear_modulus
        )
        
        I = cls.moment_of_inertia(section_width, section_height)
        A = cls.cross_section_area(section_width, section_height)
        
        bending_denominator = 3 * elastic_modulus * I
        if abs(bending_denominator) < cls.MIN_TOTAL_COMPLIANCE:
            raise NumericalInstabilityError(
                f"Bending denominator {bending_denominator} is too small, "
                f"risk of division by zero. Check E={elastic_modulus}, I={I}"
            )
        
        bending_coeff = beam_length ** 3 / bending_denominator
        
        shear_denominator = shear_modulus * A
        if abs(shear_denominator) < cls.MIN_TOTAL_COMPLIANCE:
            raise NumericalInstabilityError(
                f"Shear denominator {shear_denominator} is too small, "
                f"risk of division by zero. Check G={shear_modulus}, A={A}"
            )
        
        shear_coeff = cls.SECTION_SHAPE_FACTOR_RECTANGLE * beam_length / shear_denominator
        
        if not np.isfinite(bending_coeff) or not np.isfinite(shear_coeff):
            raise NumericalInstabilityError(
                f"Non-finite stiffness coefficients: bending={bending_coeff}, "
                f"shear={shear_coeff}"
            )
        
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
            
        Raises:
            NumericalInstabilityError: if force is invalid
            CastiglianoCalculationError: if calculation fails
        """
        if not np.isfinite(force):
            raise NumericalInstabilityError(f"Force must be finite, got {force}")
        
        bending_coeff, shear_coeff = cls.calculate_stiffness(
            beam_length, section_width, section_height,
            elastic_modulus, shear_modulus
        )
        
        displacement = force * (bending_coeff + shear_coeff)
        
        if not np.isfinite(displacement):
            raise NumericalInstabilityError(
                f"Non-finite displacement result: {displacement}"
            )
        
        return displacement

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
        
        **Critical Defense**: This is the most vulnerable function due to
        the division by total_compliance. Full validation is performed
        BEFORE any division.
        
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
            
        Raises:
            ValueError: if displacement is NaN or infinite
            InvalidGeometryError: if geometric parameters are invalid
            InvalidMaterialPropertyError: if material properties are invalid
            NumericalInstabilityError: if denominator is too small or result is non-finite
        """
        cls._validate_displacement(displacement_um)
        
        bending_coeff, shear_coeff = cls.calculate_stiffness(
            beam_length, section_width, section_height,
            elastic_modulus, shear_modulus
        )
        
        total_compliance = bending_coeff + shear_coeff
        
        if abs(total_compliance) < cls.MIN_TOTAL_COMPLIANCE:
            raise NumericalInstabilityError(
                f"Total compliance {total_compliance} is below minimum threshold "
                f"{cls.MIN_TOTAL_COMPLIANCE}. This would cause division by zero. "
                f"bending_coeff={bending_coeff}, shear_coeff={shear_coeff}. "
                f"Check material properties (E={elastic_modulus}, G={shear_modulus}) "
                f"and geometry (L={beam_length}, w={section_width}, h={section_height})"
            )
        
        displacement_m = displacement_um * 1e-6
        
        try:
            shear_force = displacement_m / total_compliance
        except ZeroDivisionError as e:
            logger.error(
                f"ZeroDivisionError caught in force calculation despite pre-check. "
                f"total_compliance={total_compliance}, displacement_m={displacement_m}"
            )
            raise NumericalInstabilityError(
                f"Division by zero in force calculation: {e}"
            ) from e
        
        if not np.isfinite(shear_force):
            raise NumericalInstabilityError(
                f"Non-finite shear force result: {shear_force}. "
                f"displacement_m={displacement_m}, total_compliance={total_compliance}"
            )
        
        if abs(shear_force) > 1e8:
            logger.warning(
                f"Unusually large shear force calculated: {shear_force}N. "
                f"Input displacement={displacement_um}μm"
            )
        
        bending_moment = shear_force * beam_length
        
        if not np.isfinite(bending_moment):
            raise NumericalInstabilityError(
                f"Non-finite bending moment result: {bending_moment}"
            )
        
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
        
        All inputs are validated to be finite before comparison.
        """
        if not (np.isfinite(displacement_um) and 
                np.isfinite(shear_force) and 
                np.isfinite(bending_moment)):
            logger.error(
                f"Non-finite values in stress level calculation: "
                f"displacement={displacement_um}, shear={shear_force}, "
                f"moment={bending_moment}"
            )
            return "danger"
        
        if displacement_warning <= 0 or displacement_danger <= displacement_warning:
            logger.warning("Invalid displacement thresholds, using defaults")
            displacement_warning, displacement_danger = 300.0, 500.0
        if shear_warning <= 0 or shear_danger <= shear_warning:
            logger.warning("Invalid shear force thresholds, using defaults")
            shear_warning, shear_danger = 3000.0, 5000.0
        if moment_warning <= 0 or moment_danger <= moment_warning:
            logger.warning("Invalid moment thresholds, using defaults")
            moment_warning, moment_danger = 1200.0, 2000.0
        
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
        """Get material properties for a wood type, with validation."""
        props = cls.WOOD_TYPES.get(wood_type, cls.WOOD_TYPES["pine"]).copy()
        
        if props["elastic_modulus"] < CastiglianoEngine.MIN_ELASTIC_MODULUS:
            logger.error(f"Invalid elastic modulus in preset for {wood_type}")
            props["elastic_modulus"] = cls.WOOD_TYPES["pine"]["elastic_modulus"]
        if props["shear_modulus"] < CastiglianoEngine.MIN_SHEAR_MODULUS:
            logger.error(f"Invalid shear modulus in preset for {wood_type}")
            props["shear_modulus"] = cls.WOOD_TYPES["pine"]["shear_modulus"]
            
        return props
