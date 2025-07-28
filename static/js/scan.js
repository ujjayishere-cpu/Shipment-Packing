let currentPallet = "";

function onSuccessPallet(decodedText) {
  currentPallet = decodedText;
  alert("Set pallet: " + currentPallet);
  document.getElementById('pack-section').style.display = 'block';
}

function onSuccessPart(decodedText) {
  const [order_no, phase, part, qty] = decodedText.split('|');
  fetch('/scan', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ pallet:currentPallet, order_no, phase, part, qty: parseInt(qty)||1 })
  }).then(r=>r.json()).then(d=>console.log(d));
}

new Html5QrcodeScanner("pallet-reader", { fps:10, qrbox:250 })
  .render(onSuccessPallet, console.error);

new Html5QrcodeScanner("part-reader", { fps:10, qrbox:250 })
  .render(onSuccessPart, console.error);

function exportExcel(){
  window.location='/export';
}
