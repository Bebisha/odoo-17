from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class DevelopingHistory(models.Model):
    _name = 'dev.history.form'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Developing History Form'
    _order = 'name desc'

    name = fields.Char(string="Name", required=True, copy=False, default='New', readonly=True)
    creation_date = fields.Date('Created Date')
    first_name = fields.Char('First Name')
    last_name = fields.Char('Last Name')
    dob = fields.Char('Date of Birth')
    age = fields.Float('Age')
    nationality = fields.Many2one('res.country', 'Nationality')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')], string="Gender")
    language = fields.Char('Language')
    child_language = fields.Char('Child Language')
    school = fields.Text('School Name')
    school_grade = fields.Char('School Grade')
    teacher = fields.Char('Teacher Name')

    mother_name = fields.Char('Mother Name')
    mother_phone = fields.Char('Mother Phone No')
    mother_nationality = fields.Many2one('res.country', 'Mother Nationality')
    mother_email = fields.Char('Mother Email')

    father_name = fields.Char('Father Name')
    father_phone_no = fields.Char('Father Phone No')
    father_nationality = fields.Many2one('res.country', 'Father Country')
    father_email = fields.Char('Father Email')
    address = fields.Text('Home Address')
    prev_address = fields.Char('Previous places your family has lived')
    siblings = fields.Integer('Siblings')
    grand_parents = fields.Integer('Grand Parents')
    others = fields.Integer('Others')

    main_concern = fields.Char(string='What is your main concern?')
    first_notice = fields.Char(string='When did you first notice difficulties?')
    space = fields.Char(string='           ')
    speech_language_therapist = fields.Boolean(string='Speech and language therapist')
    occupational_therapist = fields.Boolean(string='Occupational therapist')
    physiotherapist = fields.Boolean(string='Physiotherapist')
    educational_psychologist = fields.Boolean(string='Educational Psychologist')
    check_box_other = fields.Selection([('true', 'True'), ('false', 'False')], string='Other')
    any_other_1 = fields.Char(string='Other')
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
    child_communicate = fields.Char(
        string='How does your child communicate with you/siblings/peers? ( E.g. Words, phrases, sentences, signs, gestures?) ')
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
    is_submitted_dev = fields.Boolean(string='Submit', default=False)

    def approve_action_developmental(self):
        self.state = 'approve'
        return True

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('dev.history.sequence')
        result = super(DevelopingHistory, self).create(vals)
        return result
