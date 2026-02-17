/** @odoo-module **/

import { ListController } from '@web/views/list/list_controller';
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { preSuperSetupFolder } from "@documents/views/hooks";

export class KGFolderListController extends ListController {

    setup() {
        preSuperSetupFolder();
        super.setup();
        this.action = useService("action");
        this.orm = useService("orm");
        this.dialog = useService("dialog");
    }

    /**
     * @override
     */
    getStaticActionMenuItems() {
        const isM2MGrouped = this.model.root.isM2MGrouped;
        return {
            export: {
                isAvailable: () => this.isExportEnable,
                sequence: 10,
                description: _t("Export"),
                callback: () => this.onExportData(),
            },
            unarchive: {
                isAvailable: () =>
                    this.archiveEnabled &&
                    !isM2MGrouped &&
                    this.model.root.selection.some((record) => !record.data.active),
                sequence: 20,
                icon: "fa fa-history",
                description: _t("Restore"),
                callback: async () => {
                    await this.orm.call("documents.folder", "action_unarchive", [
                        this.model.root.selection.map((record) => record.resId),
                    ]);
                    await this.model.load();
                },
            },
            delete: {
                isAvailable: () =>
                    this.activeActions.delete &&
                    !isM2MGrouped &&
                    !this.model.root.selection.some((record) => !record.data.active),
                sequence: 20,
                description: _t("Delete"),
                callback: () => this.onDeleteSelectedRecords(),
            },
        };
    }

    /**
     * @override
     */
    async onDeleteSelectedRecords() {
        const displayDialog = await this.orm.call(
            this.props.resModel,
            "is_folder_containing_document",
            [this.model.root.selection.map((record) => record.resId)]
        );

        if (displayDialog) {
            this.dialog.add(ConfirmationDialog, {
                title: _t("Bye-bye, record!"),
                body: _t(
                    "Ready to make your record disappear into thin air? Are you sure?\n" +
                    "It will be gone forever!\n\n" +
                     "Files will be sent to trash and deleted forever after %s days.\n\n" +
                    "Think twice before you click that 'Delete/Move to trash' button!", this._deletionDelay
                ),
                confirmLabel: _t("Delete/Move to trash"),
                confirm: async () => {
                    await this.orm.call(this.props.resModel, "action_archive", [
                        this.model.root.selection.map((record) => record.resId),
                    ]);
                    await this.model.load();
                },
                cancel: () => {},
            });
        } else {
            await this.orm.call(this.props.resModel, "action_archive", [
                this.model.root.selection.map((record) => record.resId),
            ]);
            await this.model.load();
        }
    }

}
