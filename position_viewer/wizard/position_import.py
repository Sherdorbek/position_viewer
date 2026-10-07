import logging

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError

from . import api_parser

_logger = logging.getLogger(__name__)

# TODO: put your real REST endpoint here.
API_URL = "https://task4.alwaysdata.net/api/position"
API_TIMEOUT = 20  # seconds


class PositionImport(models.TransientModel):
    _name = "position.import"
    _description = "Import Position from API"

    # Not required at database level: the token is cleared after the import.
    # The form view marks it as required for the user.
    access_token = fields.Char(string="Access Token")

    def _fetch_payload(self):
        self.ensure_one()
        headers = {
            "Authorization": "Bearer %s" % self.access_token.strip(),
            "Accept": "application/json",
        }
        try:
            response = requests.get(API_URL, headers=headers, timeout=API_TIMEOUT)
        except requests.exceptions.RequestException as exc:
            _logger.warning("Position API request failed: %s", exc)
            raise UserError(_("Could not reach the API: %s") % exc)

        if response.status_code in (401, 403):
            raise UserError(_("The API rejected the access token (HTTP %s).") % response.status_code)
        if not response.ok:
            raise UserError(_("The API returned an error (HTTP %s).") % response.status_code)
        try:
            return response.json()
        except ValueError:
            raise UserError(_("The API did not return valid JSON."))

    def action_import(self):
        self.ensure_one()
        if not (self.access_token or "").strip():
            raise UserError(_("Please enter an access token."))
        data = self._fetch_payload()
        try:
            position_vals, attribute_vals = api_parser.parse_position(data)
        except ValueError as exc:
            raise UserError(_("Unexpected API response: %s") % exc)

        token_hash = api_parser.token_digest(self.access_token.strip())
        position_vals.update(
            token_hash=token_hash,
            imported_at=fields.Datetime.now(),
            attribute_ids=[(5, 0, 0)] + [(0, 0, vals) for vals in attribute_vals],
        )

        # The viewer is read-only for users, so the import writes with sudo().
        Position = self.env["api.position"].sudo()
        position = Position.search([("token_hash", "=", token_hash)], limit=1)
        if position:
            position.write(position_vals)  # same token -> refresh the same position
        else:
            position = Position.create(position_vals)

        # Do not keep the token in the database.
        self.access_token = False

        return {
            "type": "ir.actions.act_window",
            "res_model": "api.position",
            "res_id": position.id,
            "view_mode": "form",
            "target": "current",
        }
