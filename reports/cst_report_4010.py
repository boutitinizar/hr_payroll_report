# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
import locale, re, datetime

class FichePayeParser(models.AbstractModel):
    _name = 'report.hr_payroll_report.report_cst_4010_monthly'
    locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

    def is_int(self, x):
        try:
            if x == int(x):
                return True
            else:
                return False
        except ValueError:
            return False

    def get_month_year(self, d):
        d1 = datetime.datetime.strptime(d, '%Y-%m-%d')
        return d1.strftime('%B %Y')

    def get_month(self, d):
        d1 = datetime.datetime.strptime(d, '%Y-%m-%d')
        return d1.strftime('%B')

    def get_year(self, d):
        d1 = datetime.datetime.strptime(d, '%Y-%m-%d')
        return d1.strftime('%Y')


    def get_payslip_lines(self, objs):
        res = []
        ids = []
        for item in objs:
            if item.appears_on_payslip is True and not item.salary_rule_id.parent_rule_id:
                ids.append(item.id)
        if ids:
            res = self.env['hr.payslip.line'].browse(ids)
        return res

    def get_rule_category_name(self, code):
        category = self.env['hr.salary.rule.category'].search([('code', '=', code)], limit=1)
	return category.name

    def get_salary_rules(self, filter):
	rules = self.env['hr.salary.rule'].search([('appears_on_payslip', '=', True), ('parent_rule_id', '=', None), ('code', 'like', filter)], order='sequence, id')
        return rules

    def split_docs_by_month(self, docs):
        res = []
        temp = {}
        for o in docs:
            d = datetime.datetime.strptime(o.date_from, '%Y-%m-%d')
            m = d.strftime('%m')
            y = d.strftime('%Y')
            t = (m, y)
            if t in temp:
                temp[t].append(o)
            else:
                temp[t] = [o]
        for k in sorted(temp):
            res.append(temp[k])
        return res

    def split_docs_by_number(self, docs, num=5):
         res = []
         temp = []
         i = 0
         c = 0
         for o in docs:
             if i == num:
                 res.append(temp)
                 temp = [o]
                 i = 1
             else:
                 temp.append(o)
                 i += 1
             if c == len(docs)-1:
                 res.append(temp)
             c += 1
         return res

    def get_amount_by_salary_rule_and_employee(self, obj, rule):
        total = 0
        line = self.env['hr.payslip.line'].search([('slip_id', '=', obj.id), ('salary_rule_id', '=', rule.id)], limit=1)
        if line:
            total = line.amount
            return total
        else:
            return 0

    def get_total_by_salary_rule_and_employee(self, obj, rule):
        total = 0
	line = self.env['hr.payslip.line'].search([('slip_id', '=', obj.id), ('salary_rule_id', '=', rule.id)], limit=1)
	if line:
            total = line.total
            if re.match('DED', line.salary_rule_id.category_id.code) and line.total > 0:
                total = -total
            return total
        else:
            return 0

    def get_amount_of_salary_rule(self, objs, rule):
        rule_total = 0
        num = 0
        for o in objs:
            line = self.env['hr.payslip.line'].search([('slip_id', '=', o.id), ('salary_rule_id', '=', rule.id)])
            if line:
                rule_total += line.amount
		num += 1
        return [num, rule_total]

    def get_total_of_salary_rule(self, objs, rule):
        rule_total = 0
        for o in objs:
            line = self.env['hr.payslip.line'].search([('slip_id', '=', o.id), ('salary_rule_id', '=', rule.id)])
            if line:
                rule_total += line.total
        if re.match("DED", rule.category_id.code) and rule_total > 0:
            rule_total = -rule_total
        return rule_total 

    def get_total_by_rule_category_filtered(self, obj, code, filter_sup, filter_inf):
        category_total = 0
        category_id = self.env['hr.salary.rule.category'].search([('code', '=', code)], limit=1).id
        if category_id:
            line_ids = self.env['hr.payslip.line'].search([('slip_id', '=', obj.id), ('category_id', 'child_of', category_id)])
            for line in line_ids:
                if line.total > filter_sup and line.total < filter_inf:
		    category_total += line.total
        return category_total

    def get_total_of_rule_category_filtered(self, objs, code, filter_sup, filter_inf):
        category_total = 0
        num = 0
	for o in objs:
            if self.get_total_by_rule_category(o, code) > filter_sup and self.get_total_by_rule_category(o, code) < filter_inf:
                category_total += self.get_total_by_rule_category(o, code)
                num += 1
        return [num, category_total]

    def get_total_by_rule_category(self, obj, code):
        category_total = 0
        category_id = self.env['hr.salary.rule.category'].search([('code', '=', code)], limit=1).id
        if category_id:
            line_ids = self.env['hr.payslip.line'].search([('slip_id', '=', obj.id), ('category_id', 'child_of', category_id)])
            for line in line_ids:
                category_total += line.total
        return category_total

    def get_total_of_rule_category(self, objs, code):
        category_total = 0
        for o in objs:
            category_total += self.get_total_by_rule_category(o, code)
        return category_total

    def get_total_cst_trimester(self, objs, code):
        category_total = 0
        for o in objs:
            category_total += self.get_total_of_rule_category(o, code)
        return category_total

    def get_employer_line(self, obj, parent_line):
        return self.env['hr.payslip.line'].search([('slip_id', '=', obj.id), ('salary_rule_id.parent_rule_id.id', '=', parent_line.salary_rule_id.id)], limit=1)

    def get_conge_acquis(self, obj):
        try:
            if obj.conge_acquis:
                return obj.conge_acquis
            else:
                return obj.employee_id.contract_id.conge_mensuel
        except:
            pass
        return obj.employee_id.contract_id.conge_mensuel


    def get_total_conge_acquis(self, objs):
        total = 0
        for o in objs:
            total += self.get_conge_acquis(o)
        return total

    def get_worked_days_from_payslip(self, obj, code):
        i = self.env['hr.payslip.worked_days'].search([('payslip_id', '=', obj.id), ('code', '=', code)], limit=1)
        if i:
            return i.number_of_days
        else:
            return 0

    def get_total_worked_days_from_payslip(self, objs, code):
        total = 0
        for o in objs:
            total += self.get_worked_days_from_payslip(o, code)
        return total

    @api.model
    def render_html(self, docids, data=None):
        payslip = self.env['hr.payslip'].browse(docids)
        docargs = {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'data': data,
            'docs': payslip,
            'lang': "fr_FR",
            'get_payslip_lines': self.get_payslip_lines,
            'get_total_by_rule_category': self.get_total_by_rule_category,
            'get_total_by_rule_category_filtered': self.get_total_by_rule_category_filtered,
            'get_employer_line': self.get_employer_line,
            'get_salary_rules': self.get_salary_rules,
            'get_total_by_salary_rule_and_employee': self.get_total_by_salary_rule_and_employee,
            'split_docs_by_month': self.split_docs_by_month,
            'split_docs_by_number': self.split_docs_by_number,
            'get_total_of_salary_rule': self.get_total_of_salary_rule,
            'get_amount_of_salary_rule': self.get_amount_of_salary_rule,
            'get_month_year': self.get_month_year,
            'get_month': self.get_month,
            'get_year': self.get_year,
            'get_rule_category_name': self.get_rule_category_name,
            'get_total_of_rule_category': self.get_total_of_rule_category,
            'get_total_cst_trimester': self.get_total_cst_trimester,
            'get_total_of_rule_category_filtered': self.get_total_of_rule_category_filtered,
            'get_conge_acquis': self.get_conge_acquis,
            'get_total_conge_acquis': self.get_total_conge_acquis,
            'get_worked_days_from_payslip': self.get_worked_days_from_payslip,
            'get_total_worked_days_from_payslip': self.get_total_worked_days_from_payslip,
        }
        return self.env['report'].render('hr_payroll_report.report_cst_4010_monthly', docargs)
