from odoo import models, fields, api
import random
import string

class developmental_history_form(models.Model):
    _name = 'developmental.history.form'
    _description = 'Developmental History Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    today_date = fields.Date(string='Today Date')
    first_name = fields.Char(string='First Name')
    name = fields.Char(string='Name')
    last_name = fields.Char(string='Last Name')
    child_name = fields.Char(string='Full Name')
    date_of_birth = fields.Date(string='Date of Birth')
    age = fields.Float(string='Age')
    nationality = fields.Many2one('res.country', string='Nationality')
    nationality_1 = fields.Many2one('res.country', string='Nationality')
    nationality_2 = fields.Many2one('res.country', string='Nationality')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')])
    language_spoken = fields.Char(string='Language spoken at home')
    dominant_language = fields.Char(string='What is your childs dominant language?')
    current_school = fields.Char(string='Current School')
    school_year_grade = fields.Char(string='School year/grade')
    classroom_teacher = fields.Char(string='Classroom Teacher')

    mother_name = fields.Char(string='Mother Name')
    phone_number_1 = fields.Char(string='Phone Number')
    phone_number_2 = fields.Char(string='Phone Number')
    father_name = fields.Char(string='Father Name')
    mother_mail = fields.Char(string='Mother Email')
    father_mail = fields.Char(string='Father Email')
    home_address = fields.Char(string='Home Address')
    previous_place = fields.Char(string='Previous places your family has lived? (If applicable)')
    siblings = fields.Char(string='Siblings')
    grandparents = fields.Char(string='Grandparents')
    others = fields.Char(string='Others')

    main_concern = fields.Char(string='What is your main concern?')
    first_notice = fields.Char(string='When did you first notice difficulties?')
    space = fields.Char(string='           ')
    speech_language_therapist = fields.Boolean(string='Speech and language therapist')
    occupational_therapist = fields.Boolean(string='Occupational therapist')
    physiotherapist = fields.Boolean(string='Physiotherapist')
    educational_psychologist = fields.Boolean(string='Educational Psychologist')
    check_box_other = fields.Selection([('true', 'True'), ('false', 'False')],string='Other')
    any_other_1=fields.Char(string='Other')
    other_medical = fields.Char(
        string='Has your child had any other medical assessments, hospitalizations or surgeries?')
    parents_related_relative = fields.Selection([('yes', 'Yes'), ('no', 'No')])
    upload_report = fields.Binary(string='If yes, kindly upload the report:', tracking=True)
    child_general_health = fields.Text(string='Describe your childs general health')
    physical_difficulties = fields.Char(string='Does your child have any physical difficulties?')
    ear_infections = fields.Char(string='Does your child have a history of ear infections?')
    screened_tested = fields.Char(string='Has your child’s vision recently been screened or tested? When? Results?')
    wear_glasses = fields.Char(string='Does your child wear glasses?')
    past_present_medications = fields.Text(string='Please list any past or present medications your child has taken')
    allergies = fields.Text(string='Does your child have any allergies (food or non-food related)? Please list.')

    full_term_delivery = fields.Boolean(string='Full term delivery')
    full_term_cesarean = fields.Boolean(string='Full term cesarean section')
    pre_term = fields.Char(string='Pre-Term(how many weeks?)')
    during_pregnancy = fields.Char(string='Were there any difficulties during pregnancy or birth?')
    problems = fields.Char(string='Were there any problems with feeding or drinking?')
    crawling = fields.Char(string='Crawling')
    sitting = fields.Char(string='Sitting')
    walking = fields.Char(string='Walking')
    babbling = fields.Char(string='Babbling')
    first_words = fields.Char(string='First words')
    short_sentences = fields.Char(string='Short sentences (two words together)')
    child_like = fields.Char(string='What was your child like as a baby?')

    child_understanding = fields.Char(
        string='Do you think your child’s understanding and use of language is different from his/her peers?')
    child_understanding_instruction_school = fields.Char(
        string='Does your child understand and follow instructions at home and at school?')
    child_interact = fields.Char(string='How does your child interact with other children and adults?')
    child_easy_understand = fields.Char(
        string='Do you find it easy to understand your child? Does your child have difficulty making certain sounds?')
    speaking_fluently = fields.Char(
        string='Does your child ever appear to have difficulty “getting their words out” or speaking fluently?')
    family_speech = fields.Char(string='Is there a history in your family of speech and language difficulties?')

    carrying_fine_motor = fields.Char(
        string='Compared to other children your child’s age, does your child have difficulty with carrying out fine motor tasks e.g. cutting, drawing?')
    child_dressing = fields.Char(string='Does your child have difficulty with getting dressed, using cutlery etc.? ')
    bump = fields.Char(string='Does he/she bump into objects and other people?')
    figuring_activities = fields.Char(
        string='Does your child appear to have difficulty with figuring out activities and how to do them, e.g. planning activities?')

    school_experience = fields.Char(string='Does or did your child ever experience any difficulties at school?')
    enjoy_school = fields.Char(
        string='Does your child enjoy school? What subjects/activities does he or she enjoy most?')
    dislike_activities = fields.Char(string='Are there subjects or activities your child dislikes? ')
    hearing_test = fields.Char(string='Has your child had a hearing test? When? ')
    child_communicate = fields.Char(string='How does your child communicate with you/siblings/peers? ( E.g. Words, phrases, sentences, signs, gestures?) ')
    perspective = fields.Char(
        string='From your perspective how does your child get along with teachers, adults and other children at school? ')
    raised_concerns = fields.Char(string='Has school raised any concerns about your child? ')
    help = fields.Char(string='What help, if any has your child received at school? ')
    help_support_feel = fields.Char(string='Do you feel that your child needs any extra help or support? ')
    different_behaviour = fields.Char(string='Does your child’s behaviour differ between home and school?')

    speech_language_delay = fields.Boolean(string='Speech and Language Delay')
    motor_delay = fields.Boolean(string='Motor delay')
    sensory_processing_disorder = fields.Boolean(string='Sensory processing disorder')
    add = fields.Boolean(string='ADD (Attention Deficit Disorder)')
    global_development = fields.Boolean(string='Global development delay')
    asd = fields.Boolean(string='ASD (Autistic Spectrum Disorder)')
    drs_stutter_stammer = fields.Boolean(string='Dysfluency - stutter or stammer')
    other_checkbox = fields.Selection([('true', 'True'), ('false', 'False')], string='Other')
    any_other_2 = fields.Char(string='Other')
    # other_checkbox=fields.Char(string='')
    assessment_consultation = fields.Text(string='What do you hope will be achieved by this assessment/consultation?')
    other_like_information = fields.Char(
        string='Is there any other information you would like us to know about your child?')

    signature = fields.Binary(string='Signature')

    # company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    company_id = fields.Many2one('res.company')

    state = fields.Selection([('draft', 'Draft'), ('approve', 'Approved')], default='draft')

    partner_id_dev = fields.Many2one('res.partner', string='Partner')

    ref_dev = fields.Char(string='Reference')
    is_submitted_dev = fields.Boolean(string='Submit',default=False)

    _sql_constraints = [
        ('ref_unique_dev', 'unique(ref_dev)', 'This reference is already used!')
    ]

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('developmental.history.form')
        result = super(developmental_history_form, self).create(vals)
        a = str(result.first_name) + ' ' + str(result.last_name)
        result.child_name = a
        x = ''.join(random.choices(string.ascii_lowercase, k=10))
        result.ref_dev = x
        mail_template = self.env.ref('kg_developing_child_centre.developmental_history_mail_template')
        mail_template.send_mail(result.id, force_send=True)
        return result

    def approve_action_developmental(self):
        self.state = 'approve'
        partner = self.env['res.partner'].create({
            'name': self.child_name,
            'dev_history_id': self.id,
            'dob': self.date_of_birth,
            'gender': self.gender,
            'country_id': self.nationality.id,
            'language_spoken_dev': self.language_spoken,
            'school_year_grade_dev': self.school_year_grade,
            'today_date_dev': self.today_date,
            'dominant_language_dev': self.dominant_language,
            'age_dev': self.age,
            'current_school_dev': self.current_school,
            'classroom_teacher_dev': self.classroom_teacher,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone_number_1,
            'mobile': self.phone_number_2,
            'mother_name': self.mother_name,
        })
        self.partner_id_dev = partner.id


