# `tikz-qrcode`: TikZ QR Code Generation with Contiguous Areas

`tikz-qrcode` provides a simple executable that generates TikZ code that produces the QR code corresponding to the given message, where contiguous areas are drawn as a single shape to avoid ugly breaks between the squares making up these shapes.
This has the side effect of enabling very fancy rounded corners, for example by executing:

```sh
tikz_qrcode "1mm" "rounded corners=0.25mm" "https://github.com/KurtBoehm/tikz-qrcode"
```
