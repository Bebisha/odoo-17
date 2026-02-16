/** @odoo-module **/
import { ImageField } from '@web/views/fields/image/image_field';
import { useFileViewer } from "@web/core/file_viewer/file_viewer_hook";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { isBinarySize } from "@web/core/utils/binary";

export class ImagePreviewField extends ImageField {
    static template = "image_preview_zoom.ImagePreviewField";

    setup() {
        super.setup();
        this.fileViewer = useFileViewer();
        // Bind this context to the new icon click handler
        this.onClickIcon = this.onClickIcon.bind(this);
        console.log( this.onClickIcon)
    }

    onClickImage() {
        if (!this.props.record.data[this.props.name]){
            return;
        }
        const attachment = { defaultSource: this.lastURL, isViewable: true, isImage: true, displayName: '' };
        console.log( attachment,"lllllllllllllllll")
        if (isBinarySize(this.props.record.data[this.props.name])) {
            attachment['downloadUrl'] = this.lastURL;
        }
        const attachments = [attachment];
        this.fileViewer.open(attachment, attachments);
    }

    onClickIcon() {
        this.onClickImage();  // Use the existing image preview logic
    }
}

export const imagePreviewField = {
    component: ImagePreviewField,
    displayName: _t("Image"),
    supportedOptions: [
        // Options as before
    ],
    supportedTypes: ["binary"],
    fieldDependencies: [{ name: "write_date", type: "datetime" }],
    isEmpty: () => false,
    extractProps: ({ attrs, options }) => ({
        enableZoom: options.zoom,
        zoomDelay: options.zoom_delay,
        previewImage: options.preview_image,
        acceptedFileExtensions: options.accepted_file_extensions,
        width: options.size && Boolean(options.size[0]) ? options.size[0] : attrs.width,
        height: options.size && Boolean(options.size[1]) ? options.size[1] : attrs.height,
        reload: "reload" in options ? Boolean(options.reload) : true,
    }),
};

registry.category("fields").add("image_preview", imagePreviewField);
