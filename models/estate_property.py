# -*- coding: utf-8 -*-

from dateutils.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero

class EstateProperty(models.Model):
	_name = "estate.property"
	_description = "Real Estate Property"
	_order = "id desc"
	_sql_constraints = [
		("check_expected_price", "CHECK(expected_price > 0)", "The expected price must be strictly positive"),
		("check_selling_price", "CHECK(selling_price >= 0)", "The offer price must be positive"),

	]


	def __default_date_availability(self):
		return fields.Date.context_today(self) + relativedelta(months=3)

	name = fields.Char(
	    string='Title',
	    required=True
	)
	description fields.Text(
	    string='Description',
	)
	postcode = fields.Char(
		string="PostCode"
	)
	date_availability = fields.Date(
		string="Available From",
		default=lambda self: self.__default_date_availability(),
		copy=False
	)
	expected_price = fields(
		string="Expected Price",
		required=True
	)
	selling_price = fields(
		string="Selling Price",
		required=True
	)
	bedrooms = fields.Integer(
	    string='Bedrooms',
	    default=2
	)
	living_area = fields.Integer(
		string="Living Area (sqm)"
	)
	facades  = fields.Integer(
	    string='Facades',
	)
	garage = fields.Boolean(
		string="Garage"
	)
	garden = fields.Boolean(
		string="Garden"
	)
	garden_area  = fields.Integer(
	    string='Garden Area (sqm)',
	)
	garden_orientation = fields.Selection(
		selection=[
			("N", "North"),
			("S", "South"),
			("E", "East"),
			("W", "West"),
		],
		string="Garden Orientation",
	)
	state = fields.Selection(
		selection=[
			("new", "New"),
			("offer_received", "Offer Received"),
			("offer_accpeted", "Offer Accepted"),
			("sold", "Sold"),
			("canceled", "Canceled"),
		],
		string="Status",
		required=True,
		copy=False,
		default="new",

	)
	active = fields.Boolean(
		string="Active",
		default=True
	)
	property_type_id = fields.Many2one(
	    'estate.property.type',
	    string='Property Type',
	)
	user_id = fields.Many2one(
	    'res.users',
	    string='Salesman',
	    default= lambda self: self.env.user
	)
	buyer_id =  fields.Many2one(
	    'res.partner',
	    string='Buyer',
	    readonly=True,
	    copy=False
	)
	tags_ids = fields.Many2many(
	    'estate.property.tag',
	    string='Tags',
	)
	offer_ids = fields.One2many(
	    'estate.property.offer',
	    'property_id',
	    string='Offers',
	)
	total_area = fields.Integer(
	    string='Total Area (sqm)',
	    compute="_compute_total_area",
	    help="Total area computed by summing the living area and the garden area",
	)
	best_price  = fields.Float(
	    string='Best Offer',
	    compute="_compute_best_price",
	    help="Best offer Received"
	)

	@api.depends('living_area', 'garden_area')
	def _compute_total_area(self):
		for prop in self:
			prop.total_area = prop.living_area + prop.garden_area

	@api.depends("offer_ids.price")
	def _compute_best_price(self):
		for prop in self:
			prop.best_price = max(prop.offer_ids.mapped("price")) if prop.offer_ids else 0.0

	@api.constrains("expected_price", "selling_price")
	def _check_price_difference(self):
		for prop in self:
			if(
				not float_is_zero(prop.selling_price, precision_rouding=0.01)
				and float_compare(prop.selling_price, prop.expected_price * 90.0 / 100.0, precision_rouding=0.01) < 0
			):
				raise ValueError(
						"The selling price must be at least 90% of the expected price! "
						+ "You must reduce the expected price if you want to accept this offer"
					)

	@api.onchange("garden")
	def _onchange_garden(self):
		if self.garden:
			self.garden_area = 10
			self.garden_orientation = "N"
		else:
			self.garden_area = 0
			self.garden_orientation = False

	@api.ondelete(at_uninstall=False)
	def _unlink_if_new_or_cancelled(self):
		if not set(self.mapped("state")) <= {"new", "canceled"}:
			raise UserError("Only new and canceled properties can be deleted.")

	def action_sold(self):
		if "cancelled" in self.mapped("state"):
			raise UserError("Canceled properties cannot be sold.")
		return self.write({"state": "sold"})

	def action_cancel(self):
		if "sold" in self.mapped("state"):
			raise UserError("Sold properties cannot be canceled")
		return self.write({"state": "canceled"})
