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


def test_full_table_has_reference_models():
    expected = {
        "R1D", "R2D", "R3", "R3G", "R3P", "R3D", "R3L", "R3A", "R4", "R4C",
        "R4CM", "R4A", "R4AC", "D01", "R2100", "RM2100", "R3600", "RM1800",
        "RA67", "R2350", "R1350", "RA69", "RA72", "RA50", "RA70", "CR6606",
        "RA81", "RA80", "RB03", "RA71", "RB01", "RA82", "CR8808", "RB02",
        "RB04", "RA74", "RB06", "RB08", "R4AV2", "CB0401", "RC06", "RD03",
    }
    assert expected.issubset(set(SUPPORTED_ROUTERS))


def test_known_friendly_names_preserved():
    assert friendly_model("RM1800") == "Xiaomi Router AX1800"
    assert friendly_model("RA82") == "Xiaomi Router AX3000T"
    assert friendly_model("RC06") == "Redmi Router AX6000"


def test_unknown_code_still_falls_back():
    assert friendly_model("ZZ99") == "Xiaomi Router (ZZ99)"
