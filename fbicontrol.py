
import qrcode
import socket
import PIL
import os
import logging

log = logging.getLogger("RubusCast")

def fbi_show(file: str):
    try:
        os.system(f"sudo fbi -T 1 --noverbose -a {file}")
    except Exception as e:
        log.error(e)

def create_ip_qr(over_img="images/ready.jpg", output="images/qr_ip.jpg"):
    data = socket.gethostbyname(socket.gethostname())
    url = f"http://{data}"
    # Create qr code instance
    qr = qrcode.QRCode(
        version = 1,
        error_correction = qrcode.constants.ERROR_CORRECT_H,
        box_size = 10,
        border = 4,
    )
    # Add data
    qr.add_data(data)
    qr.make(fit=True)

    # Create an image from the QR Code instance
    img = qr.make_image()
    qrsize = 330
    img = img.resize((qrsize, qrsize))

    base = PIL.Image.open(over_img)

    border = 20
    base.load()[border:border+qrsize, border:border+qrsize] = img

    base.save(output)
