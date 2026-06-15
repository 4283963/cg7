import pytest
import numpy as np
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.castigliano import (
    CastiglianoEngine,
    CastiglianoCalculationError,
    InvalidMaterialPropertyError,
    InvalidGeometryError,
    NumericalInstabilityError,
)
from app.models import (
    SensorData,
    BatchSensorData,
    TenonNode,
    TenonNodeBase,
    AlertRule,
)
from app.services import (
    StressCalculationService,
    DataIngestionService,
)


VALID_PARAMS = {
    "beam_length": 2.5,
    "section_width": 0.35,
    "section_height": 0.40,
    "elastic_modulus": 11.0e9,
    "shear_modulus": 0.68e9,
}


class TestCastiglianoValidation:
    def test_moment_of_inertia_valid(self):
        I = CastiglianoEngine.moment_of_inertia(
            width=0.35, height=0.40
        )
        assert np.isfinite(I)
        assert I > 0

    @pytest.mark.parametrize("width,height", [
        (0, 0.4),
        (-0.1, 0.4),
        (0.35, 0),
        (0.35, -0.1),
        (0.0001, 0.4),
        (0.35, 0.0001),
        (np.nan, 0.4),
        (np.inf, 0.4),
        (0.35, np.inf),
    ])
    def test_moment_of_inertia_invalid(self, width, height):
        with pytest.raises(CastiglianoCalculationError):
            CastiglianoEngine.moment_of_inertia(width, height)

    def test_cross_section_area_valid(self):
        A = CastiglianoEngine.cross_section_area(0.35, 0.40)
        assert np.isfinite(A)
        assert A == pytest.approx(0.14)

    @pytest.mark.parametrize("width,height", [
        (0, 0.4),
        (-0.1, 0.4),
        (np.nan, 0.4),
        (0.35, np.inf),
    ])
    def test_cross_section_area_invalid(self, width, height):
        with pytest.raises(CastiglianoCalculationError):
            CastiglianoEngine.cross_section_area(width, height)

    def test_calculate_stiffness_valid(self):
        k1, k2 = CastiglianoEngine.calculate_stiffness(**VALID_PARAMS)
        assert np.isfinite(k1)
        assert np.isfinite(k2)
        assert k1 > 0
        assert k2 > 0

    @pytest.mark.parametrize("field,value", [
        ("beam_length", 0),
        ("beam_length", -1),
        ("beam_length", 0.0001),
        ("elastic_modulus", 0),
        ("elastic_modulus", 100),
        ("shear_modulus", 0),
        ("shear_modulus", 10),
    ])
    def test_calculate_stiffness_invalid(self, field, value):
        params = VALID_PARAMS.copy()
        params[field] = value
        with pytest.raises(CastiglianoCalculationError):
            CastiglianoEngine.calculate_stiffness(**params)

    def test_displacement_from_force_valid(self):
        disp = CastiglianoEngine.displacement_from_force(
            force=1000.0, **VALID_PARAMS
        )
        assert np.isfinite(disp)

    def test_displacement_from_force_zero_force(self):
        disp = CastiglianoEngine.displacement_from_force(
            force=0.0, **VALID_PARAMS
        )
        assert disp == 0.0

    @pytest.mark.parametrize("force", [np.nan, np.inf, -np.inf])
    def test_displacement_from_force_invalid_force(self, force):
        with pytest.raises(CastiglianoCalculationError):
            CastiglianoEngine.displacement_from_force(
                force=force, **VALID_PARAMS
            )


