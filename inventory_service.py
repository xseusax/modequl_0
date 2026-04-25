from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)
CORS(app)

FILE = "inventory.xml"


def load():
    return ET.parse(FILE).getroot()


def save(root):
    ET.ElementTree(root).write(FILE, encoding="unicode", xml_declaration=True)


@app.route("/inventory", methods=["GET"])
def inventory():
    root = load()
    products = []

    for item in root.findall("Item"):
        products.append({
            "code": item.findtext("Code", "").strip(),
            "name": item.findtext("Name", "").strip(),
            "brand": item.findtext("Brand", "").strip(),
            "category": item.findtext("Category", "").strip(),
            "price": item.findtext("Price", "0").strip(),
            "stock": item.findtext("Stock", "0").strip()
        })

    return jsonify(products)


@app.route("/update_inventory", methods=["POST"])
def update():
    try:
        root = load()
        req = ET.fromstring(request.data)

        code = req.findtext("ProductCode", "").strip()
        qty = int(req.findtext("Quantity", "0"))

        if not code or qty <= 0:
            return Response("""
            <Response>
                <Status>Failed</Status>
                <Message>Invalid product or quantity</Message>
            </Response>
            """, mimetype="application/xml")

        for item in root.findall("Item"):
            item_code = item.findtext("Code", "").strip()

            if item_code == code:
                stock_el = item.find("Stock")
                stock = int(stock_el.text)

                if stock < qty:
                    return Response(f"""
                    <Response>
                        <Status>Failed</Status>
                        <Message>Not enough stock. Available: {stock}</Message>
                    </Response>
                    """, mimetype="application/xml")

                stock_el.text = str(stock - qty)
                save(root)

                return Response(f"""
                <Response>
                    <Status>Success</Status>
                    <Name>{item.findtext("Name")}</Name>
                    <Brand>{item.findtext("Brand")}</Brand>
                    <Price>{item.findtext("Price")}</Price>
                    <RemainingStock>{stock - qty}</RemainingStock>
                </Response>
                """, mimetype="application/xml")

        return Response("""
        <Response>
            <Status>Failed</Status>
            <Message>Item not found</Message>
        </Response>
        """, mimetype="application/xml")

    except Exception as e:
        return Response(f"""
        <Response>
            <Status>Failed</Status>
            <Message>{str(e)}</Message>
        </Response>
        """, mimetype="application/xml")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
