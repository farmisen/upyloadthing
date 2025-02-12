from upyloadthing.utils import snakify


def test_snakify_dict():
    """Test dictionary key conversion."""
    input_dict = {
        "userName": "john",
        "userAge": 30,
        "userAddress": {"streetName": "Main St", "houseNumber": 123},
    }
    expected = {
        "user_name": "john",
        "user_age": 30,
        "user_address": {"street_name": "Main St", "house_number": 123},
    }
    assert snakify(input_dict) == expected


def test_snakify_list():
    """Test list of dictionaries conversion."""
    input_list = [{"userName": "john"}, {"userName": "jane"}]
    expected = [{"user_name": "john"}, {"user_name": "jane"}]
    assert snakify(input_list) == expected


def test_snakify_nested_structure():
    """Test complex nested structure conversion."""
    input_data = {
        "userData": {
            "personalInfo": {"firstName": "John", "lastName": "Doe"},
            "contactDetails": [
                {"phoneNumber": "123-456"},
                {"emailAddress": "john@example.com"},
            ],
        }
    }
    expected = {
        "user_data": {
            "personal_info": {"first_name": "John", "last_name": "Doe"},
            "contact_details": [
                {"phone_number": "123-456"},
                {"email_address": "john@example.com"},
            ],
        }
    }
    assert snakify(input_data) == expected


def test_snakify_non_dict_types():
    """Test handling of non-dictionary types."""
    assert snakify(None) is None
    assert snakify(42) == 42
    assert snakify("someString") == "someString"
    assert snakify(True) is True
    assert snakify([1, 2, 3]) == [1, 2, 3]


def test_snakify_empty_structures():
    """Test handling of empty structures."""
    assert snakify({}) == {}
    assert snakify([]) == []
    assert snakify([{}]) == [{}]
