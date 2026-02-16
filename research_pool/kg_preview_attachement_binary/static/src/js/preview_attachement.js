/** @odoo-module **/

import AbstractField from 'web.AbstractField';
import core from 'web.core';
import { field_registry } from 'web.field_registry';
import DocumentViewer from 'kg_preview_attachement_binary.legacy.DocumentViewer';

const { _t, _lt, qweb } = core;

class FieldMany2ManyAttachmentPreview extends AbstractField {
    static template = "FieldBinaryFileUploader";
    static template_files = "FieldAttachmentFileUploader.files";
    static supportedFieldTypes = ['many2many'];
    static fieldsToFetch = {
        name: {type: 'char'},
        mimetype: {type: 'char'},
    };

    constructor() {
        super(...arguments);

        if (this.field.type !== 'many2many' || this.field.relation !== 'ir.attachment') {
            const msg = _t("The type of the field '%s' must be a many2many field with a relation to 'ir.attachment' model.");
            throw _.str.sprintf(msg, this.field.string);
        }

        this.uploadedFiles = {};
        this.uploadingFiles = [];
        this.fileupload_id = _.uniqueId('oe_fileupload_temp');
        this.accepted_file_extensions = (this.nodeOptions && this.nodeOptions.accepted_file_extensions) || '*';
        $(window).on(this.fileupload_id, this._onFileLoaded.bind(this));

        this.metadata = {};
    }

    destroy() {
        super.destroy();
        $(window).off(this.fileupload_id);
    }

    // Private Methods

    _getFileUrl(attachment) {
        return `/web/content/${attachment.id}`;
    }

    _generatedMetadata() {
        _.each(this.value.data, record => {
            this.metadata[record.id] = {
                allowUnlink: this.uploadedFiles[record.data.id] || false,
                url: this._getFileUrl(record.data),
            };
        });
    }

    _render() {
        this._generatedMetadata();
        this.$('.oe_placeholder_files, .o_attachments')
            .replaceWith($(qweb.render(this.template_files, { widget: this })));
        this.$('.oe_fileupload').show();

        this.$('.o_image[data-mimetype^="image"]').each(function () {
            const $img = $(this);
            if (/gif|jpe|jpg|png/.test($img.data('mimetype')) && $img.data('src')) {
                $img.css('background-image', `url('${$img.data('src')}')`);
            }
        });
    }

    // Handlers

    _onAttach() {
        this.$('.o_input_file').click();
    }

    _onDelete(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        const fileID = $(ev.currentTarget).data('id');
        const record = _.findWhere(this.value.data, { res_id: fileID });
        if (record) {
            this._setValue({
                operation: 'FORGET',
                ids: [record.id],
            });
            const metadata = this.metadata[record.id];
            if (!metadata || metadata.allowUnlink) {
                this._rpc({
                    model: 'ir.attachment',
                    method: 'unlink',
                    args: [record.res_id],
                });
            }
        }
    }

    _onFileChanged(ev) {
        ev.stopPropagation();

        const files = ev.target.files;
        let attachment_ids = this.value.res_ids;

        if (files.length === 0) return;

        _.each(files, file => {
            const record = _.find(this.value.data, attachment => attachment.data.name === file.name);
            if (record) {
                const metadata = this.metadata[record.id];
                if (!metadata || metadata.allowUnlink) {
                    attachment_ids = _.without(attachment_ids, record.res_id);
                    this._rpc({
                        model: 'ir.attachment',
                        method: 'unlink',
                        args: [record.res_id],
                    });
                }
            }
            this.uploadingFiles.push(file);
        });

        this._setValue({
            operation: 'REPLACE_WITH',
            ids: attachment_ids,
        });

        this.$('form.o_form_binary_form').submit();
        this.$('.oe_fileupload').hide();
        ev.target.value = "";
    }

    _onFileLoaded() {
        const files = Array.prototype.slice.call(arguments, 1);
        this.uploadingFiles = [];

        let attachment_ids = this.value.res_ids;
        _.each(files, file => {
            if (file.error) {
                this.displayNotification({ title: _t('Uploading Error'), message: file.error, type: 'danger' });
            } else {
                attachment_ids.push(file.id);
                this.uploadedFiles[file.id] = true;
            }
        });

        this._setValue({
            operation: 'REPLACE_WITH',
            ids: attachment_ids,
        });
    }

    _previewAttachment(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const activeAttachmentID = $(ev.currentTarget).data('id');
        this._rpc({
            model: 'ir.attachment',
            method: 'read_as_sudo',
            kwargs: {
                domain: [['id', 'in', this.value.res_ids]],
                fields: ['id', 'mimetype', 'index_content'],
            },
        }).then(result => {
            this.attachments = result.map(r => ({
                id: r.id,
                mimetype: r.mimetype,
                fileType: r.index_content
            }));
            const attachmentViewer = new DocumentViewer(this, this.attachments, activeAttachmentID);
            attachmentViewer.appendTo($('body'));
        });
    }
}

field_registry.add("many2many_attachment_preview", FieldMany2ManyAttachmentPreview);

export default FieldMany2ManyAttachmentPreview;
