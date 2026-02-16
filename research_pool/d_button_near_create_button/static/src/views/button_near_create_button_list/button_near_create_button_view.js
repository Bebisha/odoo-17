/** @odoo-module */

import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";
import { ButtonNearCreateButtonController as Controller } from './button_near_create_button_controller';

export const ButtonNearCreateButtonView = {
    ...listView,
    Controller,
    buttonTemplate: 'd_button_near_create_button.ButtonNearCreateButtonView.Buttons',
};

registry.category("views").add("button_near_create_button", ButtonNearCreateButtonView);
