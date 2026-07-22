function initBarcodeScanner(opts) {
  var scanBtn = document.getElementById(opts.buttonId);
  if (!scanBtn) return;

  // Caller passes translated strings (the template knows the active language,
  // this static file doesn't) — fall back to English if it doesn't.
  var messages = Object.assign({
    starting: 'Starting camera...',
    libraryMissing: 'The scanning library did not load (needs an internet connection).',
    ready: 'Point the camera at the barcode.',
    cameraError: 'Could not access the camera: ',
    scanned: 'Scanned: '
  }, opts.messages || {});

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
    statusEl.textContent = messages.scanned + decodedText;
    closeModal();
    opts.onScan(decodedText);
  }

  scanBtn.addEventListener('click', function () {
    modal.style.display = 'flex';
    statusEl.textContent = messages.starting;
    if (typeof Html5Qrcode === 'undefined') {
      statusEl.textContent = messages.libraryMissing;
      return;
    }
    scanner = new Html5Qrcode('qr-reader');
    scanner.start(
      { facingMode: 'environment' },
      { fps: 10, qrbox: 220 },
      onScanSuccess
    ).then(function () {
      statusEl.textContent = messages.ready;
    }).catch(function (err) {
      statusEl.textContent = messages.cameraError + err;
    });
  });

  closeBtn.addEventListener('click', closeModal);
}
