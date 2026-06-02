from xiaomi_miwifi.routers import SUPPORTED_ROUTERS, friendly_model


def test_known_hardware_resolves():
    assert "RM1800" in SUPPORTED_ROUTERS
    assert "RA82" in SUPPORTED_ROUTERS
    assert friendly_model("RM1800") == "Xiaomi Router AX1800"
    assert friendly_model("RA82") == "Xiaomi Router AX3000T"


def test_unknown_hardware_falls_back_to_raw_code():
    assert friendly_model("ZZ99") == "Xiaomi Router (ZZ99)"


def test_lookup_is_case_insensitive():
    assert friendly_model("rm1800") == "Xiaomi Router AX1800"
