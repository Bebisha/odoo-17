from odoo import http
from odoo.http import request


class LeadFormController(http.Controller):

    @http.route('/submit/lead', type='http', auth='public', website=True, methods=['POST'], csrf=False)
    def handle_lead_form(self, **post):
        source_menu = post.get('source_menu', 'Website')  # Default to 'Website' if not provided

        medium = request.env['utm.medium'].sudo().search([('name', '=', 'Website')], limit=1)
        if not medium:
            medium = request.env['utm.medium'].sudo().create({'name': 'Website'})

        lead_source = request.env['utm.source'].sudo().search([('name', '=', 'Website')], limit=1)
        if not lead_source:
            lead_source = request.env['utm.source'].sudo().create({'name': 'Website'})

        # Get or create dynamic source based on menu
        source = request.env['lead.interest'].sudo().search([('name', '=', source_menu)], limit=1)
        if not source:
            source = request.env['lead.interest'].sudo().create({'name': source_menu})

        print("post.get('country_name')", post.get('country_name'))

        country_name = post.get('country_name')

        country = request.env['res.country'].sudo().search([('name', '=', country_name)], limit=1)

        if post.get('country_code') == '968':
            lead = request.env['crm.lead'].sudo().create({
                'name': post.get('name'),
                'contact_name': post.get('contact_name'),
                'email_from': post.get('email'),
                'phone': str("+") + str(post.get('country_code')) +str(" ") + str(post.get('phone')) ,
                'description': post.get('message'),
                'country': country.code,
                'medium_id': medium.id,
                'source_id': lead_source.id,
                'lead_interest_id': source.id,
                'type': 'lead',
                'team_id':24,
                'user_id':False,
                'company_id':1

            })
        else:
            lead = request.env['crm.lead'].sudo().create({
                'name': post.get('name'),
                'contact_name': post.get('contact_name'),
                'email_from': post.get('email'),
                'phone': str("+") + str(post.get('country_code')) + str(" ") + str(post.get('phone')),
                'description': post.get('message'),
                'country': country.code,
                'medium_id': medium.id,
                'source_id': lead_source.id,
                'lead_interest_id': source.id,
                'type': 'lead',
                'team_id': 23,
                'user_id': False,
                'company_id': 2

            })

        sales_team = request.env['crm.team'].sudo().search([], limit=1)
        if sales_team and sales_team.alias_id:
            if sales_team.alias_id.alias_full_name:
                lead_url = f"/web#id={lead.id}&model=crm.lead&view_type=form"

                mail_values = {
                    'subject': f'New Contact Us Lead: {lead.name}',
                    'body_html': f'''
                                    <p>Dear Team,</p>

                            <p>You have received a new lead submitted through the website.<br/>
                             Please find the details below:</p>
                    
                            <p>
                                <a href="{lead_url}" target="_blank" style="
                                    display: inline-block;
                                    background-color: #1f8ceb;
                                    color: #ffffff;
                                    padding: 10px 20px;
                                    text-decoration: none;
                                    border-radius: 4px;
                                    font-weight: bold;
                                    font-family: Arial, sans-serif;">
                                    View Lead 
                                </a>
                            </p>
                    
                            <p>If you have any questions or require further assistance, feel free to reach out.</p>
                    
                            <p>Best regards,<br/>
                            Sales Team</p>
                                ''',
                    'email_to': sales_team.alias_id.alias_full_name,
                }
                request.env['mail.mail'].sudo().create(mail_values).send()
        return request.render('kg_itron_website.lead_submission_success', {
            'lead': lead,
            'source_menu': source_menu,
        })

    @http.route(['/custom/contactus/submit'], type='http', auth="public", website=True, csrf=False)
    def custom_contactus_submit(self, **post):
        # Get Website medium
        medium = request.env['utm.medium'].sudo().search([('name', '=', 'Website')], limit=1)
        if not medium:
            medium = request.env['utm.medium'].sudo().create({'name': 'Website'})

        lead_source = request.env['utm.source'].sudo().search([('name', '=', 'Website')], limit=1)
        if not lead_source:
            lead_source = request.env['utm.source'].sudo().create({'name': 'Website'})

        # Get or create Contact source
        source = request.env['lead.interest'].sudo().search([('name', '=', 'Contact Us')], limit=1)
        if not source:
            source = request.env['lead.interest'].sudo().create({'name': 'Contact Us'})
        print("post.get('country_name')=======", post.get('country_name'))
        country_name = post.get('country_name')

        country = request.env['res.country'].sudo().search([('name', '=', country_name)], limit=1)

        # Create a lead
        contact_us = False
        if post.get('email_from'):
            if post.get('country_code') == '968':
                contact_us = request.env['crm.lead'].sudo().create({
                    'name': post.get('inquiry_type') or 'Website Inquiry',
                    'contact_name': f"{post.get('first_name', '')} {post.get('last_name', '')}",
                    'email_from': post.get('email_from'),
                    'phone': str("+") + str(post.get('country_code')) +str(" ") + str(post.get('phone')) ,
                    'partner_name': post.get('organization'),
                    'description': post.get('message'),
                    'country': country.code,
                    'medium_id': medium.id,
                    'source_id': lead_source.id,
                    'lead_interest_id': source.id,
                    'type': 'lead',
                    'team_id':24,
                    'user_id':False,
                    'company_id':1

                })
            else:
                contact_us = request.env['crm.lead'].sudo().create({
                    'name': post.get('inquiry_type') or 'Website Inquiry',
                    'contact_name': f"{post.get('first_name', '')} {post.get('last_name', '')}",
                    'email_from': post.get('email_from'),
                    'phone': str("+") + str(post.get('country_code')) + str(" ") + str(post.get('phone')),
                    'partner_name': post.get('organization'),
                    'description': post.get('message'),
                    'country': country.code,
                    'medium_id': medium.id,
                    'source_id': lead_source.id,
                    'lead_interest_id': source.id,
                    'type': 'lead',
                    'team_id': 23,
                    'user_id': False,
                    'company_id': 2

                })

            sales_team = request.env['crm.team'].sudo().search([], limit=1)
            if sales_team and sales_team.alias_id:
                if sales_team.alias_id.alias_full_name:
                    lead_url = f"/web#id={contact_us.id}&model=crm.lead&view_type=form"

                    mail_values = {
                        'subject': f'New Contact Us Lead: {contact_us.name}',
                        'body_html': f'''
                               <p>Dear Team,</p>
    
                                <p>You have received a new lead submitted through the website.<br/>
                                 Please find the details below:</p>
                        
                                <p>
                                    <a href="{lead_url}" target="_blank" style="
                                        display: inline-block;
                                        background-color: #1f8ceb;
                                        color: #ffffff;
                                        padding: 10px 20px;
                                        text-decoration: none;
                                        border-radius: 4px;
                                        font-weight: bold;
                                        font-family: Arial, sans-serif;">
                                        View Lead 
                                    </a>
                                </p>
                        
                                <p>If you have any questions or require further assistance, feel free to reach out.</p>
                        
                                <p>Best regards,<br/>
                                Sales Team</p>
                            ''',
                        'email_to': sales_team.alias_id.alias_full_name,
                    }
                    request.env['mail.mail'].sudo().create(mail_values).send()

        # Redirect to thank you page
        return request.render('kg_itron_website.lead_submission_success', {
            'contact_us': contact_us,
        })
