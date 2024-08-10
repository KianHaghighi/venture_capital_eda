from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

import pandas as pd
import requests
import os
#from transformers import pipeline

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

PRODUCT_HUNT_API_TOKEN = os.getenv('PRODUCT_HUNT_API_TOKEN')
CLIENT_ID = os.getenv('PRODUCT_HUNT_CLIENT_ID')
CLIENT_SECRET = os.getenv('PRODUCT_HUNT_CLIENT_SECRET')


@app.route('/')
def index():
    return render_template('builder.html')

def generate_checkboxes_html(df):
    checkboxes_html = ""
    for index, row in df.iterrows():
        checkboxes_html += f'<div class="form-check">'
        checkboxes_html += f'<input class="form-check-input" type="checkbox" name="selected_rows" value="{index}" id="row_{index}">'
        checkboxes_html += f'<label class="form-check-label" for="row_{index}">{row["Topic"]}</label>'
        checkboxes_html += '</div>'
    return checkboxes_html

@app.route('/market_map', methods=['GET', 'POST'])
def market_map():
    # Product Hunt data set
    df_ph = pd.read_csv("datasets/product_hunt_data/2020.csv")  
    df_pf_2021 = pd.read_csv("datasets/product_hunt_data/2021.csv")  
    df_ph_2022 = pd.read_csv("datasets/product_hunt_data/2022.csv")
    df_ph = pd.concat([df_ph, df_pf_2021, df_ph_2022], ignore_index=True)

    markets_html = ""
    checkboxes_html = generate_checkboxes_html(df_ph)

    if request.method == 'POST':
        print(request.form)
        market = request.form['market']
        selected_rows = request.form.getlist('selected_rows')
        # Filter the DataFrame based on the market keyword.
        filtered_df = df_ph[df_ph['Topic'].str.contains(market, case=False, na=False)]
        # Alter the links so that the user can be directed
        df_ph['ShortUrl'] = df_ph['ShortUrl'].apply(lambda x: f'<a href="{x}">{x}</a>')
        markets_html = filtered_df.to_html(escape=False, classes='table table-striped', index=False)
    else:
        # Optionally, display the entire dataset or a subset when the page first loads
        markets_html = df_ph.to_html(escape=False, classes='table table-striped', index=False)

    return render_template('market_map.html', markets_html=markets_html, checkboxes_html=checkboxes_html)


@app.route('/crunchbase_data')
def crunchbase_data():
    # Read the CSV file
    df = pd.read_csv('datasets/crunchbase_data/investments_VC.csv', encoding='ISO-8859-1')
    
    # Get the first 5 rows
    df_head = df.head()
    
    # Convert to HTML table
    table_html = df_head.to_html(classes='table table-striped', index=False)
    
    return render_template('crunchbase_data.html', table_html=table_html)

@app.route('/select_companies', methods=['POST'])
def select_companies():
    selected_companies = request.form.getlist('company')
    # Process the selected companies
    return f"Selected companies: {', '.join(selected_companies)}"

def generate_companies_html(market):
    # Example function to generate HTML for companies
    companies = ['Company A', 'Company B', 'Company C']
    companies_html = '<div class="form-check">'
    for company in companies:
        companies_html += f'<input class="form-check-input" type="checkbox" name="company" value="{company}">'
        companies_html += f'<label class="form-check-label">{company}</label><br>'
    companies_html += '</div>'
    return companies_html

# Example GraphQL query
query = """
query {
  posts(order: TOP_DAY) {
    edges {
      node {
        id
        name
        tagline
        votes_count
        comments_count
        makers {
          id
          name
        }
      }
    }
  }
}
"""
# Function to get access token
def get_access_token(client_id, client_secret):
    url = "https://api.producthunt.com/v2/oauth/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        return None

# Function to fetch data from Product Hunt
def fetch_product_hunt_data(query, access_token):
    url = "https://api.producthunt.com/v2/api/graphql"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    query = """
    {
        posts(order: NEWEST) {
            edges {
                node {
                    id
                    name
                    tagline
                    website
                    topics {
                        edges {
                            node {
                                name
                            }
                        }
                    }
                    # Remove or replace the following fields if they don't exist
                    # votes_count
                    # comments_count
                }
            }
        }
    }
    """
    response = requests.post(url, json={'query': query}, headers=headers)
    print(response.status_code)  # Debugging status code
    if response.status_code == 200:
        return response.json()
    else:
        return "Error fetching data"

