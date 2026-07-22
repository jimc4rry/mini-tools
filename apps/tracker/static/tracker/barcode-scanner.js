function initBarcodeScanner(opts) {
  var scanBtn = document.getElementById(opts.buttonId);
  if (!scanBtn) return;

  var modal = document.getElementById('scan-modal');
  var closeBtn = document.getElementById('scan-close-btn');
  var statusEl = document.getElementById('scan-status');
  var scanner = null;

  function stopScanner() {
    if (!scanner) return;
    var s = scanner;
    scanner = null;
    try {
      s.stop().then(function () {
        try { s.clear(); } catch (e) {}
      }).catch(function () {});
    } catch (e) {
      // scanner.stop() throws synchronously if the camera never actually started
      // (e.g. permission denied) — nothing to stop, safe to ignore.
    }
  }

  function closeModal() {
    modal.style.display = 'none';
    stopScanner();
  }

  function onScanSuccess(decodedText) {
    statusEl.textContent = 'Σαρώθηκε: ' + decodedText;
    closeModal();
    opts.onScan(decodedText);
  }

  scanBtn.addEventListener('click', function () {
    modal.style.display = 'flex';
    statusEl.textContent = 'Εκκίνηση κάμερας...';
    if (typeof Html5Qrcode === 'undefined') {
      statusEl.textContent = 'Η βιβλιοθήκη σάρωσης δεν φορτώθηκε (χρειάζεται σύνδεση internet).';
      return;
    }
    scanner = new Html5Qrcode('qr-reader');
    scanner.start(
      { facingMode: 'environment' },
      { fps: 10, qrbox: 220 },
      onScanSuccess
    ).then(function () {
      statusEl.textContent = 'Στόχευσε το barcode με την κάμερα.';
    }).catch(function (err) {
      statusEl.textContent = 'Δεν ήταν δυνατή η πρόσβαση στην κάμερα: ' + err;
    });
  });

  closeBtn.addEventListener('click', closeModal);
}