class TestForceFromDisplacement:
    def test_normal_case(self):
        F, M = CastiglianoEngine.force_from_displacement(
            displacement_um=100.0, **VALID_PARAMS
        )
        assert np.isfinite(F)
        assert np.isfinite(M)
        assert F > 0
        assert M > 0

    def test_zero_displacement(self):
        F, M = CastiglianoEngine.force_from_displacement(
            displacement_um=0.0, **VALID_PARAMS
        )
        assert F == 0.0
        assert M == 0.0

    def test_negative_displacement(self):
        F, M = CastiglianoEngine.force_from_displacement(
            displacement_um=-100.0, **VALID_PARAMS
        )
        assert F < 0
        assert M < 0

    @pytest.mark.parametrize("disp", [np.nan, np.inf, -np.inf])
    def test_invalid_displacement(self, disp):
        with pytest.raises(CastiglianoCalculationError):
            CastiglianoEngine.force_from_displacement(
                displacement_um=disp, **VALID_PARAMS
            )

    def test_extremely_small_elastic_modulus_triggers_numerical_instability(self):
        params = VALID_PARAMS.copy()
        params["elastic_modulus"] = 1e3
        with pytest.raises(InvalidMaterialPropertyError):
            CastiglianoEngine.force_from_displacement(
                displacement_um=100.0, **params
            )

    def test_extremely_small_beam_length_triggers_numerical_instability(self):
        params = VALID_PARAMS.copy()
        params["beam_length"] = 0.001
        with pytest.raises(InvalidGeometryError):
            CastiglianoEngine.force_from_displacement(
                displacement_um=100.0, **params
            )

    def test_zero_elastic_modulus(self):
        params = VALID_PARAMS.copy()
        params["elastic_modulus"] = 0
        with pytest.raises(InvalidMaterialPropertyError):
            CastiglianoEngine.force_from_displacement(
                displacement_um=100.0, **params
            )

    def test_zero_shear_modulus(self):
        params = VALID_PARAMS.copy()
        params["shear_modulus"] = 0
        with pytest.raises(InvalidMaterialPropertyError):
            CastiglianoEngine.force_from_displacement(
                displacement_um=100.0, **params
            )

    def test_very_large_displacement_still_valid(self):
        F, M = CastiglianoEngine.force_from_displacement(
            displacement_um=10000.0, **VALID_PARAMS
        )
        assert np.isfinite(F)
        assert np.isfinite(M)

    def test_very_small_displacement_still_valid(self):
        F, M = CastiglianoEngine.force_from_displacement(
            displacement_um=0.001, **VALID_PARAMS
        )
        assert np.isfinite(F)
        assert np.isfinite(M)

    def test_section_height_zero_prevents_zero_inertia(self):
        params = VALID_PARAMS.copy()
        params["section_height"] = 0
        with pytest.raises(InvalidGeometryError):
            CastiglianoEngine.force_from_displacement(
                displacement_um=100.0, **params
            )


class TestStressLevelCalculation:
    def test_normal_level(self):
        level = CastiglianoEngine.calculate_stress_level(
            displacement_um=100,
            shear_force=1000,
            bending_moment=500,
            displacement_warning=300,
            displacement_danger=500,
            shear_warning=3000,
            shear_danger=5000,
            moment_warning=1200,
            moment_danger=2000,
        )
        assert level == "normal"

    def test_warning_level(self):
        level = CastiglianoEngine.calculate_stress_level(
            displacement_um=400,
            shear_force=1000,
            bending_moment=500,
            displacement_warning=300,
            displacement_danger=500,
            shear_warning=3000,
            shear_danger=5000,
            moment_warning=1200,
            moment_danger=2000,
        )
        assert level == "warning"

    def test_danger_level(self):
        level = CastiglianoEngine.calculate_stress_level(
            displacement_um=600,
            shear_force=1000,
            bending_moment=500,
            displacement_warning=300,
            displacement_danger=500,
            shear_warning=3000,
            shear_danger=5000,
            moment_warning=1200,
            moment_danger=2000,
        )
        assert level == "danger"

    def test_shear_warning(self):
        level = CastiglianoEngine.calculate_stress_level(
            displacement_um=100,
            shear_force=4000,
            bending_moment=500,
            displacement_warning=300,
            displacement_danger=500,
            shear_warning=3000,
            shear_danger=5000,
            moment_warning=1200,
            moment_danger=2000,
        )
        assert level == "warning"

    def test_moment_danger(self):
        level = CastiglianoEngine.calculate_stress_level(
            displacement_um=100,
            shear_force=1000,
            bending_moment=3000,
            displacement_warning=300,
            displacement_danger=500,
            shear_warning=3000,
            shear_danger=5000,
            moment_warning=1200,
            moment_danger=2000,
        )
        assert level == "danger"

    @pytest.mark.parametrize("threshold", [0, -1, np.nan])
    def test_invalid_thresholds_use_defaults(self, threshold):
        level = CastiglianoEngine.calculate_stress_level(
            displacement_um=100,
            shear_force=1000,
            bending_moment=500,
            displacement_warning=threshold,
            displacement_danger=500,
            shear_warning=3000,
            shear_danger=5000,
            moment_warning=1200,
            moment_danger=2000,
        )
        assert level in ["normal", "warning", "danger"]

    @pytest.mark.parametrize("val", [np.nan, np.inf])
    def test_invalid_input_values_return_danger(self, val):
        level = CastiglianoEngine.calculate_stress_level(
            displacement_um=val,
            shear_force=1000,
            bending_moment=500,
            displacement_warning=300,
            displacement_danger=500,
            shear_warning=3000,
            shear_danger=5000,
            moment_warning=1200,
            moment_danger=2000,
        )
        assert level == "danger"


