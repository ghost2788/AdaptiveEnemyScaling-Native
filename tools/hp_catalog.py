"""Generate and validate the isolated AES total-HP status catalog."""

import argparse
import hashlib
import re
import sys
from pathlib import Path


MAX_DELTA = 65535
_ID_PREFIX = "AESN_HP_TOTAL_"
_REQUIRED_FIELDS = {
    "StatusType": "BOOST",
    "DisplayName": "AESNHpSourceName;1",
    "StatusPropertyFlags": "DisableOverhead;DisableCombatlog;DisablePortraitIndicator",
}
_ENTRY_ID = re.compile(r'^new entry "(AESN_HP_TOTAL_([1-9][0-9]*))"$')
_DATA = re.compile(r'^data "([A-Za-z][A-Za-z0-9]*)" "([^"]*)"$')


def status_id(delta: int) -> str | None:
    """Return the one-status ID for a supported HP delta, or none for zero."""
    if isinstance(delta, bool) or not isinstance(delta, int) or not 0 <= delta <= MAX_DELTA:
        raise ValueError(f"delta must be an integer from 0 through {MAX_DELTA}")
    if delta == 0:
        return None
    return f"AESN_HP_TOTAL_{delta}"


def render_catalog() -> str:
    """Render every supported positive bonus in ascending numeric order."""
    return "\n\n".join(_render_entry(amount) for amount in range(1, MAX_DELTA + 1)) + "\n"


def validate_catalog(text: str) -> dict:
    """Validate catalog semantics independently of the renderer."""
    if not isinstance(text, str):
        raise ValueError("catalog must be text")
    blocks = text.rstrip("\n").split("\n\n")
    if not blocks or blocks == [""]:
        raise ValueError("catalog is empty")

    seen_ids = set()
    seen_stack_ids = set()
    seen_amounts = set()
    for ordinal, block in enumerate(blocks, start=1):
        _validate_entry(block, ordinal, seen_ids, seen_stack_ids, seen_amounts)

    expected = set(range(1, MAX_DELTA + 1))
    if seen_amounts != expected:
        missing = min(expected - seen_amounts) if expected - seen_amounts else None
        unexpected = min(seen_amounts - expected) if seen_amounts - expected else None
        detail = f"missing amount {missing}" if missing is not None else f"unexpected amount {unexpected}"
        raise ValueError(f"catalog amount coverage is invalid: {detail}")
    payload = text.encode("utf-8")
    return {"count": len(seen_amounts), "sha256": hashlib.sha256(payload).hexdigest()}


def _render_entry(amount: int) -> str:
    identifier = f"{_ID_PREFIX}{amount}"
    return "\n".join(
        [
            f'new entry "{identifier}"',
            'type "StatusData"',
            'data "StatusType" "BOOST"',
            'data "DisplayName" "AESNHpSourceName;1"',
            f'data "StackId" "{identifier}"',
            f'data "Boosts" "IncreaseMaxHP({amount});"',
            'data "StatusPropertyFlags" "DisableOverhead;DisableCombatlog;DisablePortraitIndicator"',
        ]
    )


def _validate_entry(block, ordinal, seen_ids, seen_stack_ids, seen_amounts):
    lines = block.splitlines()
    if len(lines) != 7:
        raise ValueError(f"entry {ordinal} has {len(lines)} lines; expected 7")
    match = _ENTRY_ID.fullmatch(lines[0])
    if not match:
        raise ValueError(f"entry {ordinal} has an invalid ID")
    identifier, decimal = match.groups()
    amount = int(decimal)
    if not 1 <= amount <= MAX_DELTA:
        raise ValueError(f"entry {ordinal} amount is outside 1..{MAX_DELTA}")
    if lines[1] != 'type "StatusData"':
        raise ValueError(f"entry {ordinal} has unexpected inheritance or type")
    if identifier in seen_ids:
        raise ValueError(f"duplicate ID {identifier}")
    seen_ids.add(identifier)
    if amount in seen_amounts:
        raise ValueError(f"duplicate amount {amount}")
    seen_amounts.add(amount)

    fields = {}
    for line in lines[2:]:
        data_match = _DATA.fullmatch(line)
        if not data_match:
            raise ValueError(f"entry {ordinal} has malformed data")
        name, value = data_match.groups()
        if name in fields:
            raise ValueError(f"entry {ordinal} repeats field {name}")
        fields[name] = value
    required_names = {*_REQUIRED_FIELDS, "StackId", "Boosts"}
    if set(fields) != required_names:
        raise ValueError(f"entry {ordinal} has missing or extra fields")
    for name, expected in _REQUIRED_FIELDS.items():
        if fields[name] != expected:
            raise ValueError(f"entry {ordinal} has invalid {name}")
    if fields["StackId"] != identifier:
        raise ValueError(f"entry {ordinal} StackId does not match ID")
    if fields["StackId"] in seen_stack_ids:
        raise ValueError(f"duplicate StackId {fields['StackId']}")
    seen_stack_ids.add(fields["StackId"])
    if fields["Boosts"] != f"IncreaseMaxHP({amount});":
        raise ValueError(f"entry {ordinal} has an invalid boost")


def main(argv=None) -> int:
    """Run the safe catalog generate/check commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("generate", help="write a validated catalog to a new or identical path")
    generate.add_argument("--output", required=True, type=Path)
    check = commands.add_parser("check", help="validate a catalog without modifying it")
    check.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            text = render_catalog()
            receipt = validate_catalog(text)
            encoded = text.encode("utf-8")
            if args.output.exists():
                if args.output.read_bytes() != encoded:
                    raise ValueError(f"refusing to overwrite differing file: {args.output}")
            else:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_bytes(encoded)
        else:
            text = args.path.read_text(encoding="utf-8")
            receipt = validate_catalog(text)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"invalid catalog: {error}", file=sys.stderr)
        return 1
    print(f"valid catalog: count={receipt['count']} sha256={receipt['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
