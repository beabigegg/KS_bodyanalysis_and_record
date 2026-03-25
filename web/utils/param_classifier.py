from __future__ import annotations

import re


class ParamClassifier:
    PP_PREFIX_MAP: dict[str, tuple[str, str | None]] = {
        # Ball formation
        "EFO": ("ball_formation", "efo"),
        "FAB": ("ball_formation", "fab"),
        "SBD": ("ball_formation", "detection"),
        "LBD": ("ball_formation", "detection"),
        "BUMP": ("ball_formation", "bump"),
        # Bond1 — full names used in ConnX Elite PRM files
        "BOND1": ("bond1", None),
        "BOND1SEG": ("bond1", "seg_params"),
        "BOND1WEDGESEG": ("bond1", "wedge"),
        # Bond1 — legacy abbreviated names
        "B1": ("bond1", None),
        "BD1": ("bond1", None),
        # Loop
        "LOOP": ("loop", "profile"),
        "LK": ("loop", "profile"),
        "LP": ("loop", "profile"),
        "J": ("loop", "other"),
        "SPAN": ("loop", "shaping"),
        "SPAN1": ("loop", "shaping"),
        "SPAN2": ("loop", "shaping"),
        "SPAN3": ("loop", "shaping"),
        "FLAT": ("loop", "shaping"),
        "FOLD": ("loop", "shaping"),
        "FOLD2": ("loop", "shaping"),
        "SHAPE": ("loop", "shaping"),
        "BAL": ("loop", "balance"),
        # Bond2 — full names
        "BOND2": ("bond2", None),
        "BOND2SEG": ("bond2", "seg_params"),
        # Bond2 — legacy abbreviated names
        "B2": ("bond2", None),
        "BD2": ("bond2", None),
        "TAIL": ("bond2", "tail"),
        "PULLOUT": ("bond2", "tail"),
        "SSB": ("bond2", "ssb"),
        # Quick adjust
        "QS": ("quick_adjust", "stitch"),
        "QK": ("quick_adjust", "bond"),
        "QB": ("quick_adjust", "bond"),
        # Quality
        "NSOP": ("quality", "nsop"),
        "NSOL": ("quality", "nsol"),
        "SHTL": ("quality", "shtl"),
        "BITS": ("quality", "general"),
        # Misc
        "EQU": ("_unmapped", "equalization"),
        "GEN": ("_unmapped", "general"),
    }

    MAG_HANDLER_KEYWORD_MAP: dict[str, str] = {
        "FIRST_SLOT": "slot",
        "LAST_SLOT": "slot",
        "SLOT": "slot",
        "PITCH": "slot",
        "POCKET": "magazine",
        "MAG": "magazine",
        "ALIGN": "alignment",
        "TEACH": "teach",
    }

    WORKHOLDER_KEYWORD_MAP: dict[str, str] = {
        "LOT_SEP": "indexing",
        "INDEX": "indexing",
        "CLAMP": "clamp",
        "VAC": "vacuum",
        "TEMP": "temperature",
    }

    DIE_REF_KEYWORD_MAP: dict[str, str] = {
        "EYEPOINT": "eyepoint",
        "NUM_SITES": "geometry",
        "NUM_SITE": "geometry",
        "SITE_PITCH": "geometry",
    }

    LEAD_REF_KEYWORD_MAP: dict[str, str] = {
        "CORRIDOR": "vll",
        "VLL": "vll",
        "EYEPOINT": "eyepoint",
        "NUM_SITES": "geometry",
        "NUM_SITE": "geometry",
        "LEAD_PITCH": "geometry",
    }

    HB_KEYWORD_MAP: dict[str, str] = {
        "BOND_SITE": "bond_site",
        "PREHEAT": "preheat",
        "PRE_HEAT": "preheat",
        "POSTHEAT": "post_heat",
        "POST_HEAT": "post_heat",
    }

    _SEG_RE = re.compile(r"_Seg_(\d+)", re.IGNORECASE)
    _PREFIX_RE = re.compile(r"^([A-Za-z0-9]+)")

    @classmethod
    def _split_name(cls, param_name: str) -> tuple[str | None, str]:
        if "/" not in param_name:
            return None, param_name
        role, pp_body = param_name.split("/", 1)
        return role.strip().lower() or None, pp_body

    @classmethod
    def _prefix(cls, pp_body: str) -> str:
        match = cls._PREFIX_RE.search(pp_body)
        if match is None:
            return ""
        return match.group(1)

    @classmethod
    def _seg_category(cls, pp_body: str) -> str:
        match = cls._SEG_RE.search(pp_body)
        if match is None:
            return "misc"
        return f"seg_{match.group(1).zfill(2)}"

    @classmethod
    def _keyword_category(cls, body_upper: str, keyword_map: dict[str, str]) -> str:
        for keyword, category in keyword_map.items():
            if keyword in body_upper:
                return category
        return "other"

    @classmethod
    def _classify_prm(cls, pp_body: str) -> tuple[str | None, str | None]:
        prefix = cls._prefix(pp_body)
        if not prefix:
            return None, None

        mapped = cls.PP_PREFIX_MAP.get(prefix.upper())
        if mapped is None:
            return "_unmapped", prefix.lower()

        stage, category = mapped
        if stage in {"bond1", "bond2"} and category is None:
            return stage, cls._seg_category(pp_body)
        return stage, category

    @classmethod
    def classify(cls, param_name: str, file_type: str) -> tuple[str | None, str | None]:
        normalized_name = (param_name or "").strip()
        normalized_type = (file_type or "").strip().upper()

        if normalized_type in {"LF", "MAG"}:
            return None, None

        role, pp_body = cls._split_name(normalized_name)
        body_upper = pp_body.upper()

        if (role or "").startswith("parms") or normalized_type == "PRM":
            return cls._classify_prm(pp_body)

        if role == "mag_handler":
            return None, cls._keyword_category(body_upper, cls.MAG_HANDLER_KEYWORD_MAP)

        if role == "workholder":
            return None, cls._keyword_category(body_upper, cls.WORKHOLDER_KEYWORD_MAP)

        if role == "die_ref":
            return None, cls._keyword_category(body_upper, cls.DIE_REF_KEYWORD_MAP)

        if role == "lead_ref":
            return None, cls._keyword_category(body_upper, cls.LEAD_REF_KEYWORD_MAP)

        if normalized_type == "HB":
            return None, cls._keyword_category(body_upper, cls.HB_KEYWORD_MAP)

        return None, None
