# -*- encoding: utf-8 -*-
#
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import pycompat
import logging
_logger = logging.getLogger(__name__)
import babel
import copy
import datetime
import dateutil.relativedelta as relativedelta

import functools
from werkzeug import urls


def format_tz(env, dt, tz=False, format=False):
    record_user_timestamp = env.user.sudo().with_context(
        tz=tz or env.user.sudo().tz or 'UTC')
    timestamp = fields.Datetime.from_string(dt)

    ts = fields.Datetime.context_timestamp(record_user_timestamp, timestamp)

    # Babel allows to format datetime in a specific language without change locale
    # So month 1 = January in English, and janvier in French
    # Be aware that the default value for format is 'medium', instead of 'short'
    #     medium:  Jan 5, 2016, 10:20:31 PM |   5 janv. 2016 22:20:31
    #     short:   1/5/16, 10:20 PM         |   5/01/16 22:20
    if env.context.get('use_babel'):
        # Formatting available here :
        # http://babel.pocoo.org/en/latest/dates.html#date-fields
        from babel.dates import format_datetime
        return format_datetime(ts, format or 'medium', locale=env.context.get("lang") or 'en_US')

    if format:
        return pycompat.text_type(ts.strftime(format))
    else:
        lang = env.context.get("lang")
        langs = env['res.lang']
        if lang:
            langs = env['res.lang'].search([("code", "=", lang)])
        format_date = langs.date_format or '%B-%d-%Y'
        format_time = langs.time_format or '%I-%M %p'

        # Assuming ts is a valid datetime object
        fdate = str(ts.strftime(format_date))
        ftime = str(ts.strftime(format_time))

        return u"%s %s%s" % (fdate, ftime, (u' (%s)' % tz) if tz else u'')


def format_date(env, date, pattern=False):
    if not date:
        return ''
    try:
        return tools.format_date(env, date, date_format=pattern)
    except babel.core.UnknownLocaleError:
        return date


try:
    # We use a jinja2 sandboxed environment to render mako templates.
    # Note that the rendering does not cover all the mako syntax, in particular
    # arbitrary Python statements are not accepted, and not all expressions are
    # allowed: only "public" attributes (not starting with '_') of objects may
    # be accessed.
    # This is done on purpose: it prevents incidental or malicious execution of
    # Python code that may break the security of the server.
    from jinja2.sandbox import SandboxedEnvironment
    mako_template_env = SandboxedEnvironment(
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="${",
        variable_end_string="}",
        comment_start_string="<%doc>",
        comment_end_string="</%doc>",
        line_statement_prefix="%",
        line_comment_prefix="##",
        trim_blocks=True,  # do not output newline after blocks
        autoescape=True,  # XML/HTML automatic escaping
    )
    mako_template_env.globals.update({
        'str': str,
        'quote': urls.url_quote,
        'urlencode': urls.url_encode,
        'datetime': datetime,
        'len': len,
        'abs': abs,
        'min': min,
        'max': max,
        'sum': sum,
        'filter': filter,
        'reduce': functools.reduce,
        'map': map,
        'round': round,

        # dateutil.relativedelta is an old-style class and cannot be directly
        # instanciated wihtin a jinja2 expression, so a lambda "proxy" is
        # is needed, apparently.
        'relativedelta': lambda *a, **kw:
            relativedelta.relativedelta(*a, **kw),
    })
    mako_safe_template_env = copy.copy(mako_template_env)
    mako_safe_template_env.autoescape = False
except ImportError:
    _logger.warning("jinja2 not available, templating features will not work!")


class SMSTemplate(models.Model):
    _inherit = 'sms.template'
    _description = 'SMS Template'

    name = fields.Char(string='Name', copy=False, required=True)
    sms_servers_id = fields.Many2one('ir.sms_server', string='SMS Server')
    # model_id = fields.Many2one('ir.model', string='Applies to', required=True , ondelete='cascade')
    model = fields.Char(
        string='Related Document Model', store=True, readonly=True,
                        related='model_id.model')
    message = fields.Text(string='Message')
    from_number = fields.Char(string='From')
    to_number = fields.Char(string='To')

    @api.model
    def default_get(self, fields):
        context = dict(self._context)
        res = super(SMSTemplate, self).default_get(fields)
        sms_servers_id = self.env['ir.sms_server'].search(
            [], order='sequence', limit=1)
        if sms_servers_id:
            res.update({'sms_servers_id': sms_servers_id.id,
                        'from_number': sms_servers_id.from_no})

        return res

    @api.model
    def _render_template(self, template_txt, model, res_ids, post_process=False):
        """ Render the given template text, replace mako expressions ``${expr}``
        with the result of evaluating these expressions with an evaluation
        context containing:

         - ``user``: Model of the current user
         - ``object``: record of the document record this mail is related to
         - ``context``: the context passed to the mail composition wizard

        :param str template_txt: the template text to render
        :param str model: model name of the document record this mail is related to.
        :param int res_ids: list of ids of document records those mails are related to.
        """
        multi_mode = True
        if isinstance(res_ids, int):  # Change from pycompat.integer_types to int
            multi_mode = False
            res_ids = [res_ids]

        results = dict.fromkeys(res_ids, u"")

        # try to load the template
        try:
            mako_env = mako_safe_template_env if self.env.context.get('safe') else mako_template_env
            template = mako_env.from_string(tools.ustr(template_txt))
        except Exception:
            _logger.info(
                "Failed to load template %r",
                template_txt,
                exc_info=True)
            return multi_mode and results or results[res_ids[0]]

        # prepare template variables
        records = self.env[model].browse(it for it in res_ids if it)  # filter to avoid browsing [None]
        res_to_rec = dict.fromkeys(res_ids, None)
        for record in records:
            res_to_rec[record.id] = record
        variables = {
            'format_date': lambda date, format=False, context=self._context: format_date(
                self.env,
                date,
                format),
            'format_tz': lambda dt, tz=False, format=False, context=self._context: format_tz(
                self.env,
                dt,
                tz,
                format),
            'format_amount': lambda amount, currency, context=self._context: format_amount(self.env, amount, currency),
            'user': self.env.user,
            'ctx': self._context,  # context kw would clash with mako internals
        }
        for res_id, record in res_to_rec.items():
            variables['object'] = record
            try:
                render_result = template.render(variables)
            except Exception as e:
                _logger.info(
                    "Failed to render template %r using values %r with error: %s" %
                    (template, variables, str(e)), exc_info=True)
                raise UserError(
                    _("Failed to render template %r using values %r due to error: %s") %
                    (template, variables, str(e)))

            if render_result == u"False":
                render_result = u""
            results[res_id] = render_result

        if post_process:
            for res_id, result in results.items():
                results[res_id] = self.render_post_process(result)

        return multi_mode and results or results[res_ids[0]]
