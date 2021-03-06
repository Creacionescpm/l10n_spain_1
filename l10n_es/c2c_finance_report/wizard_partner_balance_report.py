##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import time
import wizard
import pooler

report_type =  '''<?xml version="1.0"?>
<form string="Select Report Type">
</form>'''


dates_form = '''<?xml version="1.0"?>
<form string="Select period">
	<field name="company_id" colspan="4"/>
	<newline/>
	<field name="date1"/>
	<field name="date2"/>
	<newline/>
	<field name="result_selection"/>
	<field name="soldeinit"/>
	<field name="amount_currency"/>
	
</form>'''

dates_fields = {
	'company_id': {'string': 'Company', 'type': 'many2one', 'relation': 'res.company', 'required': True},
	'result_selection':{'string':"Display partner ",'type':'selection','selection':[('customer','Debiteur'),('supplier','Creancier'),('all','Tous')]},
	'soldeinit':{'string':"Inclure les soldes initiaux",'type':'boolean'},
	'date1': {'string':'Start date', 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-01-01')},
	'date2': {'string':'End date', 'type':'date', 'required':True, 'default': lambda *a: time.strftime('%Y-%m-%d')},
	'amount_currency':{'string':"with amount in currency",'type':'boolean'},

}

period_form = '''<?xml version="1.0"?>
<form string="Select period">
	<field name="company_id" colspan="4"/>
	<newline/>
	<field name="fiscalyear" colspan="4"/>
	<field name="periods" colspan="4"/>
	<newline/>
	<field name="result_selection"/>
	<field name="soldeinit"/>
	<field name="amount_currency"/>
</form>'''

period_fields = {
	'company_id': {'string': 'Company', 'type': 'many2one', 'relation': 'res.company', 'required': True},
	'fiscalyear': {'string': 'Fiscal year', 'type': 'many2one', 'relation': 'account.fiscalyear',
		'help': 'Keep empty for all open fiscal year'},
	'periods': {'string': 'Periods', 'type': 'many2many', 'relation': 'account.period', 'help': 'All periods if empty'},
	'result_selection':{'string':"Display partner",'type':'selection','selection':[('customer','Debiteur'),('supplier','Creancier'),('all','Tous')]},
	'soldeinit':{'string':"Inclure les soldes initiaux",'type':'boolean'},
	'amount_currency':{'string':"with amount in currency",'type':'boolean'}
}


class wizard_reportc2c(wizard.interface):
	def _get_defaults(self, cr, uid, data, context):
		fiscalyear_obj = pooler.get_pool(cr.dbname).get('account.fiscalyear')
		data['form']['fiscalyear'] = fiscalyear_obj.find(cr, uid)

		user = pooler.get_pool(cr.dbname).get('res.users').browse(cr, uid, uid, context=context)
		if user.company_id:
			company_id = user.company_id.id
		else:
			company_id = pooler.get_pool(cr.dbname).get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]
		data['form']['company_id'] = company_id
		data['form']['soldeinit'] = True
		data['form']['result_selection'] = 'all'
		return data['form']
	
	def _get_defaults_fordate(self, cr, uid, data, context):
		user = pooler.get_pool(cr.dbname).get('res.users').browse(cr, uid, uid, context=context)
		if user.company_id:
			company_id = user.company_id.id
		else:
			company_id = pooler.get_pool(cr.dbname).get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]
		data['form']['company_id'] = company_id
		data['form']['soldeinit'] = True
		data['form']['result_selection'] = 'all'
		return data['form']
	
	def _check_date(self, cr, uid, data, context):
		sql = """
			SELECT f.id, f.date_start, f.date_stop FROM account_fiscalyear f  Where '%s' between f.date_start and f.date_stop """%(data['form']['date1'])
		cr.execute(sql)
		res = cr.dictfetchall()
		if res:
			if (data['form']['date2'] > res[0]['date_stop'] or data['form']['date2'] < res[0]['date_start']):
				raise  wizard.except_wizard('UserError','Date to must be set between ' + res[0]['date_start'] + " and " + res[0]['date_stop'])
			else:
				return 'report'
			
		else:
			raise wizard.except_wizard('UserError','Date not in a defined fiscal year')


	states = {
		'init': {
			'actions': [],
			'result': {'type':'form', 'arch':report_type,'fields':{}, 'state':[('with_period','Use with Period'),('with_date','Use with Date')]}
		},
		'with_period': {
			'actions': [_get_defaults],
			'result': {'type':'form', 'arch':period_form, 'fields':period_fields, 'state':[('end','Cancel'),('report','Print')]}
		},
		'with_date': {
			'actions': [_get_defaults_fordate],
			'result': {'type':'form', 'arch':dates_form, 'fields':dates_fields, 'state':[('end','Cancel'),('checkdate','Print')]}
		},
		'checkdate': {
			'actions': [],
			'result': {'type':'choice','next_state':_check_date}
		},
		
		'report': {
			'actions': [],
			'result': {'type':'print', 'report':'account.partner.balancec2c', 'state':'end'}
		}
	}
wizard_reportc2c('account.partner.balance.reportc2c')

