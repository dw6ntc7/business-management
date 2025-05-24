// PDF Template Utilities
class PDFTemplateUtils {
    constructor() {
        this.initializeQRCode();
        this.setupGermanNumberFormat();
    }

    // QR-Code Generierung mit qrcode-generator
    generateQRCode(text, containerId) {
        console.log('Generating QR Code:', text, 'for container:', containerId);
        const container = document.getElementById(containerId);
        if (!container) {
            console.error('QR Container not found:', containerId);
            return;
        }
        
        // Check if qrcode-generator library is loaded
        if (typeof qrcode === 'undefined') {
            console.warn('qrcode-generator library not loaded yet, retrying...');
            setTimeout(() => this.generateQRCode(text, containerId), 100);
            return;
        }
        
        try {
            // Clear container
            container.innerHTML = '';
            
            // Create QR code instance
            const qr = qrcode(0, 'M'); // Type 0 = auto-detect, Error correction level M
            qr.addData(text);
            qr.make();
            
            // Generate SVG
            const svgString = qr.createSvgTag({
                cellSize: 4,
                margin: 2,
                scalable: true
            });
            
            // Insert SVG into container
            container.innerHTML = svgString;
            
            // Apply styling to SVG
            const svg = container.querySelector('svg');
            if (svg) {
                svg.style.width = '120px';
                svg.style.height = '120px';
                svg.style.border = '1px solid #e2e8f0';
                svg.style.borderRadius = '8px';
                svg.style.display = 'block';
            }
            
            console.log('QR Code generated successfully with SVG');
        } catch (error) {
            console.error('Error generating QR Code:', error);
            // Fallback: show error message
            container.innerHTML = '<div style="width:120px;height:120px;border:1px solid #e2e8f0;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#718096;font-size:12px;">QR-Code Fehler</div>';
        }
    }

    // Deutsche Zahlenformatierung
    formatGermanNumber(number) {
        return new Intl.NumberFormat('de-DE', {
            style: 'currency',
            currency: 'EUR'
        }).format(number);
    }

    // Datum formatieren
    formatGermanDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('de-DE');
    }

    // Berechnung für Netto/Brutto
    calculateTotal(items) {
        return items.reduce((sum, item) => {
            const price = parseFloat(item.price) || 0;
            const quantity = parseInt(item.quantity) || 0;
            return sum + (price * quantity);
        }, 0);
    }

    // QR-Code für Zahlungen
    generatePaymentQR(iban, bic, amount, reference, recipientName) {
        const epcQR = this.generateEPCQRCode(iban, bic, amount, reference, recipientName);
        return epcQR;
    }

    // EPC QR-Code für SEPA-Überweisungen
    generateEPCQRCode(iban, bic, amount, reference, recipientName) {
        const epcData = [
            'BCD',  // Service Tag
            '002',  // Version
            '1',    // Character set (UTF-8)
            'SCT',  // Identification
            bic || '',     // BIC
            recipientName || '', // Beneficiary Name
            iban || '',    // Beneficiary Account (IBAN)
            `EUR${amount}`, // Amount
            '',     // Purpose
            reference || '', // Remittance Information (unstructured)
            ''      // Remittance Information (structured)
        ].join('\n');
        
        return epcData;
    }

    // QR-Code für Website/Links
    generateWebsiteQR(url, containerId) {
        this.generateQRCode(url, containerId);
    }

    // Initialisierung der QR-Code-Bibliothek
    initializeQRCode() {
        // Prüfe ob qrcode-generator bereits geladen ist
        if (typeof qrcode === 'undefined') {
            console.log('Loading qrcode-generator library...');
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/qrcode-generator@1.4.4/qrcode.js';
            script.onload = () => {
                console.log('qrcode-generator library loaded successfully');
                // Teste die Bibliothek
                if (typeof qrcode !== 'undefined') {
                    console.log('qrcode-generator is ready for use');
                } else {
                    console.error('qrcode-generator failed to load properly');
                }
            };
            script.onerror = () => {
                console.error('Failed to load qrcode-generator library');
            };
            document.head.appendChild(script);
        } else {
            console.log('qrcode-generator library already available');
        }
    }

    setupGermanNumberFormat() {
        // Event Listener für automatische Formatierung
        document.addEventListener('input', (e) => {
            if (e.target.classList.contains('currency-input')) {
                const value = parseFloat(e.target.value) || 0;
                e.target.value = this.formatGermanNumber(value);
            }
        });
    }

    // Status Badge Styling
    getStatusBadgeClass(status) {
        const statusMap = {
            'Entwurf': 'badge-secondary',
            'Versendet': 'badge-primary', 
            'Angenommen': 'badge-success',
            'Abgelehnt': 'badge-danger',
            'Abgebrochen': 'badge-warning',
            'Offen': 'badge-warning',
            'Bezahlt': 'badge-success',
            'Überfällig': 'badge-danger',
            'Storniert': 'badge-secondary'
        };
        return statusMap[status] || 'badge-secondary';
    }

    // PDF Download Funktionalität
    downloadPDF() {
        window.print();
    }

    // Validierung von IBAN
    validateIBAN(iban) {
        // Entferne Leerzeichen und konvertiere zu Großbuchstaben
        iban = iban.replace(/\s/g, '').toUpperCase();
        
        // Prüfe Länge (Deutschland: 22 Zeichen)
        if (iban.length !== 22) return false;
        
        // Prüfe Format (DE + 20 Alphanumerisch)
        if (!/^DE\d{20}$/.test(iban)) return false;
        
        return true;
    }

    // Berechne MwSt
    calculateVAT(gross, vatRate) {
        const net = gross / (1 + vatRate / 100);
        const vat = gross - net;
        return {
            net: net,
            vat: vat,
            gross: gross
        };
    }

    // Berechne Netto aus Brutto und Steuersatz
    calculateNetFromGross(gross, vatRate) {
        return gross / (1 + vatRate / 100);
    }

    // Berechne Brutto aus Netto und Steuersatz  
    calculateGrossFromNet(net, vatRate) {
        return net * (1 + vatRate / 100);
    }

    // Drucken-spezifische Funktionen
    preparePrintView() {
        // Verstecke Navigations- und Aktionselemente
        const elements = document.querySelectorAll('.no-print, .navbar, .action-buttons');
        elements.forEach(el => el.style.display = 'none');
        
        // Setze Print-optimierte Styles
        document.body.classList.add('print-mode');
    }

    restoreNormalView() {
        // Stelle normale Ansicht wieder her
        const elements = document.querySelectorAll('.no-print, .navbar, .action-buttons');
        elements.forEach(el => el.style.display = '');
        
        document.body.classList.remove('print-mode');
    }
}

// Globale Utility-Funktionen
function DownloadPdf() {
    if (window.pdfUtils) {
        window.pdfUtils.preparePrintView();
        setTimeout(() => {
            window.print();
            setTimeout(() => {
                window.pdfUtils.restoreNormalView();
            }, 1000);
        }, 100);
    } else {
        window.print();
    }
}

// Initialisierung
window.pdfUtils = new PDFTemplateUtils();

// Debug-Informationen
console.log('PDF Utils loaded:', window.pdfUtils);