class TestPydanticValidation:
    def test_sensor_data_valid(self):
        data = SensorData(node_id="node-1", displacement_um=100.0)
        assert data.node_id == "node-1"
        assert data.displacement_um == 100.0

    @pytest.mark.parametrize("disp", [np.nan, np.inf, 20000.0, -20000.0])
    def test_sensor_data_invalid_displacement(self, disp):
        with pytest.raises(Exception):
            SensorData(node_id="node-1", displacement_um=disp)

    @pytest.mark.parametrize("node_id", ["", "  ", None])
    def test_sensor_data_invalid_node_id(self, node_id):
        with pytest.raises(Exception):
            SensorData(node_id=node_id, displacement_um=100.0)

    def test_batch_data_empty_rejected(self):
        with pytest.raises(Exception):
            BatchSensorData(data=[])

    def test_batch_data_too_large_rejected(self):
        data = [
            SensorData(node_id=f"node-{i}", displacement_um=100.0)
            for i in range(1001)
        ]
        with pytest.raises(Exception):
            BatchSensorData(data=data)

    def test_tenon_node_valid(self):
        node = TenonNode(
            id="node-1",
            name="Test Node",
            x=100.0,
            y=200.0,
            **VALID_PARAMS,
        )
        assert node.id == "node-1"

    @pytest.mark.parametrize("field,value", [
        ("beam_length", 0),
        ("beam_length", 0.001),
        ("section_width", 0),
        ("section_width", 0.0001),
        ("elastic_modulus", 0),
        ("shear_modulus", 0),
    ])
    def test_tenon_node_invalid_params(self, field, value):
        params = VALID_PARAMS.copy()
        params[field] = value
        with pytest.raises(Exception):
            TenonNode(
                id="node-1",
                name="Test",
                x=100, y=100,
                **params,
            )

    @pytest.mark.parametrize("field,value", [
        ("displacement_threshold", 0),
        ("displacement_threshold", -1),
        ("shear_threshold", 0),
        ("moment_threshold", 0),
    ])
    def test_alert_rule_invalid_thresholds(self, field, value):
        params = {
            "node_id": "node-1",
            "displacement_threshold": 500.0,
            "shear_threshold": 5000.0,
            "moment_threshold": 2000.0,
        }
        params[field] = value
        with pytest.raises(Exception):
            AlertRule(**params)


class TestServiceLayerErrorHandling:
    @classmethod
    def setup_class(cls):
        from app.database import init_db
        init_db()

    def test_calculate_stress_valid(self):
        node = TenonNode(
            id="node-base-left",
            name="Test",
            x=100, y=100,
            **VALID_PARAMS,
        )
        F, M, level = StressCalculationService.calculate_stress(node, 100.0)
        assert np.isfinite(F)
        assert np.isfinite(M)
        assert level in ["normal", "warning", "danger"]

    def test_pydantic_blocks_invalid_params_before_service(self):
        from pydantic import ValidationError
        params = VALID_PARAMS.copy()
        params["elastic_modulus"] = 1e3
        with pytest.raises(ValidationError):
            TenonNode(
                id="test-node",
                name="Test",
                x=100, y=100,
                **params,
            )

    def test_pydantic_blocks_zero_section_height(self):
        from pydantic import ValidationError
        params = VALID_PARAMS.copy()
        params["section_height"] = 0
        with pytest.raises(ValidationError):
            TenonNode(
                id="test-node",
                name="Test",
                x=100, y=100,
                **params,
            )

    def test_castigliano_engine_directly_with_small_modulus(self):
        from app.castigliano import InvalidMaterialPropertyError
        params = VALID_PARAMS.copy()
        params["elastic_modulus"] = 1e3
        with pytest.raises(InvalidMaterialPropertyError):
            CastiglianoEngine.force_from_displacement(
                displacement_um=100.0, **params
            )

    def test_castigliano_engine_directly_with_zero_height(self):
        from app.castigliano import InvalidGeometryError
        params = VALID_PARAMS.copy()
        params["section_height"] = 0
        with pytest.raises(InvalidGeometryError):
            CastiglianoEngine.force_from_displacement(
                displacement_um=100.0, **params
            )


