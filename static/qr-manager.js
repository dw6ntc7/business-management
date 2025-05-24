// QR Code Generation Utility
// This script ensures QR codes are generated reliably across different browsers

window.QRCodeManager = {
    pendingGenerations: [],
    libraryReady: false,
    
    init: function() {
        console.log('🔧 QRCodeManager initialized');
        this.checkLibraryStatus();
    },
    
    checkLibraryStatus: function() {
        if (typeof qrcode !== 'undefined') {
            console.log('✅ QR library ready');
            this.libraryReady = true;
            this.processPendingGenerations();
        } else {
            console.log('⏳ Waiting for QR library...');
            setTimeout(() => this.checkLibraryStatus(), 100);
        }
    },
    
    generateQR: function(containerId, data) {
        if (this.libraryReady) {
            this.doGenerateQR(containerId, data);
        } else {
            console.log('📋 Queueing QR generation for:', containerId);
            this.pendingGenerations.push({containerId, data});
        }
    },
    
    processPendingGenerations: function() {
        console.log('🚀 Processing', this.pendingGenerations.length, 'pending QR generations');
        this.pendingGenerations.forEach(item => {
            this.doGenerateQR(item.containerId, item.data);
        });
        this.pendingGenerations = [];
    },
    
    doGenerateQR: function(containerId, data) {
        console.log('🎯 Generating QR for:', containerId);
        
        const container = document.getElementById(containerId);
        if (!container) {
            console.error('❌ Container not found:', containerId);
            return;
        }
        
        try {
            // Create QR code
            const qr = qrcode(0, 'M');
            qr.addData(data);
            qr.make();
            
            // Generate SVG
            const svgString = qr.createSvgTag({
                cellSize: 4,
                margin: 2,
                scalable: true
            });
            
            // Insert into container
            container.innerHTML = svgString;
            
            // Style the SVG
            const svg = container.querySelector('svg');
            if (svg) {
                svg.style.width = '120px';
                svg.style.height = '120px';
                svg.style.display = 'block';
                svg.style.margin = '0 auto';
                svg.style.border = '1px solid #e2e8f0';
                svg.style.borderRadius = '8px';
                svg.style.backgroundColor = 'white';
            }
            
            console.log('✅ QR generated successfully for:', containerId);
            
        } catch (error) {
            console.error('❌ QR generation failed for', containerId, ':', error);
            container.innerHTML = '<div style="width:120px;height:120px;border:1px solid #dc2626;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#dc2626;font-size:10px;text-align:center;">QR Error</div>';
        }
    }
};

// Auto-initialize when script loads
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => window.QRCodeManager.init(), 50);
});
