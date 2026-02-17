/** @odoo-module */

import { registry } from "@web/core/registry";
import { formView } from '@web/views/form/form_view';
import { KGFolderFormController } from "./folder_form_controller";

export const KGFolderFormView = {
    ...formView,
    Controller: KGFolderFormController,
};

registry.category("views").add("kg_folder_form", KGFolderFormView);
