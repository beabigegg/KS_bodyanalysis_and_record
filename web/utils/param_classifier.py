from __future__ import annotations

import re


class ParamClassifier:
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

    QUICK_ADJUST_PREFIXES = {"QS", "QK", "QB"}
    QUICK_STITCH_KEYWORDS = {
        "STITCH",
        "LF MATERIAL",
        "WIRE DIAMETER",
        "MAX SCRUB FREQ",
        "COMPACTED",
        "CONDITION SEGMENT",
        "SCRUB AMPLITUDE",
        "SCRUB CYCLE",
    }

    BITS_PREFIXES = {"NSOP", "NSOL", "SHTL", "BITS"}
    BITS_MISC_KEYWORDS = {
        "CLAMP OPEN OFFSET",
        "LOWER HEIGHT ALARM",
        "UPPER HEIGHT ALARM",
        "BOND2 HT LIMIT",
        "BOND2 PRELEARN TIP",
        "TAIL CLOSE OFFSET",
    }

    LOOP_PREFIXES = {
        "LOOP",
        "LK",
        "LP",
        "J",
        "SPAN",
        "SPAN1",
        "SPAN2",
        "SPAN3",
        "FLAT",
        "FOLD",
        "FOLD2",
        "SHAPE",
        "BAL",
        "PCL",
        "QL",
        "RFP",
        "TK",
        "TOL",
        "MULTIBEND",
        "MULTIBENDPAYOUT",
        "MULTIBENDANGLE",
        "SHARPNESS",
        "SMOOTH",
        "LAT",
        "APPROACH",
        "AUTO",
    }
    LOOP_SECOND_APPROACH_KEYWORDS = {
        "APPROACH",
        "CONTACT ANGLE",
        "STEP DISTANCE",
    }
    LOOP_BALANCE_KEYWORDS = {
        "BALANCE",
        "REF WIRE LENGTH",
        "LF2",
    }
    LOOP_SHAPING_KEYWORDS = {
        "SPAN",
        "FLAT",
        "FOLD",
        "SHAPE",
        "RMOT",
        "TOL",
        "BLEED",
        "SHARPNESS",
        "MULTIBEND",
        "SMOOTH",
        "LAT",
        "LF3",
    }
    LOOP_MAIN_KEYWORDS = {
        "WIRE PROFILE",
        "KINK",
        "REVERSE MOTION",
        "LOOP",
        "PCL",
        "QL",
        "TK",
        "RFP",
    }

    BOND2_PREFIXES = {
        "BOND2",
        "BOND2SEG",
        "B2",
        "BD2",
        "TAIL",
        "PULLOUT",
        "SSB",
        "WEDGE",
        "Z",
    }
    BOND2_TAIL_KEYWORDS = {
        "TAIL SCRUB",
        "TAIL-STEP",
        "TAIL STEP",
        "TAIL XY",
        "TAIL_XY",
    }
    BOND2_SCRUB_KEYWORDS = {
        "2ND SCRUB",
        "2ND XY SCRUB",
        "SCRUB PHASE MODE",
    }
    BOND2_FORCE_KEYWORDS = {
        "FORCE",
        "DAMPING",
        "EQU FACTOR",
    }
    BOND2_USG_KEYWORDS = {
        "USG",
        "RING DOWN",
        "PRE BLEED",
        "PRE-BLEED",
    }
    BOND2_MISC_KEYWORDS = {
        "Z-TEAR",
        "Z_TEAR",
        "CAP-BOND",
        "CAP_",
        "NSOL TEST",
        "LED_BOND",
    }

    BOND1_PREFIXES = {
        "BOND1",
        "BOND1SEG",
        "BOND1WEDGESEG",
        "B1",
        "BD1",
        "EFO",
        "FAB",
        "SBD",
        "LBD",
        "S",
        "IMPACT",
        "FORCE",
        "USG",
        "PRO",
        "RESP",
        "SEC",
        "BURST",
        "BOND",
        "BALL",
        "CALCEFOTIME",
        "ADJ",
        "ADV",
        "C",
        "BHD",
    }
    BUMP_PREFIXES = {"BUMP"}
    BUMP_KEYWORDS = {"BUMP"}
    BOND1_EFO_KEYWORDS = {
        "EFO",
        "FAB",
        "SBD",
        "LBD",
        "TAIL EXTENSION",
        "WIRE DIAMETER",
        "BALL SIZE",
        "CALCEFOTIME",
    }
    BOND1_COMMON_KEYWORDS = {
        "TIP",
        "C/V",
        "CONTACT",
        "CONTDETECT",
        "IMPACT",
    }
    BOND1_FORCE_KEYWORDS = {
        "FORCE",
        "DAMPING",
        "ENERGY",
        "FS",
        "REFERENCE DELAY",
        "ADJ USG LEVEL",
        "MIN USG TIME",
    }
    BOND1_USG_KEYWORDS = {
        "USG",
        "BURST",
        "PREBLEED",
        "PRE-BLEED",
        "POWER EQU",
        "RAMP",
    }
    BOND1_SCRUB_KEYWORDS = {
        "SCRUB",
        "SETTL",
        "SMOOTH",
    }

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
        return match.group(1).upper()

    @staticmethod
    def _normalized_body(pp_body: str) -> str:
        return pp_body.upper().replace("_", " ").replace("-", " ")

    @staticmethod
    def _has_any(body_upper: str, keywords: set[str]) -> bool:
        return any(keyword in body_upper for keyword in keywords)

    @classmethod
    def _keyword_category(cls, body_upper: str, keyword_map: dict[str, str]) -> str:
        for keyword, category in keyword_map.items():
            if keyword.replace("_", " ").upper() in body_upper:
                return category
        return "other"

    @classmethod
    def _prm_stage(cls, prefix: str, body_upper: str) -> str:
        if prefix in cls.QUICK_ADJUST_PREFIXES or "ADJUST" in body_upper:
            return "quick_adjust"

        if prefix in cls.BITS_PREFIXES or cls._has_any(body_upper, {"NSOP", "NSOL", "SHTL", "BITS"} | cls.BITS_MISC_KEYWORDS):
            return "bits_other"

        if prefix in cls.LOOP_PREFIXES or cls._has_any(
            body_upper,
            cls.LOOP_SECOND_APPROACH_KEYWORDS | cls.LOOP_BALANCE_KEYWORDS | cls.LOOP_SHAPING_KEYWORDS | cls.LOOP_MAIN_KEYWORDS,
        ):
            return "loop"

        if prefix in cls.BOND2_PREFIXES or cls._has_any(
            body_upper,
            cls.BOND2_TAIL_KEYWORDS | cls.BOND2_SCRUB_KEYWORDS | cls.BOND2_MISC_KEYWORDS,
        ):
            return "bond2"

        if prefix in cls.BUMP_PREFIXES or cls._has_any(body_upper, cls.BUMP_KEYWORDS):
            return "bump"

        if prefix in cls.BOND1_PREFIXES or cls._has_any(
            body_upper,
            cls.BOND1_EFO_KEYWORDS | cls.BOND1_COMMON_KEYWORDS | cls.BOND1_FORCE_KEYWORDS | cls.BOND1_USG_KEYWORDS | cls.BOND1_SCRUB_KEYWORDS,
        ):
            return "bond1"

        return "_unmapped"

    @classmethod
    def _bond1_category(cls, body_upper: str) -> str:
        if cls._has_any(body_upper, cls.BOND1_EFO_KEYWORDS):
            return "ball_efo"
        if cls._has_any(body_upper, cls.BOND1_COMMON_KEYWORDS):
            return "common"
        if cls._has_any(body_upper, cls.BOND1_FORCE_KEYWORDS):
            return "force"
        if cls._has_any(body_upper, cls.BOND1_USG_KEYWORDS):
            return "usg"
        if cls._has_any(body_upper, cls.BOND1_SCRUB_KEYWORDS):
            return "scrub"
        return "misc"

    @classmethod
    def _bond2_category(cls, body_upper: str) -> str:
        if cls._has_any(body_upper, cls.BOND2_TAIL_KEYWORDS):
            return "tail_scrub"
        if cls._has_any(body_upper, cls.BOND2_SCRUB_KEYWORDS):
            return "scrub"
        if cls._has_any(body_upper, cls.BOND2_FORCE_KEYWORDS):
            return "force"
        if cls._has_any(body_upper, cls.BOND2_USG_KEYWORDS):
            return "usg"
        return "misc"

    @classmethod
    def _loop_category(cls, prefix: str, body_upper: str) -> str:
        if prefix == "BAL":
            return "balance"
        if cls._has_any(body_upper, cls.LOOP_SECOND_APPROACH_KEYWORDS):
            return "second_approach"
        if cls._has_any(body_upper, cls.LOOP_BALANCE_KEYWORDS):
            return "balance"
        if cls._has_any(body_upper, cls.LOOP_SHAPING_KEYWORDS):
            return "shaping"
        return "main"

    @classmethod
    def _bits_category(cls, body_upper: str) -> str:
        if "NSOP" in body_upper:
            return "nsop"
        if "NSOL" in body_upper or "SHTL" in body_upper:
            return "nsol_shtl"
        if "BITS" in body_upper:
            return "bits"
        return "misc"

    @classmethod
    def _quick_adjust_category(cls, body_upper: str) -> str:
        if cls._has_any(body_upper, cls.QUICK_STITCH_KEYWORDS):
            return "stitch"
        return "bond"

    @classmethod
    def _classify_prm(cls, pp_body: str) -> tuple[str | None, str | None]:
        prefix = cls._prefix(pp_body)
        if not prefix:
            return None, None

        body_upper = cls._normalized_body(pp_body)
        stage = cls._prm_stage(prefix, body_upper)
        if stage == "_unmapped":
            return "_unmapped", prefix.lower()
        if stage in {"bond1", "bump"}:
            return stage, cls._bond1_category(body_upper)
        if stage == "bond2":
            return stage, cls._bond2_category(body_upper)
        if stage == "loop":
            return stage, cls._loop_category(prefix, body_upper)
        if stage == "bits_other":
            return stage, cls._bits_category(body_upper)
        if stage == "quick_adjust":
            return stage, cls._quick_adjust_category(body_upper)
        return stage, None

    @classmethod
    def classify(cls, param_name: str, file_type: str) -> tuple[str | None, str | None]:
        normalized_name = (param_name or "").strip()
        normalized_type = (file_type or "").strip().upper()

        if normalized_type in {"LF", "MAG"}:
            return None, None

        role, pp_body = cls._split_name(normalized_name)
        body_upper = cls._normalized_body(pp_body)

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
