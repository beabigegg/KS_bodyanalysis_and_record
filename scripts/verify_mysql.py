"""Verify MySQL data after a pipeline run."""
from __future__ import annotations

import os

from dotenv import load_dotenv
import pymysql


def main() -> None:
    load_dotenv()
    conn = pymysql.connect(host=os.getenv("MYSQL_HOST", "127.0.0.1"), port=int(os.getenv("MYSQL_PORT", "3306")), user=os.getenv("MYSQL_USER", "root"), password=os.getenv("MYSQL_PASSWORD", ""), database=os.getenv("MYSQL_DATABASE", ""), charset=os.getenv("MYSQL_CHARSET", "utf8mb4"))
    cur = conn.cursor()

    print("=== ksbody_recipe_import ===")
    cur.execute("SELECT id, machine_type, machine_id, product_type, bop, wafer_pn, recipe_version, recipe_name, mc_serial, sw_version, recipe_datetime, source_file FROM ksbody_recipe_import")
    for row in cur.fetchall():
        print(f"  id={row[0]}, machine_type={row[1]}, machine_id={row[2]}, product_type={row[3]}, bop={row[4]}, wafer_pn={row[5]}, ver={row[6]}")
        print(f"    recipe_name={row[7]}, mc_serial={row[8]}, sw_version={row[9]}, recipe_datetime={row[10]}")
        print(f"    source_file={row[11]}")

    print("\n=== ksbody_recipe_params (by file_type) ===")
    cur.execute("SELECT file_type, COUNT(*) FROM ksbody_recipe_params WHERE recipe_import_id=1 GROUP BY file_type ORDER BY COUNT(*) DESC")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} params")

    print("\n=== ksbody_recipe_params (PRM sample, first 5) ===")
    cur.execute("SELECT param_name, param_value, unit, min_value, max_value, default_value FROM ksbody_recipe_params WHERE recipe_import_id=1 AND file_type='PRM' LIMIT 5")
    for row in cur.fetchall():
        print(f"  {row[0]} = {row[1]} [{row[2]}] min={row[3]} max={row[4]} default={row[5]}")

    print("\n=== ksbody_recipe_app_spec ===")
    cur.execute("SELECT * FROM ksbody_recipe_app_spec WHERE recipe_import_id=1")
    for row in cur.fetchall():
        print(f"  cap_tip_dia={row[4]}, cap_hole_dia={row[5]}, wire_dia={row[10]}, wire_metal={row[11]}")

    print("\n=== ksbody_recipe_bsg (count + sample) ===")
    cur.execute("SELECT COUNT(*) FROM ksbody_recipe_bsg WHERE recipe_import_id=1")
    print(f"  total: {cur.fetchone()[0]}")
    cur.execute("SELECT ball_group, inspection_key, process_key, value FROM ksbody_recipe_bsg WHERE recipe_import_id=1 LIMIT 5")
    for row in cur.fetchall():
        print(f"  group={row[0]}, insp={row[1]}, proc={row[2]}, val={row[3]}")

    print("\n=== ksbody_recipe_rpm_limits (count + sample) ===")
    cur.execute("SELECT COUNT(*) FROM ksbody_recipe_rpm_limits WHERE recipe_import_id=1")
    print(f"  total: {cur.fetchone()[0]}")
    cur.execute("SELECT signal_name, property_name, lower_limit, upper_limit, active FROM ksbody_recipe_rpm_limits WHERE recipe_import_id=1 LIMIT 5")
    for row in cur.fetchall():
        print(f"  signal={row[0]}, prop={row[1]}, lower={row[2]}, upper={row[3]}, active={row[4]}")

    print("\n=== ksbody_recipe_rpm_reference (count) ===")
    cur.execute("SELECT COUNT(*) FROM ksbody_recipe_rpm_reference WHERE recipe_import_id=1")
    print(f"  total: {cur.fetchone()[0]}")
    conn.close()


if __name__ == "__main__":
    main()
