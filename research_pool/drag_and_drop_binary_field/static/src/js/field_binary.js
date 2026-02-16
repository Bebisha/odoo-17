/** @odoo-module **/
import { registry } from "@web/core/registry";
import { BinaryField } from "@web/views/fields/binary/binary_field";
import { onMounted, useState } from "@odoo/owl";
import { useFileViewer } from "@web/core/file_viewer/file_viewer_hook";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

export class FieldBinaryFileDragAndDrop extends BinaryField {
  setup() {

  static template = "web.BinaryField";
   static components = {
        FileUploader,
    };
   static props = {
        ...standardFieldProps,
        acceptedFileExtensions: { type: String, optional: true },
        fileNameField: { type: String, optional: true },
    };

    super.setup();
    console.log("FieldBinaryFileDragAndDrop setup called");

    this.fileViewer = useFileViewer();
    this.orm = useService("orm"); // Ensure ORM service is available

    // Initialize state
    this.state = useState({
      isValid: true,
      fileName: '',
      fileType: '',
      objectUrl: '',
      enableZoom: this.props.enableZoom || false,
      zoomDelay: this.props.zoomDelay || 300,
      previewImage: this.props.previewImage || false,
      width: this.props.width || 'auto',
      height: this.props.height || 'auto',
    });

    console.log("Initial state:", this.state);

    onMounted(() => {
      this.el = this.__owl__.bdom.parentEl;
      console.log("Element mounted:", this.el);

      // Find the existing button
      const existingButton = this.el.querySelector('.btn.btn-link.btn-sm.lh-1.fa.fa-download.o_download_file_button');
      if (existingButton) {
        console.log("Existing button found:", existingButton);

        // Create a new button
        const newButton = document.createElement('button');
        newButton.className = 'btn btn-link btn-sm lh-1'; // Add classes as needed
        newButton.innerHTML = `<i class="fa fa-eye"></i>`; // Set the icon to a preview icon
        newButton.addEventListener('click', () => this.onClickNewButton());
        console.log("New button created and click event bound");

        // Insert the new button after the existing button
        existingButton.parentNode.insertBefore(newButton, existingButton.nextSibling);
        console.log("New button inserted after existing button");
      } else {
        console.log("Existing button not found");
      }
    });
  }

  async onClickNewButton() {
    console.log("New button clicked",this.props.record.data[this.props.fileNameField]);
    const recordID = this.props.record.resId;
    console.log("Fetching file data for record ID:", recordID);
    console.log("Fetching file data for record ID:", this.props.record.evalContextWithVirtualIds.active_model);
//    const recordID = this.props.record.resId;

    try {
      if (!this.orm) {
        throw new Error("ORM service is not available");
      }

      // Fetch file information
      const result = await this.orm.call('sale.order', 'get_file_info', [recordID, this.props.name]);
      const fileID = result.fileId;

      // Log the result to inspect
      console.log("Result from ORM call:", result);
      console.log("File ID from ORM call:", fileID);
      console.log("this.state.objectUrl", this.state.objectUrl);

      if (result && result.fileUrl) {
        this.state.fileName = result.fileName;
        this.state.fileType = result.fileType;
        this.state.objectUrl = result.fileUrl;

        console.log('this.state.fileName:', this.state.fileName);
        console.log('this.state.objectUrl:', this.state.objectUrl);

        // Set the field value to the file name
        this._updateFieldValue(this.state.fileName);

        // Handle PDF or other file types
        if (this.state.fileType === 'application/pdf') {
          this._previewPDF();
        } else {
          console.error("File type is not PDF:", this.state.fileType);
          alert("The file is not a PDF.");
        }
      } else {
        console.log("No file data available or URL is missing");
      }
    } catch (error) {
      console.error("Error fetching file data:", error);
      alert(`Error fetching file data: ${error.message}`); // Display a user-friendly message
    }
  }

  _updateFieldValue(fileName) {
    console.log(`Updating field value to: ${fileName}`);
    if (this.props.field) {
      // Assuming `field` is the field you want to update with the file name
      this.props.field = fileName;
    }
  }

  _previewPDF() {
    console.log(`Previewing PDF: ${this.state.objectUrl}`);

    // Load PDF.js library dynamically if not already available
    if (!window.pdfjsLib) {
      const script = document.createElement('script');
      console.log(script, "script");
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.10.377/pdf.min.js';
      script.onload = () => {
        this._initializePDFViewer();
      };
      document.head.appendChild(script);
    } else {
      this._initializePDFViewer();
    }
  }

