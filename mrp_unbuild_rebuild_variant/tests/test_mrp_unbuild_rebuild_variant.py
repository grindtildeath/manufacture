# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.tests import SavepointCase


class TestMrpUnbuildRebuildVariant(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        ref = cls.env.ref

        # Ref products
        cls.product_amplifier_phono_tuner = ref(
            "mrp_unbuild_rebuild_variant.product_product_amplifier_with_phono_with_tuner"
        )
        cls.product_amplifier_tuner = ref(
            "mrp_unbuild_rebuild_variant.product_product_amplifier_without_phono_with_tuner"
        )
        cls.product_amplifier_phono = ref(
            "mrp_unbuild_rebuild_variant.product_product_amplifier_with_phono_without_tuner"
        )
        cls.product_amp_case = ref(
            "mrp_unbuild_rebuild_variant.product_product_amplifier_case"
        )
        cls.product_amp_preamp = ref(
            "mrp_unbuild_rebuild_variant.product_product_amplifier_preamp"
        )
        cls.product_amp_power_amp = ref(
            "mrp_unbuild_rebuild_variant.product_product_amplifier_power_amp"
        )
        cls.product_amp_phono = ref(
            "mrp_unbuild_rebuild_variant.product_product_amplifier_phono"
        )
        cls.product_amp_tuner = ref(
            "mrp_unbuild_rebuild_variant.product_product_amplifier_tuner"
        )

        # Ref bom, locations
        cls.amplifier_bom = ref(
            "mrp_unbuild_rebuild_variant.mrp_bom_amplifier"
        )
        cls.stock_location = ref("stock.stock_location_stock")

        # Init inventory
        inventory_matrix = {
            cls.product_amp_case: ["000123", "000124"],
            cls.product_amp_preamp: ["100456", "100457"],
            cls.product_amp_power_amp: ["200789", "200790"],
            cls.product_amp_phono: ["300321", "300322"],
            cls.product_amp_tuner: ["400654", "400655"],
        }
        for product, serials in inventory_matrix.items():
            for number in serials:
                lot = cls._create_lot_number(product, number)
                cls.env["stock.quant"]._update_available_quantity(
                    product, cls.stock_location, 1.0, lot_id=lot
                )

        # Create original manufacturing orders
        cls.amplifier_phono_tuner_50001_mo = cls._create_manufacturing_order(
            cls.product_amplifier_phono_tuner, 1.0, cls.amplifier_bom
        )
        cls.amplifier_phono_tuner_50001_mo.action_assign()
        # Ensure serials are mapped correctly (shouldn't be necessary if no
        #  other addons changes assignation rules, but let's be safe)
        inventory_matrix = {
            cls.product_amp_case: "000123",
            cls.product_amp_preamp: "100456",
            cls.product_amp_power_amp: "200789",
            cls.product_amp_phono: "300321",
            cls.product_amp_tuner: "400654",
        }
        for move in cls.amplifier_phono_tuner_50001_mo.move_raw_ids:
            raw_product = move.product_id
            move_line = move.move_line_ids
            serial_to_use = inventory_matrix.get(raw_product)
            if move_line.lot_id.name != serial_to_use:
                raw_lot = cls.env["stock.production.lot"].search(
                    {
                        "product_id": raw_product.id,
                        "name": serial_to_use,
                    }
                )
                move_line.lot_id = raw_lot.id
        produce_wiz = cls.env["mrp.product.produce"].with_context(
            active_id=cls.amplifier_phono_tuner_50001_mo.id
        ).create({})
        cls.lot_50001 = cls._create_lot_number(cls.product_amplifier_phono_tuner, "50001")
        produce_wiz.lot_id = cls.lot_50001
        produce_wiz.do_produce()

    @classmethod
    def _create_lot_number(cls, product, lot_number):
        return cls.env["stock.production.lot"].create(
            {
                "product_id": product.id,
                "name": lot_number,
            }
        )

    @classmethod
    def _create_manufacturing_order(cls, product, product_qty, bom):
        return cls.env["mrp.production"].create(
            {
                "product_id": product.id,
                "product_qty": product_qty,
                "product_uom_id": product.uom_id.id,
                "bom_id": bom.id,
            }
        )

    def test_unbuild_rebuild(self):
        lot_60001 = self._create_lot_number(
            self.product_amplifier_phono_tuner, "60001"
        )
        rebuild_order = self.env["mrp.unbuild.rebuild.variant"].create(
            {
                "unbuild_product_id": self.product_amplifier_phono_tuner.id,
                "unbuild_lot_id": self.lot_50001.id,
                "quantity": 1.0,
                "rebuild_product_id": self.product_amplifier_tuner.id,
                "rebuild_lot_id": lot_60001.id,
            }
        )
        qty_amplifier_phono_tuner_in_stock = self.env["stock.quant"]._get_available_quantity(
            self.product_amplifier_phono_tuner, self.stock_location
        )
        self.assertAlmostEqual(qty_amplifier_phono_tuner_in_stock, 0.0)
        rebuild_order.process()
        qty_amplifier_phono_tuner_in_stock = self.env[
            "stock.quant"]._get_available_quantity(
            self.product_amplifier_phono_tuner, self.stock_location
        )
        self.assertAlmostEqual(qty_amplifier_phono_tuner_in_stock, 1.0)
