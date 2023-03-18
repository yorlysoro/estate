# -*- coding: utf-8 -*-

from odoo import fields, models

class EstatePropertyType(models.Model):
	_name = "estate.property.tag"
	_description = "Real Estate Property Tag"
	_order = "name"
	_sql_constraints = [
		("check_name", "UNIQUE(name)", "The name must be unique"),
	]

	name = fields.Char(
		string="Name",
		required=True
	)
	color = fields.Integer(
		string="Color Index"
	)
