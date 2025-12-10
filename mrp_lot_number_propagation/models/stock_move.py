# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    propagate_lot_number = fields.Boolean(
        default=False,
        readonly=True,
    )

    def _action_assign(self, force_qty=False):
        res = super()._action_assign(force_qty=force_qty)
        for move in self:
            finished_lot = move.raw_material_production_id.lot_producing_id
            if (
                move.propagate_lot_number
                and finished_lot
                and len(move.move_line_ids) == 1
                and move.move_line_ids.lot_id.name != finished_lot.name
            ):
                move.raw_material_production_id.write({"lot_producing_id": False})
                if not finished_lot.quant_ids:
                    finished_lot.unlink()
        return res