@app.route('/producthunt_data', methods=['GET'])
def get_product_hunt_data():
    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET
    access_token = get_access_token(client_id, client_secret)
    if access_token:
        data = fetch_product_hunt_data(query, access_token)
        return render_template('producthunt_data.html', data=data['data']['posts']['edges'])
    else:
        return jsonify({"error": "Failed to obtain access token"})

def fetch_crunchbase_data():
    url = "https://api.crunchbase.com/api/v3.1/your_endpoint"
    params = {
        "user_key": "e3941765dfeec33977f94b57cba729ba",
        "other_params": "value"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()  # Or process the response as needed
    else:
        return "Error fetching data"

def generate_companies_html(market):
    # Example function to generate HTML for companies
    companies = ['Company A', 'Company B', 'Company C']
    companies_html = '<div class="form-check">'
    for company in companies:
        companies_html += f'<input class="form-check-input" type="checkbox" name="company" value="{company}">'
        companies_html += f'<label class="form-check-label">{company}</label><br>'
    companies_html += '</div>'
    return companies_html

# Load the pre-trained model for classification
#classifier = pipeline('zero-shot-classification', model='facebook/bart-large-mnli')

@app.route('/create_market_map', methods=['POST'])
def create_market_map():
    # Get user input from the form
    market = request.form['market']
    funding = float(request.form['funding'])
    date_founded = request.form['date_founded']
    location = request.form['location']
    thesis = request.form['thesis']
    
    # Read the CSV file
    csv_file = request.files['csv_file']
    df = pd.read_csv(csv_file, encoding='ISO-8859-1')
    
    # Ensure the columns are of the correct data type
    df[' funding_total_usd '] = pd.to_numeric(df[' funding_total_usd '], errors='coerce')
    df['founded_at'] = pd.to_datetime(df['founded_at'], errors='coerce')
    
    # Define predefined categories and subcategories
    predefined_categories = {
    "Finance": [
        "Payments", 
        "Lending", 
        "Insurance", 
        "Wealth Management", 
        "Fintech Infrastructure", 
        "Personal Finance", 
        "Cryptocurrency"
    ],
    "Technology": [
        "Blockchain", 
        "Regtech", 
        "Artificial Intelligence", 
        "Cybersecurity", 
        "Cloud Computing", 
        "Internet of Things (IoT)"
    ],
    "Business": [
        "B2B", 
        "Enterprise Software", 
        "E-commerce", 
        "Logistics", 
        "Supply Chain Management"
    ],
    "Healthcare": [
        "Digital Health", 
        "Biotech", 
        "Medtech", 
        "Telemedicine"
    ],
    "Consumer": [
        "Consumer Electronics", 
        "Food and Beverage", 
        "Retail", 
        "Travel and Hospitality"
    ],
    "Sustainability": [
        "Renewable Energy", 
        "Clean Tech", 
        "Sustainable Agriculture"
    ]
}
    # Filter the data based on user input
    filtered_df = df[
        (df[' market '] == market) &
        (df[' funding_total_usd '] >= funding) &
        (df['founded_at'] >= pd.to_datetime(date_founded)) &
        (df['region'] == location)
    ]
    
    # Create a dictionary to hold sub-category data
    market_map = {category: [] for category in predefined_categories}
    
    # Check if 'subcategory' column exists
    if 'subcategory' in df.columns:
        # Proceed with filtering and processing
        filtered_df = df[
            (df['market'] == market) &
            (df['funding_total_usd'] >= funding) &
            (df['founded_at'] >= pd.to_datetime(date_founded)) &
            (df['region'] == location)
        ]
        
        # Populate the market_map with company names
        for category, subcategories in predefined_categories.items():
            for subcategory in subcategories:
                companies = filtered_df[filtered_df['subcategory'] == subcategory]['company_name'].tolist()
                market_map[category][subcategory] = companies
    else:
        print("Subcategory column not found.")
    
    return render_template('market_map.html', market=market, market_map=market_map)



@app.route('/create_from_scratch', methods=['GET', 'POST'])
def create_from_scratch():
    project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
    agent_id = os.getenv('DIALOGFLOW_AGENT_ID')
    return render_template('create_from_scratch.html', project_id=project_id, agent_id=agent_id)

@app.route('/upload_your_own', methods=['GET', 'POST'])
def upload_your_own():
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