  _initializePDFViewer() {
    const modalHtml = `
      <div class="modal-overlay"></div>
      <div class="modal-pdf">
        <div class="modal-content">
          <div class="modal-header">
            <a id="OrderPdfDownloadLink" href="${this.state.objectUrl}" download="${this.state.fileName}">
              <i class="fa fa-fw fa-download"></i> Download
            </a>
            <a class="close-pdf">&times;</a>
          </div>
          <div class="pdf-container">
            <div id="pdfCanvasContainer"></div>
          </div>
          <div class="modal-footer">
            <button title="Zoom In" id="m2m-zoom-in"><i class="fa fa-fw fa-plus"></i></button>
            <button title="Zoom Out" id="m2m-zoom-out"><i class="fa fa-fw fa-minus"></i></button>
            <button title="Print" id="m2m-print-pdf"><i class="fa fa-fw fa-print"></i></button>
            <a href="${this.state.objectUrl}" target="_blank">
              <button title="Open in New Tab"><i class="fa fa-fw fa-external-link"></i></button>
            </a>
          </div>
        </div>
      </div>`;

    $('body').append(modalHtml);
    $('.modal-pdf').show();
    console.log("PDF modal displayed");

    const pdfjsLib = window.pdfjsLib;
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.10.377/pdf.worker.min.js';
    const pdfCanvasContainer = document.getElementById('pdfCanvasContainer');

    pdfjsLib.getDocument(this.state.objectUrl)
      .promise
      .then(pdf => {
        const totalPageCount = pdf.numPages;

        function renderPage(pageNum) {
          pdf.getPage(pageNum)
            .then(page => {
              const viewport = page.getViewport({ scale: 1 });
              const canvas = document.createElement('canvas');
              canvas.className = 'pdf-page-canvas';
              pdfCanvasContainer.appendChild(canvas);
              const context = canvas.getContext('2d');
              canvas.height = viewport.height;
              canvas.width = viewport.width;
              page.render({ canvasContext: context, viewport: viewport })
                .promise
                .then(() => {
                  if (pageNum < totalPageCount) {
                    renderPage(pageNum + 1);
                  }
                })
                .catch(error => console.error('Error rendering page:', error));
            })
            .catch(error => console.error('Error getting page:', error));
        }

        renderPage(1);
      })
      .catch(error => console.error('Error loading PDF:', error));

    $('.close-pdf').click(() => {
      console.log("PDF modal closed");
      $('.modal-pdf').remove();
      $('.modal-overlay').remove();
    });

    $('.modal-overlay').click(event => {
      if ($(event.target).hasClass('modal-overlay')) {
        console.log("Overlay clicked");
        $('.modal-pdf').remove();
        $('.modal-overlay').remove();
      }
    });

    let zoomValue = 100;
    const zoomIncrement = 10;
    const minZoom = 50;
    const maxZoom = 200;
    const zoomContainer = document.getElementById('pdfCanvasContainer');
    const zoomInButton = document.getElementById('m2m-zoom-in');
    const zoomOutButton = document.getElementById('m2m-zoom-out');
    const printButton = document.getElementById('m2m-print-pdf');

    function updateZoomLevel() {
      zoomContainer.style.transform = `scale(${zoomValue / 100})`;
      console.log(`PDF zoom level updated to: ${zoomValue}`);
    }

    zoomInButton.addEventListener('click', () => {
      if (zoomValue < maxZoom) {
        zoomValue += zoomIncrement;
        updateZoomLevel();
      }
    });

    zoomOutButton.addEventListener('click', () => {
      if (zoomValue > minZoom) {
        zoomValue -= zoomIncrement;
        updateZoomLevel();
      }
    });

    printButton.addEventListener('click', () => {
      console.log('Printing PDF.');
      const iframe = document.createElement('iframe');
      iframe.src = this.state.objectUrl;
      iframe.style.display = 'none';
      document.body.appendChild(iframe);
      iframe.onload = () => {
        iframe.contentWindow.focus();
        iframe.contentWindow.print();
      };
    });
  }
}

export const FieldBinaryFileDragAndDropComponent = {
  component: FieldBinaryFileDragAndDrop,
  displayName: _t("Image"),
  supportedOptions: [
    'enableZoom',
    'zoomDelay',
    'previewImage',
    'width',
    'height',
  ],
  supportedTypes: ["binary"],
  fieldDependencies: [{ name: "write_date", type: "datetime" }],
  isEmpty: () => false,
//  extractProps: ({ attrs, options }) => ({
//    enableZoom: options.zoom,
//    zoomDelay: options.zoom_delay,
//    previewImage: options.preview_image,
//    acceptedFileExtensions: options.accepted_file_extensions,
//    width: options.size && Boolean(options.size[0]) ? options.size[0] : attrs.width,
//    height: options.size && Boolean(options.size[1]) ? options.size[1] : attrs.height,
//  }),
};

registry.category("fields").add("drag_and_drop", FieldBinaryFileDragAndDropComponent);