class TestExceptionHierarchy:
    def test_exception_inheritance(self):
        assert issubclass(InvalidMaterialPropertyError, CastiglianoCalculationError)
        assert issubclass(InvalidGeometryError, CastiglianoCalculationError)
        assert issubclass(NumericalInstabilityError, CastiglianoCalculationError)

    def test_exception_catching_hierarchy(self):
        try:
            raise NumericalInstabilityError("Test error")
        except CastiglianoCalculationError:
            caught = True
        assert caught

    def test_specific_exception_catching(self):
        try:
            raise InvalidMaterialPropertyError("Bad modulus")
        except InvalidMaterialPropertyError as e:
            assert "modulus" in str(e).lower() or "material" in str(e).lower()


class TestNumericalEdgeCases:
    def test_denominator_close_to_zero_but_still_valid(self):
        params = VALID_PARAMS.copy()
        params["elastic_modulus"] = CastiglianoEngine.MIN_ELASTIC_MODULUS
        F, M = CastiglianoEngine.force_from_displacement(
            displacement_um=100.0, **params
        )
        assert np.isfinite(F)
        assert np.isfinite(M)

    def test_section_dimensions_at_minimum(self):
        params = VALID_PARAMS.copy()
        params["section_width"] = CastiglianoEngine.MIN_SECTION_DIMENSION
        params["section_height"] = CastiglianoEngine.MIN_SECTION_DIMENSION
        F, M = CastiglianoEngine.force_from_displacement(
            displacement_um=100.0, **params
        )
        assert np.isfinite(F)
        assert np.isfinite(M)

    def test_beam_length_at_minimum(self):
        params = VALID_PARAMS.copy()
        params["beam_length"] = CastiglianoEngine.MIN_BEAM_LENGTH
        F, M = CastiglianoEngine.force_from_displacement(
            displacement_um=100.0, **params
        )
        assert np.isfinite(F)
        assert np.isfinite(M)

    def test_displacement_at_extrema(self):
        for disp in [10000.0, -10000.0, 0.0, 0.001]:
            F, M = CastiglianoEngine.force_from_displacement(
                displacement_um=disp, **VALID_PARAMS
            )
            assert np.isfinite(F), f"Failed for disp={disp}"
            assert np.isfinite(M), f"Failed for disp={disp}"

    def test_all_params_at_minimum_boundaries(self):
        params = {
            "beam_length": CastiglianoEngine.MIN_BEAM_LENGTH,
            "section_width": CastiglianoEngine.MIN_SECTION_DIMENSION,
            "section_height": CastiglianoEngine.MIN_SECTION_DIMENSION,
            "elastic_modulus": CastiglianoEngine.MIN_ELASTIC_MODULUS,
            "shear_modulus": CastiglianoEngine.MIN_SHEAR_MODULUS,
        }
        F, M = CastiglianoEngine.force_from_displacement(
            displacement_um=100.0, **params
        )
        assert np.isfinite(F)
        assert np.isfinite(M)

    def test_all_params_below_minimum_rejected(self):
        params = {
            "beam_length": CastiglianoEngine.MIN_BEAM_LENGTH * 0.5,
            "section_width": CastiglianoEngine.MIN_SECTION_DIMENSION * 0.5,
            "section_height": CastiglianoEngine.MIN_SECTION_DIMENSION * 0.5,
            "elastic_modulus": CastiglianoEngine.MIN_ELASTIC_MODULUS * 0.5,
            "shear_modulus": CastiglianoEngine.MIN_SHEAR_MODULUS * 0.5,
        }
        with pytest.raises(InvalidGeometryError):
            CastiglianoEngine.force_from_displacement(
                displacement_um=100.0, **params
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
