from odoo import _, api, fields, models


class ApiPosition(models.Model):
    _name = "api.position"
    _description = "Imported Position"
    _rec_name = "title"
    _order = "imported_at desc, id desc"

    title = fields.Char(required=True, readonly=True)
    description = fields.Text(readonly=True)
    project_number = fields.Integer(readonly=True)
    users_count = fields.Integer(string="Cvs", readonly=True)
    api_updated_at = fields.Datetime(string="Updated in source", readonly=True)
    imported_at = fields.Datetime(string="Imported at", readonly=True)
    token_hash = fields.Char(index=True, readonly=True, copy=False)
    attribute_ids = fields.One2many(
        "api.position.attribute", "position_id", string="Attributes", readonly=True
    )
    attribute_count = fields.Integer(compute="_compute_attribute_count", string="Attributes")

    @api.depends("attribute_ids")
    def _compute_attribute_count(self):
        for rec in self:
            rec.attribute_count = len(rec.attribute_ids)


class ApiPositionAttribute(models.Model):
    _name = "api.position.attribute"
    _description = "Imported Position Attribute"
    _order = "position_id, sequence, id"

    position_id = fields.Many2one(
        "api.position", required=True, ondelete="cascade", index=True, readonly=True
    )
    sequence = fields.Integer(readonly=True)
    remote_id = fields.Integer(string="Source ID", readonly=True)
    name = fields.Char(string="Title", readonly=True)
    category = fields.Char(readonly=True)
    description = fields.Text(readonly=True)
    type = fields.Char(readonly=True)
    options = fields.Char(string="Options", readonly=True)

    # Aggregated results, kept exactly as the source API reports them.
    agg_popular = fields.Char(string="Most popular", readonly=True)
    agg_min = fields.Char(string="Min", readonly=True)
    agg_max = fields.Char(string="Max", readonly=True)
    agg_avg = fields.Char(string="Average", readonly=True)
    aggregate_display = fields.Char(string="Aggregated result", compute="_compute_aggregate_display")

    @api.depends("agg_popular", "agg_min", "agg_max", "agg_avg")
    def _compute_aggregate_display(self):
        for rec in self:
            parts = []
            if rec.agg_popular:
                parts.append(_("Most popular: %s") % rec.agg_popular)
            if rec.agg_min:
                parts.append(_("Min: %s") % rec.agg_min)
            if rec.agg_max:
                parts.append(_("Max: %s") % rec.agg_max)
            if rec.agg_avg:
                parts.append(_("Avg: %s") % rec.agg_avg)
            rec.aggregate_display = " | ".join(parts)
