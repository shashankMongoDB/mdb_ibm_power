
# Building an Intelligent Finance Assistant with MongoDB Enterprise Advanced and IBM Watsonx.ai

For this tutorial, we’ll use a financial dataset containing customer details, transactions, spending insights, and metadata. These records reflect real-world scenarios such as payments, savings, and expenses, making them highly relevant for developing an intelligent finance assistant. We’ll generate vector embeddings for storing and retrieving this data using the sentence-transformers model (all-mpnet-base-v2), which captures the semantic meaning of financial data for efficient similarity searches and contextual data retrieval. To follow along, you’ll need an IDE, MongoDB Enterprise Advanced for data storage and indexing, and an IBM Watsonx.ai account—specifically using the “ibm/granite-3-8b-instruct” model as the decoder. By the end of this tutorial, you’ll have a functional system ready to deliver real-time financial assistance and personalized recommendations.

---

## Features
1. **Login Page**: 
   - User authentication interface for customers.
   - Minimalistic and responsive design.

2. **Chatbot Interface**: 
   - Interactive FAQ assistant powered by MongoDB Enterprise Advanced and IBM Watsonx.
   - Chatbot widget for real-time banking assistance.

3. **Backend Processing**:
   - Data preprocessing script (`preprocessing.py`) to clean and prepare data.
   - Core logic processing script (`processing.py`) to manage requests and responses.

---

## Files

### 1. `login.html`
- A responsive login page with a clean design.
- Accepts **Customer ID** for authentication.
- Includes an integrated chatbot widget for quick FAQs assistance.

### 2. `chatbot.html`
- A full-fledged chatbot interface with a sleek design.
- Includes welcome messages, logout functionality, and real-time interaction.
- Backend integration for fetching data via APIs.

### 3. `preprocessing.py`
- Prepares and cleans the data to ensure efficient processing.
- Key tasks: Data normalization, handling missing values, and optimization for MongoDB.

### 4. `processing.py`
- Implements the core chatbot logic.
- Handles API calls, processes user queries, and fetches responses from the database or AI model.

---

## Setup Instructions

### Prerequisites
- Python 3.11+
- MongoDB Enterprise Advanced Installed
- IBM Cloud Account to access IBM Watsonx.ai foundation models: Use need API_KEY, Project_ID, API_URL to run processing.py file

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo-url.git
   cd your-repo-directory
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the preprocessing script to prepare data:
   ```bash
   python preprocessing.py
   ```

4. Start the application backend:
   ```bash
   python processing.py
   ```

5. Serve the frontend:
   - Use a web server like Flask, or any static file server to host the HTML files.

---

## Usage
1. Open `<hosted-ip:5000/login>` in a web browser.
2. Enter **Customer ID** and log in. (eg: Enter between CUST00001-CUST01000)
3. Interact with the chatbot for banking assistance.

---

## Screenshots
<img width="1512" alt="Screenshot 2025-01-07 at 6 11 41 PM" src="https://github.com/user-attachments/assets/c3a9883f-59fa-443c-b7c4-f3bbd16f008d" />
<img width="1512" alt="Screenshot 2025-01-07 at 6 14 11 PM" src="https://github.com/user-attachments/assets/4de6b30c-704b-4972-89d2-991b4f7453bf" />



---

## Requirements

Refer to `requirements.txt` for the list of dependencies.

---

## Technologies Used
- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python, MongoDB
- **APIs**: IBM Watsonx AI
- **Database**: MongoDB Enterprise Advanced
