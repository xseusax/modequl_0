from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import xml.etree.ElementTree as ET
import os
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

# =========================
# FILES
# =========================
INVENTORY_FILE = "inventory.xml"
ORDER_FILE = "orders.xml"


# =========================
# LOAD / SAVE INVENTORY
# =========================
def load_inventory():
    return ET.parse(INVENTORY_FILE).getroot()


def save_inventory(root):
    ET.ElementTree(root).write(INVENTORY_FILE, encoding="unicode", xml_declaration=True)


# =========================
# LOAD / SAVE ORDERS
# =========================
def load_orders():
    if not os.path.exists(ORDER_FILE):
        root = ET.Element("Orders")
        ET.ElementTree(root).write(ORDER_FILE, encoding="unicode", xml_declaration=True)
        return root
    return ET.parse(ORDER_FILE).getroot()


def save_orders(root):
    ET.ElementTree(root).write(ORDER_FILE, encoding="unicode", xml_declaration=True)


# =========================
# GET INVENTORY
# =========================
@app.route("/inventory", methods=["GET"])
def inventory():
    root = load_inventory()
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


# =========================
# UPDATE INVENTORY + CREATE ORDER
# =========================
@app.route("/update_inventory", methods=["POST"])
def update_inventory():
    try:
        inv_root = load_inventory()
        order_root = load_orders()

        req = ET.fromstring(request.data)

        code = req.findtext("ProductCode", "").strip()
        qty = int(req.findtext("Quantity", "0"))
        customer = req.findtext("CustomerName", "Guest").strip()

        if not code or qty <= 0:
            return Response("""
            <Response>
                <Status>Failed</Status>
                <Message>Invalid product or quantity</Message>
            </Response>
            """, mimetype="application/xml")

        for item in inv_root.findall("Item"):
            item_code = item.findtext("Code", "").strip()

            if item_code == code:
                stock_el = item.find("Stock")
                stock = int(stock_el.text)
                price = float(item.findtext("Price", "0"))

                if stock < qty:
                    return Response(f"""
                    <Response>
                        <Status>Failed</Status>
                        <Message>Not enough stock. Available: {stock}</Message>
                    </Response>
                    """, mimetype="application/xml")

                # =========================
                # CALCULATIONS
                # =========================
                new_stock = stock - qty
                total = price * qty
                txn_id = str(uuid.uuid4())
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # update stock
                stock_el.text = str(new_stock)
                save_inventory(inv_root)

                # =========================
                # SAVE ORDER HISTORY
                # =========================
                order = ET.SubElement(order_root, "Order")

                ET.SubElement(order, "TransactionID").text = txn_id
                ET.SubElement(order, "ProductCode").text = code
                ET.SubElement(order, "ProductName").text = item.findtext("Name")
                ET.SubElement(order, "Brand").text = item.findtext("Brand")
                ET.SubElement(order, "Quantity").text = str(qty)
                ET.SubElement(order, "Price").text = str(price)
                ET.SubElement(order, "TotalAmount").text = f"{total:.2f}"
                ET.SubElement(order, "CustomerName").text = customer
                ET.SubElement(order, "Timestamp").text = timestamp

                save_orders(order_root)

                # =========================
                # RESPONSE
                # =========================
                return Response(f"""
                <Response>
                    <Status>Success</Status>
                    <TransactionID>{txn_id}</TransactionID>
                    <Name>{item.findtext("Name")}</Name>
                    <Brand>{item.findtext("Brand")}</Brand>
                    <Price>{price}</Price>
                    <TotalAmount>{total:.2f}</TotalAmount>
                    <RemainingStock>{new_stock}</RemainingStock>
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


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
