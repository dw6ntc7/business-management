// Gemeinsame Funktionen für Angebots- und Rechnungsformular
function addPositionShared(positionIndex, containerId, catalogPositions) {
    const container = document.getElementById(containerId);
    const idx = positionIndex.value++;
    let selectHtml = '';
    if (catalogPositions && catalogPositions.length > 0) {
        selectHtml = `<select class="form-select catalog-select mb-2" onchange="fillFromCatalog(this, ${idx}, catalogPositions)">
            <option value="">Aus Katalog wählen ...</option>
            ${catalogPositions.map(pos => `<option value="${pos.id}">${pos.name} (${pos.unit}, ${pos.price} €)</option>`).join('')}
        </select>`;
    }
    const html = `
    <div class="card mb-2 p-2 position-row">
        ${selectHtml}
        <div class="row">
            <div class="col-md-4 mb-2">
                <input type="text" class="form-control" name="positions[${idx}][name]" placeholder="Positionsname" required>
            </div>
            <div class="col-md-2 mb-2">
                <input type="number" class="form-control" name="positions[${idx}][quantity]" placeholder="Menge" value="1" min="1" step="1" required oninput="updateTotalsShared()">
            </div>
            <div class="col-md-2 mb-2">
                <input type="number" class="form-control gross-input" name="positions[${idx}][gross]" placeholder="Brutto" step="0.01" required oninput="updateTotalsShared()">
            </div>
            <div class="col-md-2 mb-2">
                <input type="number" class="form-control vat-input" name="positions[${idx}][vat]" placeholder="MwSt" value="20" step="0.01" required oninput="updateTotalsShared()">
            </div>
            <div class="col-md-2 mb-2">
                <input type="number" class="form-control net-input" name="positions[${idx}][net]" placeholder="Netto" step="0.01" readonly>
            </div>
        </div>
    </div>`;
    container.insertAdjacentHTML('beforeend', html);
}

function fillFromCatalog(select, idx, catalogPositions) {
    const selectedId = select.value;
    const pos = catalogPositions.find(p => p.id == selectedId);
    if (!pos) return;
    const row = select.closest('.position-row');
    row.querySelector(`[name="positions[${idx}][name]"]`).value = pos.name;
    row.querySelector(`[name="positions[${idx}][gross]"]`).value = pos.price;
    row.querySelector(`[name="positions[${idx}][vat]"]`).value = pos.vat;
    row.querySelector(`[name="positions[${idx}][quantity]"]`).value = 1;
    updateTotalsShared();
}

function updateTotalsShared() {
    let totalGross = 0;
    let totalNet = 0;
    document.querySelectorAll('.position-row').forEach(function(row) {
        const grossInput = row.querySelector('.gross-input');
        const vatInput = row.querySelector('.vat-input');
        const netInput = row.querySelector('.net-input');
        const quantityInput = row.querySelector('[name*="[quantity]"]');
        let gross = parseFloat(grossInput.value) || 0;
        let vat = parseFloat(vatInput.value) || 20;
        let quantity = parseFloat(quantityInput.value) || 1;
        let net = gross / (1 + vat/100);
        netInput.value = (net).toFixed(2);
        totalGross += gross * quantity;
        totalNet += net * quantity;
    });
    if(document.getElementById('total_gross'))
        document.getElementById('total_gross').value = totalGross.toFixed(2);
    if(document.getElementById('total_net'))
        document.getElementById('total_net').value = totalNet.toFixed(2);
}

document.addEventListener('input', function(e) {
    if (e.target.classList.contains('gross-input') || e.target.classList.contains('vat-input') || e.target.name.includes('[quantity]')) {
        updateTotalsShared();
    }
});
window.addEventListener('DOMContentLoaded', function() {
    updateTotalsShared();
});
