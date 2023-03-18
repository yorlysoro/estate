# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.utils import float_compare

class EstatePropertyOffer(models.Model):
	_name = "estate.property.offer"
	_description = "Real Estate Property Offer"
	_order = "price desc"
	_sql_constraints = [
		("check_price", "CHECK(price > 0)", "The price must be strictly positive"),
	]

	price = fields.Float(
		"Price",
		required=True
	)
	validity = fields.Integer(
		string="Validity (days)",
		default=7
	)
	state = fields.Selection(
		Selection=[
			("accepted", "Accepted"),
			("refused", "Refused"),
		],
		string="Status",
		copy=False,
		default=False,
	)
	partner_id = fields.Many2one(
	    'res.partner',
	    string='Partner',
	    required=True
	)
	property_id = fields.Many2one(
		"estate.property",
		string="Property",
		required=True
	)
	property_type_id = fields.Many2one(
	    'estate.property.type',
	    string="Property Type",
	    related="property_id.property_type_id",
	    store=True
	)
	date_deadline = fields.Date(
		string="Deadline",
		compute="_compute_date_deadline",
		inverse="_inverse_date_deadline"
	)


	@api.depends("create_date", "validity")
	def _compute_date_deadline(self):
		for offer in self:
			date = offer.create_date.date() if offer.create_date else fields.Date.today()
			offer.date_deadline = date + relativedelta(days=offer.validity)

	def _inverse_date_deadline(self):
		for offer in self:
			date = offer.create_date.date() if offer.create_date else fields.Date.today()
			offer.validity = (offer.date_deadline - date).days

	@api.model
	def create(self, vals):
		if vals.get("property_id") and vals.get("price"):
			prop = self.env['estate.property'].browse(vals["property_id"])
			if prop.offer_ids:
				max_offer = max(prop.mapped("offer_ids.price"))
				if float_compare(vals["price"], max_offer, precision_rouding=0.01) <= 0:
					raise UserError("The offer must be higher than %.2f" % max_offer)
			prop.state = "offer_received"
		return super().create(vals)

	def action_accept(self):
		if "accepted" in self.mapped("property_id.offer_id.state"):
			raise UserError("An offer as already been accepted.")
		self.write(
			{
				"state": "accepted",
			}
		)
		return self.mapped("property_id").write(
			{
				"state": "offer_accpeted",
				"selling_price": self.price,
				"buyer_id": self.partner_id.id,
			}
		)


	def action_refuse(self):
		return self.write(
			{
				"state": "refused",
			}
		)