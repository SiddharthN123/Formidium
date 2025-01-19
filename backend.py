from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# API Keys and URLs
EXCHANGE_RATE_API_KEY = "3ccabf37493f58299dc1857e"
FIAT_BASE_URL = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}"
COINGECKO_URL = "https://api.coingecko.com/api/v3"

def get_crypto_price(crypto_symbol: str, target_currency: str = 'usd') -> float:
    """Get cryptocurrency price from CoinGecko"""
    try:
        crypto_ids = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum'
        }
        
        if crypto_symbol not in crypto_ids:
            raise ValueError(f"Unsupported cryptocurrency: {crypto_symbol}")

        response = requests.get(
            f"{COINGECKO_URL}/simple/price",
            params={
                'ids': crypto_ids[crypto_symbol],
                'vs_currencies': target_currency.lower()
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data[crypto_ids[crypto_symbol]][target_currency.lower()]
        else:
            raise Exception(f"CoinGecko API error: {response.status_code}")
    except Exception as e:
        print(f"Error fetching crypto price: {e}")
        raise

def get_fiat_rates(base_currency: str) -> dict:
    """Get fiat currency exchange rates"""
    try:
        response = requests.get(f"{FIAT_BASE_URL}/latest/{base_currency}")
        if response.status_code == 200:
            return response.json()['conversion_rates']
        else:
            raise Exception(f"Exchange rate API error: {response.status_code}")
    except Exception as e:
        print(f"Error fetching fiat rates: {e}")
        raise

@app.route('/currency/convert', methods=['GET'])
def convert_currency():
    try:
        # Get request parameters
        base_currency = request.args.get('base_currency', 'USD').upper()
        target_currency = request.args.get('target_currency', 'EUR').upper()
        amount = float(request.args.get('amount', 1))

        # Validate amount
        if amount <= 0:
            return jsonify({
                "error": "Invalid amount",
                "message": "Amount must be greater than 0"
            }), 400

        # Initialize variables
        converted_amount = 0
        conversion_rate = 0
        display_rates = {}

        # Check if dealing with crypto
        crypto_currencies = ['BTC', 'ETH']
        is_base_crypto = base_currency in crypto_currencies
        is_target_crypto = target_currency in crypto_currencies

        try:
            if is_base_crypto:
                if is_target_crypto:
                    # Crypto to Crypto
                    base_usd = get_crypto_price(base_currency, 'usd')
                    target_usd = get_crypto_price(target_currency, 'usd')
                    conversion_rate = target_usd / base_usd
                else:
                    # Crypto to Fiat (e.g., BTC to INR)
                    conversion_rate = get_crypto_price(base_currency, target_currency.lower())
            elif is_target_crypto:
                # Fiat to Crypto
                crypto_price = get_crypto_price(target_currency, base_currency.lower())
                conversion_rate = 1 / crypto_price if crypto_price else 0
            else:
                # Fiat to Fiat
                rates = get_fiat_rates(base_currency)
                conversion_rate = rates[target_currency]

            # Calculate converted amount
            converted_amount = amount * conversion_rate

            # Get display rates
            if not is_base_crypto:
                # Add crypto rates
                for crypto in crypto_currencies:
                    try:
                        display_rates[crypto] = get_crypto_price(crypto, base_currency.lower())
                    except:
                        continue

            # Add fiat rates
            try:
                fiat_rates = get_fiat_rates(base_currency)
                common_currencies = ['USD', 'EUR', 'INR', 'GBP']
                for curr in common_currencies:
                    if curr != base_currency and curr != target_currency:
                        display_rates[curr] = fiat_rates[curr]
            except:
                pass

            return jsonify({
                "success": True,
                "base_currency": base_currency,
                "target_currency": target_currency,
                "amount": amount,
                "converted_amount": round(converted_amount, 8),
                "rate": conversion_rate,
                "rates": display_rates,
                "timestamp": datetime.now().isoformat()
            }), 200

        except Exception as e:
            print(f"Conversion error: {str(e)}")
            raise

    except ValueError as e:
        return jsonify({
            "error": "Invalid Input",
            "message": str(e)
        }), 400
    
    except Exception as e:
        return jsonify({
            "error": "Server Error",
            "message": f"An unexpected error occurred: {str(e)}"
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/currencies', methods=['GET'])
def get_available_currencies():
    """Get list of available currencies"""
    try:
        # Get fiat currencies
        fiat_rates = get_fiat_rates('USD')
        
        return jsonify({
            "success": True,
            "fiat_currencies": list(fiat_rates.keys()),
            "crypto_currencies": ['BTC', 'ETH']
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Server Error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)