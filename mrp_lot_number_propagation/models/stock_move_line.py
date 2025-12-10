# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _get_manufacturing_order_with_propagated_serial(self):
        # Search into backorders from the linked production for a MOs whose finished
        #  serial number match the one from the propagating move line
        self.ensure_one()
        return self.production_id.procurement_group_id.mrp_production_ids.filtered(
            lambda prod: prod.lot_producing_id.name == self.lot_id.name
        )

    def unlink(self):
        # When a manufacturing order is split through the produce all wizard,
        #  the serial numbers of the finished product is created and written on each
        #  backorder MO, before move lines are unlinked from the original MO and
        #  created again on the Backorder
        # Since the propagation feature now created the stock.lot record when the MO
        #  is marked as done, we remove the serial and unlink it, in case it does not
        #  exist
        propagating_move_lines = self.filtered(
            lambda ml: ml.move_id.propagate_lot_number
        )
        for prop_ml in propagating_move_lines:
            propagated_prod = prop_ml._get_manufacturing_order_with_propagated_serial()
            lot = propagated_prod.lot_producing_id
            propagated_prod.write({"lot_producing_id": False})
            if not lot.quant_ids:
                lot.unlink()
        return super().unlink()
