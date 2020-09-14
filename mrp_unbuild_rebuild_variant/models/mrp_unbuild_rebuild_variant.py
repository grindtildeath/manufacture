# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class MrpUnbuildRebuildVariant(models.Model):

    _name = "mrp.unbuild.rebuild.variant"

    name = fields.Char()  # TODO Add sequence
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Done")],
        required=True,
        default="draft",
        readonly=True
    )
    unbuild_product_id = fields.Many2one("product.product")
    unbuild_bom_id = fields.Many2one("mrp.bom")
    unbuild_location_id = fields.Many2one("stock.location")
    # if unbuild product is tracked:
    unbuild_lot_id = fields.Many2one("stock.production.lot")
    # if unbuild product's bom includes tracked components:
    unbuild_original_mo_id = fields.Many2one("mrp.production")
    # if unbuild product's bom does not include tracked components:
    # TODO: handle uom
    quantity = fields.Float()

    # TODO: Domain for same product.template
    rebuild_product_id = fields.Many2one(
        "product.product",
        # FIXME: domain="[('product_tmpl_id', '=', 'unbuild_product_id.product_tmpl_id.id')]"
    )
    # TODO: Check if this bom could be different than unbuild_bom_id
    rebuild_bom_id = fields.Many2one("mrp.bom")
    rebuild_location_id = fields.Many2one("stock.location")
    rebuild_lot_id = fields.Many2one("stock.production.lot")

    unbuild_order_id = fields.Many2one(
        "mrp.unbuild", readonly=True
    )
    rebuild_order_id = fields.Many2one(
        "mrp.production", readonly=True
    )

    @api.onchange("unbuild_product_id")
    def _onchange_unbuild_product_id(self):
        # TODO reproduce the onchange from mrp.unbuild on product_id
        pass

    def process(self):
        self.ensure_one()
        unbuild_order = self.env["mrp.unbuild"].create(
            {
                "product_id": self.unbuild_product_id.id,
                "bom_id": self.unbuild_bom_id.id,

            }
        )
        unbuild_order.action_validate()

        rebuild_order = self.env["mrp.production"].create(
            {
                "product_id": self.rebuild_product_id.id,
                "bom_id": self.rebuild_bom_id.id,
            }
        )
        # TODO: Check how open_produce_product init this wizard and select
        #  needed stock.production.lot or quants
        produce_wizard = self.env["mrp.product.produce"].create(
            {

            }
        )
        produce_wizard.do_produce()

        self.write(
            {
                "state": "done",
                "unbuild_order_id": unbuild_order.id,
                "rebuild_order_id": rebuild_order.id,
            }
        )
