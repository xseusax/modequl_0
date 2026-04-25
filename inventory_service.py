from flask import Flask, Response, jsonify
from flask_cors import CORS
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)
CORS(app)

FILE = "inventory.xml"


def load():
    return ET.parse(FILE).getroot()


@app.route("/inventory", methods=["GET"])
def inventory():
    root = load()

    products = []

    for item in root.findall("Item"):
        products.append({
            "code": item.findtext("Code"),
            "name": item.findtext("Name"),
            "brand": item.findtext("Brand"),
            "price": item.findtext("Price"),
            "stock": item.findtext("Stock")
        })

    return jsonify(products)


@app.route("/inventory_xml", methods=["GET"])
def inventory_xml():
    root = load()
    return Response(
        ET.tostring(root, encoding="unicode"),
        mimetype="application/xml"
    )


@app.route("/update_inventory", methods=["POST"])
def update():
    root = load()
    req = ET.fromstring(request.data)

    code = req.find("ProductCode").text
    qty = int(req.find("Quantity").text)

    for item in root.findall("Item"):
        if item.find("Code").text == code:
            stock = int(item.find("Stock").text)

            if stock < qty:
                return Response("""
                <Response>
                    <Status>Failed</Status>
                    <Message>Not enough stock</Message>
                </Response>
                """, mimetype="application/xml")

            item.find("Stock").text = str(stock - qty)
            ET.ElementTree(root).write(FILE, encoding="unicode")

            return Response(f"""
            <Response>
                <Status>Success</Status>
                <Name>{item.find('Name').text}</Name>
                <Brand>{item.find('Brand').text}</Brand>
                <Price>{item.find('Price').text}</Price>
                <RemainingStock>{stock - qty}</RemainingStock>
            </Response>
            """, mimetype="application/xml")

    return Response("""
    <Response>
        <Status>Failed</Status>
        <Message>Item not found</Message>
    </Response>
    """, mimetype="application/xml")


if __name__ == "__main__":
    from flask import request
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
