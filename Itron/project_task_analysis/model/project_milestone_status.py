from odoo import models, fields, tools


class ProjectMilestoneStatus(models.Model):
    _name = 'project.milestone.status'
    _auto = False

    timeline_line_id = fields.Many2one('kg.project.timeline', string='Project Timeline')
    project_id = fields.Many2one('project.project', string='Project')
    milestone_id = fields.Many2one('project.milestone', string='Milestone')
    line_start_date = fields.Date(string='Start Date')
    line_end_date = fields.Date(string='End Date')

    def _query(self):
        query = """
            select
                row_number() over(ORDER BY min(t.id)) as id,
                min(t.id) as timeline_line_id,
                k.name as project_id,
                t.milestone_id as milestone_id, min(t.line_start_date) as line_start_date, max(t.line_end_date) as line_end_date
                
                from timeline_line t  
                left join kg_project_timeline k on k.id=t.project_id
                group by t.milestone_id, k.name
        """
        return query

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))
