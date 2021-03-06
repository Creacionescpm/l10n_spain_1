##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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
import pooler
import rml_parse
from report import report_sxw

class aged_trial_reportc2c(rml_parse.rml_parse):
	
	def __init__(self, cr, uid, name, context):
		super(aged_trial_reportc2c, self).__init__(cr, uid, name, context)
		self.line_query = ''
		self.total_account = []
		
		self.localcontext.update({
			'time': time,
			'get_lines': self._get_lines,
			'get_total': self._get_total,
			'get_direction': self._get_direction,
			'get_for_period': self._get_for_period,
			'get_company': self._get_company,
			'get_currency': self._get_currency,
		})

	def _add_header(self, node):
		return True

	def _get_lines(self, form):
		if (form['result_selection'] == 'customer' ):
			self.ACCOUNT_TYPE = "('receivable')"
		elif (form['result_selection'] == 'supplier'):
			self.ACCOUNT_TYPE = "('payable')"
		else:
			self.ACCOUNT_TYPE = "('payable','receivable')"
			

		res = []
		account_move_line_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
		self.line_query = account_move_line_obj._query_get(self.cr, self.uid, obj='line',
				context={'fiscalyear': form['fiscalyear']})
		self.cr.execute("SELECT DISTINCT res_partner.id AS id, " \
					"res_partner.name AS name " \
				"FROM res_partner,account_move_line AS line, account_account,account_move_reconcile AS recon " \
				"WHERE (line.account_id=account_account.id) " \
					"AND ((reconcile_id IS NULL) " \
					"OR (reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s ))) " \
					"AND (line.partner_id=res_partner.id) " \
					"AND (account_account.company_id = %d) " \
				"ORDER BY res_partner.name", (form['date1'],form['company_id']))
		partners = self.cr.dictfetchall()
		## mise a 0 du total
		for i in range(7):
			self.total_account.append(0)
		#
		
		for partner in partners:
			values = {}
			## If choise selection is in the future
			if form['direction_selection'] == 'future':
				self.cr.execute("SELECT SUM(debit-credit) " \
					"FROM account_move_line AS line, account_account " \
					"WHERE (line.account_id=account_account.id) " \
						"AND (account_account.type IN " + self.ACCOUNT_TYPE + ") " \
						"AND (COALESCE(date_maturity,date) < %s) AND (partner_id=%d) " \
						"AND ((reconcile_id IS NULL) " \
						"OR (reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s ))) " \
						"AND (account_account.company_id = %d) " \
						"AND account_account.active",
						(form['date1'], partner['id'],form['date1'], form['company_id']))
				before = self.cr.fetchone()
				self.total_account[6] = self.total_account[6] + (before and before[0] or 0.0)

				values['direction'] = before and before[0] or 0.0
			else:
				self.cr.execute("SELECT SUM(debit-credit) " \
					"FROM account_move_line AS line, account_account " \
					"WHERE (line.account_id=account_account.id) " \
						"AND (account_account.type IN " + self.ACCOUNT_TYPE + ") " \
						"AND (COALESCE(date_maturity,date) > %s) AND (partner_id=%d) " \
						"AND ((reconcile_id IS NULL) " \
						"OR (reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s ))) " \
						"AND (account_account.company_id = %d) " \
						"AND account_account.active",
						(form['date1'], partner['id'],form['date1'], form['company_id']))
				after = self.cr.fetchone()
				self.total_account[6] = self.total_account[6] + (after and after[0] or 0.0)
				values['direction'] = after and after[0] or ""
				#print str(values['direction'])
			for i in range(5):
				self.cr.execute("SELECT SUM(debit-credit) " \
						"FROM account_move_line AS line, account_account " \
						"WHERE (line.account_id=account_account.id) " \
							"AND (account_account.type IN " + self.ACCOUNT_TYPE + ") " \
							"AND (COALESCE(date_maturity,date) BETWEEN %s AND  %s) " \
							"AND (partner_id = %d) " \
							"AND ((reconcile_id IS NULL) " \
							"OR (reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s ))) " \
							"AND (account_account.company_id = %d) " \
							"AND account_account.active",
							(form[str(i)]['start'], form[str(i)]['stop'],partner['id'],form['date1'] ,form['company_id']))
				during = self.cr.fetchone()
				# Ajout du compteur
				self.total_account[(i)] = self.total_account[(i)] + (during and during[0] or 0)

				#print str(during)
				values[str(i)] = during and during[0] or ""
			self.cr.execute("SELECT SUM(debit-credit) " \
					"FROM account_move_line AS line, account_account " \
					"WHERE (line.account_id = account_account.id) " \
						"AND (account_account.type IN " + self.ACCOUNT_TYPE + ") " \
						"AND (partner_id = %d) " \
						"AND ((reconcile_id IS NULL) " \
						"OR (reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s ))) " \
						"AND (account_account.company_id = %d) " \
						"AND account_account.active",
						(partner['id'],form['date1'],form['company_id']))
			total = self.cr.fetchone()
			values['total'] = total and total[0] or 0.0
			## Add for total
			self.total_account[(i+1)] = self.total_account[(i+1)] + (total and total[0] or 0.0)
			
			values['name'] = partner['name']
			#t = 0.0
			#for i in range(5)+['direction']:
			#	t+= float(values.get(str(i), 0.0) or 0.0)
			#values['total'] = t
			
			if values['total']:
				
				res.append(values)
		total = 0.0
		totals = {}
		for r in res:
			total += float(r['total'] or 0.0)
			for i in range(5)+['direction']:
				totals.setdefault(str(i), 0.0)
				totals[str(i)] += float(r[str(i)] or 0.0)
		return res

	def _get_total(self, pos):
		period = self.total_account[int(pos)]
		return period 


	def _get_direction(self,pos):
		period = self.total_account[int(pos)]
		return period 

	def _get_for_period(self,pos):
		
		period = self.total_account[int(pos)]
		return period 

	def _get_company(self, form):
		return pooler.get_pool(self.cr.dbname).get('res.company').browse(self.cr, self.uid, form['company_id']).name

	def _get_currency(self, form):
		return pooler.get_pool(self.cr.dbname).get('res.company').browse(self.cr, self.uid, form['company_id']).currency_id.name


report_sxw.report_sxw(
	'report.aged.trial.balancec2c',
	'res.partner',
	'addons/c2c_finance_report/aged_trial_balance.rml',
	parser=aged_trial_reportc2c, header=False)
