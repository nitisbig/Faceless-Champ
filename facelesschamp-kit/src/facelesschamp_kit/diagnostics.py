"""Stable errors shared by Python services and the CLI."""

import math


class KitError(ValueError):
    def __init__(self, code, message, **scope):
        self.code, self.message, self.scope = code, message, scope
        super().__init__(f"{code}: {message}" + (f" ({scope})" if scope else ""))

    def as_dict(self):
        return {"code": self.code, "message": self.message, **self.scope}


def number(value, name, minimum=0, positive=False):
    if isinstance(value, bool):
        raise KitError("INVALID_VALUE", f"{name} must be a finite number")
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise KitError("INVALID_VALUE", f"{name} must be a finite number") from None
    if not math.isfinite(value) or value < minimum or (positive and value == minimum):
        raise KitError("INVALID_VALUE", f"{name} must be finite and {'>' if positive else '>='} {minimum}")
    return value


def fields(value, allowed, scope):
    if not isinstance(value, dict):
        raise KitError("CONFIG", f"{scope} must be a table")
    unknown = value.keys() - set(allowed)
    if unknown:
        raise KitError("CONFIG", f"Unknown fields in {scope}: {', '.join(sorted(unknown))}")
