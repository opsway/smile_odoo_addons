# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import sys

from odoo import api

if sys.version_info > (3,):
    long = int


def audit_decorator(method):

    def get_new_values(self):
        new_values = []
        for record in self:
            vals = {}
            for fname in self._fields:
                vals[fname] = self._fields[fname].convert_to_read(
                    record[fname], record, use_name_get=False)
            new_values.append(vals)
        return new_values

    @api.model
    def audit_create(self, vals):
        result = audit_create.origin(self, vals)
        record = self.browse(result) if isinstance(result, (int, long)) \
            else result
        rule = self._get_audit_rule('create')
        if rule:
            # read needs sudo, related fields may be restricted for the editor
            new_values = record.sudo().read(load='_classic_write')
            rule.log('create', new_values=new_values)
        return result

    def audit_write(self, vals):
        rule = None
        if (self._name != self._context.get('audit_rec_model') or
                (self._name == self._context.get('audit_rec_model') and
                 self.ids != self._context.get('audit_rec_ids'))):
            rule = self._get_audit_rule('write')
        if rule:
            # read needs sudo, related fields may be restricted to the editor
            old_values = self.sudo().read(load='_classic_write')
        result = audit_write.origin(self, vals)
        if rule:
            if audit_write.origin.__name__ == '_write':
                new_values = get_new_values(self)
            else:
                # read needs sudo, related fields may be restricted to the editor
                new_values = self.sudo().read(load='_classic_write')
            rule.log('write', old_values, new_values)
        return result

    def audit_unlink(self):
        rule = self._get_audit_rule('unlink')
        if rule:
            # read needs sudo, related fields may be restricted to the editor
            old_values = self.sudo().read(load='_classic_write')
            rule.log('unlink', old_values)
        return audit_unlink.origin(self)

    if 'create' in method:
        return audit_create
    if 'write' in method:
        return audit_write
    if 'unlink' in method:
        return audit_unlink
