(function () {
  var script = document.currentScript;
  if (!script) return;
  var origin = new URL(script.src).origin;

  var iframe = document.createElement("iframe");
  iframe.src = origin + "/qr-code-generator/embed/";
  iframe.title = "QR Code Generator - Minitools Hub";
  iframe.loading = "lazy";
  iframe.style.width = "100%";
  iframe.style.maxWidth = "360px";
  iframe.style.height = "360px";
  iframe.style.border = "none";
  iframe.style.borderRadius = "12px";
  iframe.style.colorScheme = "normal";

  script.parentNode.insertBefore(iframe, script.nextSibling);
})();
