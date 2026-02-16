/** @odoo-module **/
import { core, Widget } from 'web.core';
import { hidePDFJSButtons } from '@web/legacy/js/libs/pdfjs';
import QWeb from 'web.QWeb';

const SCROLL_ZOOM_STEP = 0.1;
const ZOOM_STEP = 0.5;

class DocumentViewer extends Widget {
    constructor(parent, attachments, activeAttachmentID) {
        super(parent);
        this.attachment = attachments.filter(attachment => {
            const match = attachment.type === 'url' 
                ? attachment.url.match("(youtu|.png|.jpg|.gif)") 
                : attachment.mimetype.match("(image|video|application/pdf|text)");

            if (match) {
                attachment.fileType = match[1];
                if (match[1].match("(.png|.jpg|.gif)")) {
                    attachment.fileType = 'image';
                }
                if (match[1] === 'youtu') {
                    const youtubeArray = attachment.url.split('/');
                    let youtubeToken = youtubeArray[youtubeArray.length - 1];
                    if (youtubeToken.indexOf('watch') !== -1) {
                        youtubeToken = youtubeToken.split('v=')[1];
                        const amp = youtubeToken.indexOf('&');
                        if (amp !== -1) {
                            youtubeToken = youtubeToken.substring(0, amp);
                        }
                    }
                    attachment.youtube = youtubeToken;
                }
                return true;
            }
            return false;
        });

        this.activeAttachment = attachments.find(att => att.id === activeAttachmentID);
        this.modelName = 'ir.attachment';
        this._reset();
    }

    template = "arv_DocumentViewer";

    events = {
        'click .o_download_btn': '_onDownload',
        'click .o_viewer_img': '_onImageClicked',
        'click .o_viewer_video': '_onVideoClicked',
        'click .move_next': '_onNext',
        'click .move_previous': '_onPrevious',
        'click .o_rotate': '_onRotate',
        'click .o_zoom_in': '_onZoomIn',
        'click .o_zoom_out': '_onZoomOut',
        'click .o_zoom_reset': '_onZoomReset',
        'click .o_close_btn, .o_viewer_img_wrapper': '_onClose',
        'click .o_print_btn': '_onPrint',
        'DOMMouseScroll .o_viewer_content': '_onScroll', // Firefox
        'mousewheel .o_viewer_content': '_onScroll', // Chrome, Safari, IE
        'keydown': '_onKeydown',
        'keyup': '_onKeyUp',
        'mousedown .o_viewer_img': '_onStartDrag',
        'mousemove .o_viewer_content': '_onDrag',
        'mouseup .o_viewer_content': '_onEndDrag'
    };

    start() {
        this.$el.modal('show');
        this.$el.on('hidden.bs.modal', this._onDestroy.bind(this));
        this.$('.o_viewer_img').on("load", this._onImageLoaded.bind(this));
        this.$('[data-toggle="tooltip"]').tooltip({ delay: 0 });
        return super.start();
    }

    destroy() {
        if (this.isDestroyed()) {
            return;
        }
        this.trigger_up('document_viewer_closed');
        this.$el.modal('hide');
        this.$el.remove();
        super.destroy();
    }

    _next() {
        const index = this.attachment.indexOf(this.activeAttachment);
        const newIndex = (index + 1) % this.attachment.length;
        this.activeAttachment = this.attachment[newIndex];
        this._updateContent();
    }

    _previous() {
        const index = this.attachment.indexOf(this.activeAttachment);
        const newIndex = index === 0 ? this.attachment.length - 1 : index - 1;
        this.activeAttachment = this.attachment[newIndex];
        this._updateContent();
    }

    _reset() {
        this.scale = 1;
        this.dragStartX = this.dragstopX = 0;
        this.dragStartY = this.dragstopY = 0;
    }

    _updateContent() {
        this.$('.o_viewer_content').html(QWeb.render('odx.DocumentViewer.Content', {
            widget: this
        }));
        if (this.activeAttachment.fileType === 'application/pdf') {
            hidePDFJSButtons(this.$('.o_viewer_content')[0]);
        }
        this.$('.o_viewer_img').on("load", this._onImageLoaded.bind(this));
        this.$('[data-toggle="tooltip"]').tooltip({ delay: 0 });
        this._reset();
    }

    _getTransform(scale, angle) {
        return `scale3d(${scale}, ${scale}, 1) rotate(${angle}deg)`;
    }

