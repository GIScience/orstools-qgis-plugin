import pytest
from qgis.PyQt.QtCore import QVariant, QMetaType

from ORStools.utils.wrapper import create_qgs_field

test_cases_qvariant = [
    ("int_field", QVariant.Int, 10, 0, "Integer field", None),
    ("double_field", QVariant.Double, 10, 5, "Double field", None),
    ("string_field", QVariant.String, 50, 0, "String field", None),
]

test_cases_qmetatype = [
    ("int_field", QMetaType.Int, 10, 0, "Integer field", None),
    ("double_field", QMetaType.Double, 10, 5, "Double field", QMetaType.Float),
    ("string_field", QMetaType.QString, 50, 0, "String field", None),
]


@pytest.mark.parametrize(
    "name, type_enum, length, precision, comment, subtype_enum", test_cases_qvariant
)
def test_create_qgs_field_with_qvariant(name, type_enum, length, precision, comment, subtype_enum):
    field = create_qgs_field(name, type_enum, length, precision, comment, subtype_enum)
    assert field.name() == name
    assert field.length() == length
    assert field.precision() == precision
    assert field.comment() == comment


@pytest.mark.parametrize(
    "name, type_enum, length, precision, comment, subtype_enum", test_cases_qmetatype
)
def test_create_qgs_field_with_qmetatype(name, type_enum, length, precision, comment, subtype_enum):
    field = create_qgs_field(name, type_enum, length, precision, comment, subtype_enum)
    assert field.name() == name
    assert field.length() == length
    assert field.precision() == precision
    assert field.comment() == comment