class partner_developmental(models.Model):
    _inherit = 'res.partner'

    today_date_dev = fields.Date(string='Today Date')
    age_dev = fields.Float(string='Age')
    child_name_dev = fields.Char(string='Full Name')
    dominant_language_dev = fields.Char(string='What is your childs dominant language?')
    current_school_dev = fields.Char(string='Current School')
    classroom_teacher_dev = fields.Char(string='Classroom Teacher')
    school_year_grade_dev = fields.Char(string='School year/grade')
    language_spoken_dev = fields.Char(string='Language spoken at home')
    dev_history_id = fields.Many2one('developmental.history.form', string='DH ID')


    def open_developmental_history_form(self):
        ctx = {
            'default_name': self.dev_history_id.name,
            'default_child_name': self.dev_history_id.child_name,
            'default_first_name': self.dev_history_id.first_name,
            'default_last_name': self.dev_history_id.last_name,
            'default_today_date': self.today_date_dev,
            'default_age': self.age_dev,
            'default_dominant_language': self.dominant_language_dev,
            'default_nationality': self.country_id.id,
            'default_current_school': self.current_school_dev,
            'default_classroom_teacher': self.classroom_teacher_dev,
            'default_school_year_grade': self.school_year_grade_dev,
            'default_date_of_birth': self.dob,
            'default_gender': self.gender,
            'default_language_spoken': self.language_spoken_dev,
            'default_state':'approve'
        }
        return {
            'name': 'DH Form Details',
            'domain': [('partner_id_dev', 'in', [self.id])],
            'context': ctx,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'developmental.history.form',
            'type': 'ir.actions.act_window'
        }