    _rotate(angle) {
        this._reset();
        const newAngle = (this.angle || 0) + angle;
        this.$('.o_viewer_img').css('transform', this._getTransform(this.scale, newAngle));
        this.$('.o_viewer_img').css('max-width', newAngle % 180 !== 0 ? $(document).height() : '100%');
        this.$('.o_viewer_img').css('max-height', newAngle % 180 !== 0 ? $(document).width() : '100%');
        this.angle = newAngle;
    }

    _zoom(scale) {
        if (scale > 0.5) {
            this.$('.o_viewer_img').css('transform', this._getTransform(scale, this.angle || 0));
            this.scale = scale;
        }
        this.$('.o_zoom_reset').add('.o_zoom_out').toggleClass('disabled', scale === 1);
    }

    _onClose(e) {
        e.preventDefault();
        this.destroy();
    }

    _onDestroy() {
        this.destroy();
    }

    _onDownload(e) {
        e.preventDefault();
        window.location = `/web/content/${this.modelName}/${this.activeAttachment.id}/datas?download=true`;
    }

    _onDrag(e) {
        e.preventDefault();
        if (this.enableDrag) {
            const $image = this.$('.o_viewer_img');
            const $zoomer = this.$('.o_viewer_zoomer');
            const top = $image.prop('offsetHeight') * this.scale > $zoomer.height() ? e.clientY - this.dragStartY : 0;
            const left = $image.prop('offsetWidth') * this.scale > $zoomer.width() ? e.clientX - this.dragStartX : 0;
            $zoomer.css("transform", `translate3d(${left}px, ${top}px, 0)`);
            $image.css('cursor', 'move');
        }
    }

    _onEndDrag(e) {
        e.preventDefault();
        if (this.enableDrag) {
            this.enableDrag = false;
            this.dragstopX = e.clientX - this.dragStartX;
            this.dragstopY = e.clientY - this.dragStartY;
            this.$('.o_viewer_img').css('cursor', '');
        }
    }

    _onImageClicked(e) {
        e.stopPropagation();
    }

    _onImageLoaded() {
        this.$('.o_loading_img').hide();
    }

    _onKeydown(e) {
        switch (e.which) {
            case $.ui.keyCode.RIGHT:
                e.preventDefault();
                this._next();
                break;
            case $.ui.keyCode.LEFT:
                e.preventDefault();
                this._previous();
                break;
        }
    }

    _onKeyUp(e) {
        switch (e.which) {
            case $.ui.keyCode.ESCAPE:
                e.preventDefault();
                this._onClose(e);
                break;
        }
    }

    _onNext(e) {
        e.preventDefault();
        this._next();
    }

    _onPrevious(e) {
        e.preventDefault();
        this._previous();
    }

    _onPrint(e) {
        e.preventDefault();
        const src = this.$('.o_viewer_img').prop('src');
        const script = QWeb.render('im_livechat.legacy.mail.PrintImage', { src });
        const printWindow = window.open('about:blank', "_new");
        printWindow.document.open();
        printWindow.document.write(script);
        printWindow.document.close();
    }

    _onScroll(e) {
        const scale = e.originalEvent.wheelDelta > 0 || e.originalEvent.detail < 0 
            ? this.scale + SCROLL_ZOOM_STEP 
            : this.scale - SCROLL_ZOOM_STEP;
        this._zoom(scale);
    }

    _onStartDrag(e) {
        e.preventDefault();
        this.enableDrag = true;
        this.dragStartX = e.clientX - (this.dragstopX || 0);
        this.dragStartY = e.clientY - (this.dragstopY || 0);
    }

    _onVideoClicked(e) {
        e.stopPropagation();
        const videoElement = e.target;
        if (videoElement.paused) {
            videoElement.play();
        } else {
            videoElement.pause();
        }
    }

    _onRotate(e) {
        e.preventDefault();
        this._rotate(90);
    }

    _onZoomIn(e) {
        e.preventDefault();
        const scale = this.scale + ZOOM_STEP;
        this._zoom(scale);
    }

    _onZoomOut(e) {
        e.preventDefault();
        const scale = this.scale - ZOOM_STEP;
        this._zoom(scale);
    }

    _onZoomReset(e) {
        e.preventDefault();
        this._zoom(1);
    }
}

export default DocumentViewer;
