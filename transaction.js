document.addEventListener('DOMContentLoaded', function () {
    const viewTransactionsBtn = document.getElementById('viewTransactionsBtn');
    const submitPublicKeyBtn = document.getElementById('submitPublicKey');
    const publicKeyInputSection = document.getElementById('publicKeyInputSection');
    const transactionTableSection = document.getElementById('transactionTableSection');
    const transactionTable = document.getElementById('transactionTable').getElementsByTagName('tbody')[0];

    // Check Ganache connection when page loads
    fetch('http://localhost:5000/check_connection')
        .then(response => response.json())
        .then(data => {
            if (data.status !== 'connected') {
                alert('Cannot connect to Ganache. Please ensure Ganache is running on port 7545');
            }
        })
        .catch(error => {
            console.error('Connection check failed:', error);
            alert('Cannot connect to the server. Please ensure both Ganache and the Flask server are running.');
        });

    // Show public key input when clicking "View Recent Transactions"
    viewTransactionsBtn.addEventListener('click', function () {
        publicKeyInputSection.style.display = 'block';
    });

    // Submit public key and fetch transaction history
    submitPublicKeyBtn.addEventListener('click', function () {
        const publicKey = document.getElementById('publicKey').value.trim();

        if (publicKey === "") {
            alert("Please enter a valid Ethereum public key.");
            return;
        }

        // Hide the input and show the transaction table
        publicKeyInputSection.style.display = 'none';
        transactionTableSection.style.display = 'block';

        fetch(`http://localhost:5000/get_transaction_history?address=${publicKey}`)
        .then(response => {
            console.log("Response status:", response.status);
            return response.json().then(data => ({
                status: response.status,
                body: data
            }));
        })
            .then(({status, body}) => {
                console.log("Full response:", {status, body});  // Debug log
                
                if (status === 200) {
                    if (body.status === "error") {
                        throw new Error(body.message);
                    }
                    
                    transactionTable.innerHTML = '';
                    
                    if (body.transactions && body.transactions.length > 0) {
                        body.transactions.forEach(txn => {
                            const row = transactionTable.insertRow();
                            
                            // Add transaction hash with truncation
                            const hashCell = row.insertCell(0);
                            const shortHash = `${txn.tx_hash.substring(0, 6)}...${txn.tx_hash.substring(62)}`;
                            hashCell.textContent = shortHash;
                            hashCell.title = txn.tx_hash; // Show full hash on hover
                            
                            // Add other cells with shortened addresses
                            row.insertCell(1).textContent = `${txn.from.substring(0, 6)}...${txn.from.substring(38)}`;
                            row.insertCell(2).textContent = txn.to ? `${txn.to.substring(0, 6)}...${txn.to.substring(38)}` : 'N/A';
                            row.insertCell(3).textContent = txn.amount.toFixed(4);
                            row.insertCell(4).textContent = txn.status;
                            row.insertCell(5).textContent = txn.timestamp;
                        });
                    } else {
                        const row = transactionTable.insertRow();
                        const cell = row.insertCell(0);
                        cell.colSpan = 6;
                        cell.textContent = "No transactions found for this address";
                    }
                } else {
                    throw new Error(body.message || "Unknown error occurred");
                }
            })
            .catch(error => {
                console.error("Error:", error);
                alert(error.message || "An error occurred while fetching transactions");
                publicKeyInputSection.style.display = 'block';
                transactionTableSection.style.display = 'none';
            });
    });
});