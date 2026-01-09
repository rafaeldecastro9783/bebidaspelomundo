import base64
import requests
from django.conf import settings

def criar_pix_pagarme(pedido):
    url = f"{settings.PAGARME_BASE_URL}/orders"
    amount = int(pedido.total * 100)


    auth = base64.b64encode(
        f"{settings.PAGARME_API_KEY}:".encode()
    ).decode()

    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json",
    }

    payload = {
        "customer": {
            "name": pedido.cliente.nome_completo if pedido.cliente else "Cliente PDV",
            "type": "individual",
            "email": "pdv@mercado.local",
            "document": "00000000000",
            "phones": {
                "mobile_phone": {
                    "country_code": "55",
                    "area_code": "11",
                    "number": "999999999"
                }
            }
        },
        "items": [
            {
                "amount": amount,
                "description": f"Pedido {pedido.codigo}",
                "quantity": 1,
            }
        ],
        "payments": [
            {
                "payment_method": "pix",
                "pix": {
                    "expires_in": 3600
                }
            }
        ]
    }


    response = requests.post(url, json=payload, headers=headers)

    # DEBUG (mantenha por enquanto)
    print("STATUS:", response.status_code)
    print("RESPONSE:", response.text)

    response.raise_for_status()
    return response.json()
