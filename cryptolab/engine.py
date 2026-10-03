"""Evaluate transfer maturity against source depth, challenge windows and explicit chain halts."""

from .common import (
    number,
    integer,
    identity,
    records,
    chronology,
    allocate,
    result,
    validate_document,
)
from decimal import Decimal


def _analyze(d):
    now = integer(d["now"])
    rules = {identity(r["chain"]): r for r in records(d["chains"], "chain")}
    rows = []
    for t in records(d["transfers"], "id"):
        chain = identity(t["chain"])
        if chain not in rules:
            raise ValueError("unknown chain")
        rule = rules[chain]
        head = integer(rule["head"])
        height = integer(t["height"])
        submitted = integer(t["submitted_at"])
        required = integer(rule["confirmations"], 1)
        delay = integer(rule["challenge_seconds"])
        if height > head or submitted > now:
            raise ValueError("future transfer")
        halted = rule.get("halted", False)
        if not isinstance(halted, bool):
            raise ValueError("halted must be boolean")
        confirmations = head - height + 1
        mature = now - submitted >= delay
        rows.append(
            {
                "id": t["id"],
                "confirmations": confirmations,
                "blocks_remaining": max(required - confirmations, 0),
                "seconds_remaining": max(delay - (now - submitted), 0),
                "ready": confirmations >= required and mature and not halted,
            }
        )
    return {"transfers": rows, "ready_count": sum(r["ready"] for r in rows)}


def analyze(document):
    validate_document(document)
    try:
        return result(_analyze(document))
    except (KeyError, TypeError, ArithmeticError, RecursionError) as error:
        raise ValueError("invalid domain input: " + str(error)) from error
