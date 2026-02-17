import json

from odoo import http
from odoo.http import content_disposition, request, route
from odoo.addons.report_xlsx.controllers.main import ReportController


class ReportController(ReportController):

    @http.route(
        [
            "/report/<converter>/<reportname>",
            "/report/<converter>/<reportname>/<docids>",
        ],
        type="http",
        auth="user",
        website=True,

    )
    def report_routes(self, reportname, docids=None, converter=None, **data):
        report = request.env["report"]._get_report_from_name(reportname)

        if converter == "xlsx" and not report:
            context = dict(request.env.context)
        if docids:
            docids = [int(i) for i in docids.split(",")]
        if data.get("options"):
            data.update(json.loads(data.pop("options")))

        if data.get("context"):
            data["context"] = json.loads(data["context"])
            context.update(data["context"])
        context["report_name"] = reportname

        xlsx = report.with_context(**context)._render_xlsx(docids, data=data)[0]
        report_file = context.get("report_file")
        if not report_file:
            active_model = context.get("active_model", "export")
            report_file = active_model.replace(".", "_")
            xlsxhttpheaders = [
                (
                    "Content-Type",
                    "application/vnd.openxmlformats-"


                    "officedocument.spreadsheetml.sheet",
                ),
                ("Content-Length", len(xlsx)),
                ("Content-Disposition", "attachment; filename=%s.xlsx" % report_file),
            ]
        return request.make_response(xlsx, headers=xlsxhttpheaders, content_type="application/vnd.ms-excel")
        return super().report_routes(reportname, docids, converter, **data)
