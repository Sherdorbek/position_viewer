"""Pure helpers that turn the API payload into values for Odoo records.

Nothing in here imports Odoo, so it can be tested on its own.
"""
import hashlib
from datetime import datetime, timezone


def token_digest(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def parse_datetime(value):
    """ISO 8601 string -> naive UTC datetime (what Odoo stores), or False."""
    if not value or not isinstance(value, str):
        return False
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _text(value):
    if value is None or value is False or value == "":
        return ""
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    return str(value)


def _two_decimals(value):
    try:
        return "%.2f" % float(value)
    except (TypeError, ValueError):
        return _text(value)


def parse_aggregate(aggregate):
    """Aggregate is {'popular': ...} for text, {'min','max','avg'} for numbers,
    and [] (an empty list) when there is nothing to aggregate."""
    if not isinstance(aggregate, dict):
        aggregate = {}
    avg = aggregate.get("avg")
    return {
        "agg_popular": _text(aggregate.get("popular")),
        "agg_min": _text(aggregate.get("min")),
        "agg_max": _text(aggregate.get("max")),
        "agg_avg": _two_decimals(avg) if avg not in (None, "") else "",
    }


def parse_position(data):
    """Return (position_vals, [attribute_vals, ...]); raise ValueError if invalid."""
    if not isinstance(data, dict):
        raise ValueError("The response is not a JSON object.")
    title = (data.get("title") or "").strip()
    if not title:
        raise ValueError("The response has no 'title'.")

    attributes = []
    raw_attributes = data.get("attributes")
    for index, attr in enumerate(raw_attributes if isinstance(raw_attributes, list) else [], start=1):
        if not isinstance(attr, dict):
            continue
        options = attr.get("oneOfManies") or []
        values = {
            "sequence": index * 10,
            "remote_id": attr.get("id") or 0,
            "name": attr.get("name") or "",
            "category": attr.get("categoryName") or "",
            "description": attr.get("description") or "",
            "type": attr.get("type") or "",
            "options": ", ".join(
                str(o.get("value", "")) for o in options if isinstance(o, dict)
            ),
        }
        values.update(parse_aggregate(attr.get("aggregate")))
        attributes.append(values)

    users = data.get("users")
    position = {
        "title": title,
        "description": data.get("description") or "",
        "project_number": data.get("projectNumber") or 0,
        "users_count": len(users) if isinstance(users, list) else 0,
        "api_updated_at": parse_datetime(data.get("updatedAt")),
    }
    return position, attributes
