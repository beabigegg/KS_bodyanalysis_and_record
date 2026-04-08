from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sqlite3
import tarfile
import tempfile


def _add_text_file(archive: tarfile.TarFile, arcname: str, content: str) -> None:
    data = content.strip().encode("utf-8") + b"\n"
    info = tarfile.TarInfo(name=arcname)
    info.size = len(data)
    archive.addfile(info, BytesIO(data))


def _build_rpm_bytes() -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
        db_path = Path(handle.name)

    try:
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                """
                CREATE TABLE rpm_limits (
                    signal_name_k TEXT,
                    property_name_k TEXT,
                    rpm_group_k TEXT,
                    bond_type_k TEXT,
                    measurement_name_k TEXT,
                    limit_type_k TEXT,
                    statistic_type_k TEXT,
                    lower_limit REAL,
                    upper_limit REAL,
                    lower_active INTEGER,
                    upper_active INTEGER
                )
                """
            )
            conn.execute(
                """
                INSERT INTO rpm_limits (
                    signal_name_k, property_name_k, rpm_group_k, bond_type_k,
                    measurement_name_k, limit_type_k, statistic_type_k,
                    lower_limit, upper_limit, lower_active, upper_active
                ) VALUES (
                    'sig-a', 'prop-a', 'grp', 'ball', 'm1', 'warning', 'avg',
                    0.1, 0.9, 1, 1
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE rpm_reference_data (
                    signal_name_k TEXT,
                    property_name_k TEXT,
                    rpm_group_k TEXT,
                    bond_type_k TEXT,
                    measurement_name_k TEXT,
                    source_k TEXT,
                    average REAL,
                    median REAL,
                    std_dev REAL,
                    median_abs_dev REAL,
                    minimum REAL,
                    maximum REAL,
                    sample_count INTEGER
                )
                """
            )
            conn.execute(
                """
                INSERT INTO rpm_reference_data (
                    signal_name_k, property_name_k, rpm_group_k, bond_type_k,
                    measurement_name_k, source_k, average, median, std_dev,
                    median_abs_dev, minimum, maximum, sample_count
                ) VALUES (
                    'sig-a', 'prop-a', 'grp', 'ball', 'm1', 'golden',
                    0.5, 0.5, 0.1, 0.05, 0.2, 0.8, 10
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

        return db_path.read_bytes()
    finally:
        db_path.unlink(missing_ok=True)


def build_sample_recipe_archive(base_dir: Path, variant: str) -> Path:
    machine_type = "ConnX Elite"
    variants = {
        "pja3406": {
            "machine_id": "PJA3406",
            "filename": "L_WBK_ConnX Elite@ECC17@BOP-A@WAF903898_1",
            "bnd_name": "MR192600.BND",
            "bnd_lines": [
                "name Recipe-A",
                "mc_serial_number 10626",
                "mc_software_version 1.0",
                "date_time 03/24/26 08:00:00",
                "mag_handler CJ621A20.PHY",
                "workholder CJ621A41.PHY",
                "lead_frame LF0001.LF",
                "magazine MAG0001.MAG",
                "heat_block HB0001.HB",
                "indexer_ref_system IDX0001.REF",
                "parms CJ621A20.PRM ball",
                "parms CJ621A41.PRM",
                "ref CJ621A20.REF",
                "ref CJ621A41.REF",
                "master_wire_chain 1 AP643419.WIR",
            ],
            "refs": {
                "CJ621A20.REF": "ref_type = DIE\nname = Die Ref\nnum_sites = 8",
                "CJ621A41.REF": "ref_type = LEAD\nname = Lead Ref\nnum_sites = 16",
            },
            "prms": {
                "CJ621A20.PRM": "\n".join(
                    [
                        "Bond1_Force_Seg_01 = 150",
                        "EFO_Power = 80",
                        "SF3_Rtn_Control = 1",
                    ]
                ),
                "CJ621A41.PRM": "Bond1_Force_Seg_01 = 151",
            },
        },
        "pjs6400": {
            "machine_id": "PJS6400",
            "filename": "L_WBK_ConnX Elite@ECC17@BOP-A@WAF007957_1",
            "bnd_name": "JA252600.BND",
            "bnd_lines": [
                "name Recipe-B",
                "mc_serial_number 10627",
                "mc_software_version 1.0",
                "date_time 03/24/26 08:00:00",
                "mag_handler CJ621A20.PHY",
                "workholder CJ621A41.PHY",
                "lead_frame LF0001.LF",
                "magazine MAG0001.MAG",
                "heat_block HB0001.HB",
                "indexer_ref_system IDX0001.REF",
                "parms CJ621A20.PRM",
                "parms CJ621A41.PRM",
                "ref AP643419.REF",
                "master_wire_chain 1 AP643419.WIR",
            ],
            "refs": {
                "AP643419.REF": "ref_type = DIE\nname = Wire Ref\nnum_sites = 4",
            },
            "prms": {
                "CJ621A20.PRM": "Bond1_Force_Seg_01 = 150",
                "CJ621A41.PRM": "Bond1_Force_Seg_01 = 150",
            },
        },
    }
    spec = variants[variant]
    archive_path = base_dir / machine_type / spec["machine_id"] / spec["filename"]
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    wir_content = "\n".join(
        [
            "group CJ621A20.PRM 2",
            "group CJ621A41.PRM 3",
            "connect 1 INST1 SITE1 2 PROFILE1",
            "connect 2 INST2 SITE2 2 PROFILE1",
            "connect 3 INST3 SITE3 3 PROFILE2",
        ]
    )
    bsg_content = "\n".join(
        [
            "ball_group 1 {",
            "  fab {",
            "    pbi_dia_nom = 5.0",
            "  }",
            "}",
        ]
    )
    app_content = "\n".join(["CapManufacturer=K&S", "WireDia=1.7"])

    with tarfile.open(archive_path, mode="w:gz") as archive:
        _add_text_file(archive, spec["bnd_name"], "\n".join(spec["bnd_lines"]))
        _add_text_file(archive, "CJ621A20.PHY", "IN_FIRST_SLOT = 1")
        _add_text_file(archive, "CJ621A41.PHY", "LOT_SEP_MODES = 2")
        _add_text_file(archive, "LF0001.LF", "LF_PITCH = 254.0")
        _add_text_file(archive, "MAG0001.MAG", "MAG_POS = 1")
        _add_text_file(archive, "HB0001.HB", "PREHEAT_TEMP = 120")
        _add_text_file(archive, "AP643419.WIR", wir_content)
        _add_text_file(archive, "RECIPE.BSG", bsg_content)
        _add_text_file(archive, "RECIPE.APP", app_content)

        for name, content in spec["refs"].items():
            _add_text_file(archive, name, content)
        for name, content in spec["prms"].items():
            _add_text_file(archive, name, content)

        rpm_bytes = _build_rpm_bytes()
        rpm_info = tarfile.TarInfo(name="RECIPE.RPM")
        rpm_info.size = len(rpm_bytes)
        archive.addfile(rpm_info, BytesIO(rpm_bytes))

    return archive_path
