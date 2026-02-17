/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from '@web/views/list/list_view';
import { KGFolderListController } from './folder_list_controller';

export const KGFolderListView = {
    ...listView,
    Controller: KGFolderListController,
};

registry.category("views").add("kg_folder_list", KGFolderListView);
