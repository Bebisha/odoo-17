from odoo import models, fields, api


class KGProductTemplateInherit(models.Model):
    _inherit = "product.template"

    @api.model
    def default_get(self, fields):
        result = super(KGProductTemplateInherit, self).default_get(fields)
        if not self._context.get('default_detailed_type'):
            result['detailed_type'] = 'product'
        return result
    is_equipment = fields.Boolean(string="Equipment", help="Check this box if the item is considered equipment.")


    brand_id = fields.Many2one("product.brand", string="Brand")
    brand_code = fields.Char(string="New Brand Code", related='brand_id.code')
    brand_code_old = fields.Char(string="Old Brand Code", related='brand_id.old_code')

    category_code = fields.Char(string="Category Code", related='categ_id.code')

    sub_category_id = fields.Many2one("product.category", string="Sub category" ,domain="[('parent_id', '=', categ_id)]")
    sub_cate_id = fields.Many2one("sub.category", string="Sub Categor" )
    subcategory_code = fields.Char(string="Subcategory Code", related='sub_category_id.code',readonly=False)

    make = fields.Char(string="Make")
    serial_no = fields.Char(string="Serial number")
    physical_status_id = fields.Many2one('physical.status', string="Physical Status")
    accesories = fields.Text(string="Accessories")
    new_code = fields.Char(string="NEW ITEM CODE")
    existing_code = fields.Char(string="EXISTING ITEM CODE")
    full_description = fields.Text(string="Full Description")
    product_range = fields.Float(string="Range")
    range = fields.Char(string="Range")
    model = fields.Char(string="Model")
    type_of_sensors = fields.Many2one("type.sensors", string="Type of Sensor")
    type_of_sensor = fields.Char(string="Type of Sensor")
    communication_output = fields.Char(string="Communication Output")
    no_of_channels = fields.Integer(string="Number of Channels")
    life_period = fields.Date(string="Life Period")
    fitting_dimension = fields.Float(string="Fitting Dimension")
    body_type = fields.Many2one("type.body", string="Body Type")
    class_approval = fields.Char(string="Class Approval")
    dg_non_dg = fields.Selection([('dg', 'DG'), ('non_dg', 'NON DG')], string="DG / NON DG", default='dg')
    certification = fields.Char(string="Certifications")
    technical_description = fields.Text(string="Technical Description")
    operation_voltage = fields.Char(string="Voltage")
    dimensions = fields.Char(string="Dimensions")
    no_of_zones = fields.Integer(string="No of Zones")
    no_of_loops = fields.Integer(string="No of Loops")
    ip_rating = fields.Float(string="IP Rating")
    transport_regulation = fields.Char(string="Transport Regulation")
    rated_current = fields.Char(string="Rated Current")
    frequency = fields.Char(string="Rated Frequency" )
    rated_voltage = fields.Char(string="Rated Voltage" )
    network_type = fields.Many2one("type.network", string="Network Type")
    no_of_voltage = fields.Integer(string="No of Voltage")
    input_voltage = fields.Char(string="Input Voltage")
    output_voltage = fields.Char(string="Output Voltage")
    technical_specification = fields.Char(string="Technical Specification")
    connection_size = fields.Float(string="Connection Size")
    differential_range = fields.Float(string="Differential Range")
    medium = fields.Char(string="Medium")
    mounting_type = fields.Many2one("type.mounting", string="Mounting Type")
    length_of_type = fields.Float(string="Length of Type")
    colour = fields.Char(string="Colour")
    copper_thickness = fields.Char(string="Copper Thickness")
    no_of_cores = fields.Integer(string="No of Cores")
    main = fields.Char(string="Main")
    complementary = fields.Char(string="Complementary")
    auto_default_code = fields.Boolean(default=False, string="Auto-Internal Reference")
    part_no = fields.Char(string="Part No")
    product_group_id = fields.Many2one("product.group", string="Group")
    group_code = fields.Char(string="Group code",related='product_group_id.code')
    type_of_gas = fields.Char(string="Type of Gas")
    rated_power = fields.Char(string="Rated power")
    rated_wattage = fields.Char(string="Rated wattage")
    max_pressure = fields.Char(string="Maximum Pressure(BAR)")
    buyoncy = fields.Char(string="Buyoncy")
    number_of_poles = fields.Char(string="Number of Poles")
    capacity = fields.Char(string="Capacity")
    combustion_property = fields.Char(string="Combustion Property")

    length = fields.Float(string="Length")
    diameter = fields.Float(string="Diameter")

    room = fields.Integer(string="Room")
    rack = fields.Integer(string="Rack")
    bin = fields.Integer(string="Bin")
    minimum_stock = fields.Integer(string="Minimum Stock")
    stock_main_store = fields.Integer(string="Stock Main Store")
    stock_ajman = fields.Integer(string="Stock Ajman")
    stock_fujairah = fields.Integer(string="Stock Fujairah")
    stock_abudhabi = fields.Integer(string="Stock Abudhabi")


    is_gas_detection = fields.Boolean(default=False, string="Gas Detection", compute="compute_gas_detection")
    is_fire_detection = fields.Boolean(default=False, string="Fire Detection", compute="compute_fire_detection")
    is_electrical_system = fields.Boolean(default=False, string="Electrical System",
                                          compute="compute_electrical_system")
    is_measuring_control_instruments = fields.Boolean(default=False, string="Measuring Control & Instruments",
                                                      compute="compute_measuring_control_instruments")
    is_navigation_system = fields.Boolean(default=False, string="Navigation System",
                                          compute="compute_navigation_system")
    is_communication_system = fields.Boolean(default=False, string="Communication System",
                                             compute="compute_communication_system")
    is_featured_marine_products = fields.Boolean(default=False, string="Featured Marine Products",
                                                 compute="compute_featured_marine_products")
    is_life_saving_appliances = fields.Boolean(default=False, string="Life Saving Appliances",
                                               compute="compute_life_saving_appliances")
    is_fire_fighting_appliances = fields.Boolean(default=False, string="Fire Fighting Appliances",
                                                 compute="compute_fire_fighting_appliances")
    is_cables = fields.Boolean(default=False, string="Cables", compute="compute_cables")
    is_hardware = fields.Boolean(default=False, string="Hardware", compute="compute_hardware")
    is_tools_equipments = fields.Boolean(default=False, string="Tools & Equipments", compute="compute_tools_equipments")
    is_health_safety_env = fields.Boolean(default=False, string="Health, Safety & Environment",
                                          compute="compute_health_safety_env")
    is_consumables = fields.Boolean(default=False, string="Consumables", compute="compute_consumables")
    is_labour_product = fields.Boolean(string="Is Labour" ,default=False,copy=False)



    @api.depends('product_group_id')
    def compute_gas_detection(self):
        for rec in self:
            gas_detection_group = self.env.ref('kg_voyage_marine_inventory.group_gas_detection_system')
            rec.is_gas_detection = rec.product_group_id == gas_detection_group

    @api.depends('product_group_id')
    def compute_fire_detection(self):
        for rec in self:
            fire_detection_group = self.env.ref('kg_voyage_marine_inventory.group_fire_detection_system')
            rec.is_fire_detection = rec.product_group_id == fire_detection_group

    @api.depends('product_group_id')
    def compute_electrical_system(self):
        for rec in self:
            electrical_system_group = self.env.ref('kg_voyage_marine_inventory.group_electrical_system')
            rec.is_electrical_system = rec.product_group_id == electrical_system_group

    @api.depends('product_group_id')
    def compute_measuring_control_instruments(self):
        for rec in self:
            mci_group = self.env.ref('kg_voyage_marine_inventory.group_measuring_control_instruments')
            rec.is_measuring_control_instruments = rec.product_group_id == mci_group

    @api.depends('product_group_id')
    def compute_navigation_system(self):
        for rec in self:
            navigation_system_group = self.env.ref('kg_voyage_marine_inventory.group_navigation_system')
            rec.is_navigation_system = rec.product_group_id == navigation_system_group

    @api.depends('product_group_id')
    def compute_communication_system(self):
        for rec in self:
            communication_system_group = self.env.ref('kg_voyage_marine_inventory.group_communication_system')
            rec.is_communication_system = rec.product_group_id == communication_system_group

    @api.depends('product_group_id')
    def compute_featured_marine_products(self):
        for rec in self:
            featured_marine_group = self.env.ref('kg_voyage_marine_inventory.group_featured_marine_products')
            rec.is_featured_marine_products = rec.product_group_id == featured_marine_group

    @api.depends('product_group_id')
    def compute_life_saving_appliances(self):
        for rec in self:
            life_saving_appliances_group = self.env.ref('kg_voyage_marine_inventory.group_life_saving_appliances')
            rec.is_life_saving_appliances = rec.product_group_id == life_saving_appliances_group

    @api.depends('product_group_id')
    def compute_fire_fighting_appliances(self):
        for rec in self:
            fire_fighting_appliances_group = self.env.ref(
                'kg_voyage_marine_inventory.group_fire_fighting_appliances')
            rec.is_fire_fighting_appliances = rec.product_group_id == fire_fighting_appliances_group

    @api.depends('product_group_id')
    def compute_cables(self):
        for rec in self:
            cables_group = self.env.ref('kg_voyage_marine_inventory.group_cables')
            rec.is_cables = rec.product_group_id == cables_group

    @api.depends('product_group_id')
    def compute_hardware(self):
        for rec in self:
            hardware_group = self.env.ref('kg_voyage_marine_inventory.group_hardware')
            rec.is_hardware = rec.product_group_id == hardware_group

    @api.depends('product_group_id')
    def compute_tools_equipments(self):
        for rec in self:
            tools_equipment_group = self.env.ref('kg_voyage_marine_inventory.group_tools_and_equipments')
            rec.is_tools_equipments = rec.product_group_id == tools_equipment_group

    @api.depends('product_group_id')
    def compute_health_safety_env(self):
        for rec in self:
            health_safety_env_group = self.env.ref('kg_voyage_marine_inventory.group_health_safety_environment')
            rec.is_health_safety_env = rec.product_group_id == health_safety_env_group

    @api.depends('product_group_id')
    def compute_consumables(self):
        for rec in self:
            consumables_group = self.env.ref('kg_voyage_marine_inventory.group_consumables')
            rec.is_consumables = rec.product_group_id == consumables_group

    def kg_update_product_code(self):
        product_id = self.env['product.template'].search([])
        if product_id:
            for rec in product_id:
                if rec.auto_default_code:
                    if rec.categ_id and rec.sub_category_id and rec.brand_id and not rec.default_code:
                        if rec.category_code and rec.subcategory_code and rec.brand_code:
                            sequence_model = self.env['product.part.number.sequence']
                            sequence = sequence_model.search([
                                ('category_id', '=', rec.categ_id.id),
                                ('subcategory_id', '=', rec.sub_category_id.id),
                                ('brand_id', '=', rec.brand_id.id),
                                ('company_id', '=', rec.company_id.id)
                            ], limit=1)

                            if not sequence:
                                sequence = sequence_model.create({
                                    'category_id': rec.categ_id.id,
                                    'subcategory_id': rec.sub_category_id.id,
                                    'brand_id': rec.brand_id.id,
                                    'current_sequence': 1,
                                    'company_id': rec.company_id.id,
                                })
                            else:
                                sequence.current_sequence += 1

                            part_number = f"{rec.category_code}/{rec.subcategory_code}/{rec.brand_code}/{str(sequence.current_sequence).zfill(4)}"
                            rec.default_code = part_number
                            sequence.sudo().write({'current_sequence': sequence.current_sequence})