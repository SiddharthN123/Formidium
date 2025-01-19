from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from web3 import Web3
import sys

app = Flask(__name__)
CORS(app)

def connect_to_ganache():
    try:
        w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
        if not w3.is_connected():
            print("Failed to connect to Ganache")
            return None
        print("Successfully connected to Ganache")
        return w3
    except Exception as e:
        print(f"Error connecting to Ganache: {str(e)}")
        return None

w3 = connect_to_ganache()

@app.route('/get_transaction_history', methods=['GET'])
def get_transaction_history():
    try:
        # Check connection
        if not w3 or not w3.is_connected():
            return jsonify({
                "status": "error",
                "message": "Not connected to Ganache"
            }), 500

        address = request.args.get('address')
        if not address:
            return jsonify({"status": "error", "message": "No address provided"}), 400

        try:
            # Convert to checksum address
            checksum_address = Web3.to_checksum_address(address)
        except ValueError as e:
            return jsonify({"status": "error", "message": f"Invalid address format: {str(e)}"}), 400

        try:
            # Get latest block number
            latest_block = w3.eth.block_number
            print(f"Latest block number: {latest_block}")

            # Get all transactions from last 100 blocks (adjust as needed)
            all_transactions = []
            start_block = max(0, latest_block - 100)

            print(f"Scanning blocks from {start_block} to {latest_block}")

            for block_num in range(start_block, latest_block + 1):
                try:
                    # Get block with transactions
                    block = w3.eth.get_block(block_num, full_transactions=True)
                    
                    # Process transactions in the block
                    for tx in block['transactions']:
                        # Check if transaction involves our address
                        if (tx['from'].lower() == checksum_address.lower() or 
                            (tx['to'] and tx['to'].lower() == checksum_address.lower())):
                            
                            # Get transaction receipt for status
                            receipt = w3.eth.get_transaction_receipt(tx['hash'])
                            
                            transaction = {
                                'tx_hash': tx['hash'].hex(),
                                'from': tx['from'],
                                'to': tx['to'] if tx['to'] else 'Contract Creation',
                                'amount': float(Web3.from_wei(tx['value'], 'ether')),
                                'gas_price': float(Web3.from_wei(tx['gasPrice'], 'gwei')),
                                'status': 'Success' if receipt['status'] == 1 else 'Failed',
                                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                                'block_number': block_num
                            }
                            all_transactions.append(transaction)
                            print(f"Found transaction: {transaction['tx_hash']}")
                
                except Exception as block_error:
                    print(f"Error processing block {block_num}: {str(block_error)}")
                    continue

            response_data = {
                "status": "success",
                "address": checksum_address,
                "total_transactions": len(all_transactions),
                "transactions": all_transactions,
                "blocks_scanned": {
                    "start": start_block,
                    "end": latest_block,
                    "total": latest_block - start_block + 1
                }
            }

            return jsonify(response_data)

        except Exception as e:
            print(f"Error processing transactions: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Error processing transactions: {str(e)}"
            }), 500

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }), 500

@app.route('/check_connection', methods=['GET'])
def check_connection():
    if w3 and w3.is_connected():
        try:
            accounts = w3.eth.accounts
            latest_block = w3.eth.block_number
            return jsonify({
                "status": "connected",
                "accounts": accounts,
                "latest_block": latest_block
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error getting blockchain info: {str(e)}"
            })
    else:
        return jsonify({
            "status": "disconnected",
            "message": "Not connected to Ganache"
        })

if __name__ == '__main__':
    if not w3 or not w3.is_connected():
        print("Warning: Not connected to Ganache. Please ensure Ganache is running on port 7545")
    else:
        print(f"Connected to Ganache. Available accounts: {len(w3.eth.accounts)}")
    app.run(debug=True, port=5000)