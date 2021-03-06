##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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
import locale
from report import report_sxw

#from addons.account.wizard import wizard_account_balance_report

parents = {
    'tr':1,
    'li':1,
    'story': 0,
    'section': 0
}

class account_report_bs(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_report_bs, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'lines': self.lines,
            'fiscalyear': self.fiscalyear,
        })
        self.context = context

    def fiscalyear(self, form):
        """Returns name of the fiscal year and optional periods"""
        res = self.pool.get('account.fiscalyear').browse(self.cr, self.uid, form['fiscalyear']).name
        if form['periods'][0][2]:
            res += ': '
            for period in self.pool.get('account.period').browse(self.cr, self.uid, sorted(form['periods'][0][2])):
                res += period.name + ', '
            res = res [:-2]
        return res

    def line_total(self,line_id,ctx):
        _total = 0
        bsline= self.pool.get('account.report.bs').browse(self.cr,self.uid,[line_id])[0]
        bsline_accids = bsline.account_id
        res =self.pool.get('account.report.bs').read(self.cr,self.uid,[line_id],['account_id','child_id'])[0]
        for acc_id in res['account_id']:
            acc = self.pool.get('account.account').browse(self.cr,self.uid,[acc_id],ctx)[0]
            _total += acc.balance
        bsline_reportbs = res['child_id']

        for report in bsline_reportbs:
            _total +=self.line_total(report,ctx)
        return     _total

    def lines(self, form, ids={}, done=None, level=1):
        if not ids:
            ids = self.ids
        if not ids:
            return []
        if not done:
            done={}
        result = []
        ctx = self.context.copy()
        ctx['fiscalyear'] = form['fiscalyear']
        ctx['periods'] = form['periods'][0][2]
        report_objs = self.pool.get('account.report.bs').browse(self.cr, self.uid, ids)
        title_name = False
        if level==1:
            title_name = report_objs[0].name
        def cmp_code(x, y):
            return cmp(x.sequence, y.sequence)
        report_objs.sort(cmp_code)

        for report_obj in report_objs:
            if report_obj.id in done:
                continue
            done[report_obj.id] = 1
            color_font = ''
            color_back = ''
            if report_obj.color_font:
                color_font = report_obj.color_font.name
            if report_obj.color_back:
                color_back = report_obj.color_back.name

            res = {
                'code': report_obj.code,
                'name': report_obj.name,
                'level': level,
                'balance': self.line_total(report_obj.id,ctx),
                'color_font':color_font,
                'color_back':color_back,
                'font_style' : report_obj.font_style
            }
            result.append(res)
            report_type = report_obj.report_type
            if report_type != 'only_obj':
                account_ids = self.pool.get('account.report.bs').read(self.cr,self.uid,[report_obj.id],['account_id'])[0]['account_id']
                for account_id in account_ids:
                    res1 = self.check_child_id(account_id,level,ctx,report_type)
                    result += res1

            if report_obj.child_id:
                ids2 = [(x.code,x.id) for x in report_obj.child_id]
                ids2.sort()
                result += self.lines(form, [x[1] for x in ids2], done, level+1)

        return result

    def check_child_id(self,account_id,level,ctx,report_type):
        account = self.pool.get('account.account').browse(self.cr,self.uid,[account_id],ctx)[0]
        result = []
        res = {
            'code': account.code,
            'name': account.name,
            'level': level+1,
            'balance': account.balance,
            'color_font' : 'black',
            'color_back' :'pink',
            'font_style' : 'Helvetica-BoldOblique',
            }
        result.append(res)
        if report_type != 'with_account':
            acc_child_id  = self.pool.get('account.account').search(self.cr,self.uid,[('parent_id','=',[account_id]),('type','=','view')])
            for child_id in acc_child_id :
                result += self.check_child_id(child_id,level+1,ctx,report_type)
        return result



#    def _sum_credit(self):
#        return self.sum_credit
#
#    def _sum_debit(self):
#        return self.sum_debit
report_sxw.report_sxw('report.account.report.bs', 'account.report.bs', 'addons/l10n_ES_account_report/report/account_report_bs.rml', parser=account_report_bs, header=False)