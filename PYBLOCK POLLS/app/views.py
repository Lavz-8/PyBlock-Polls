import datetime
import json
import requests
from flask import render_template, redirect, request,jsonify
from flask import flash
from app import app
import smtplib
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, request, render_template
from flask import redirect, url_for

# The node with which our application interacts, there can be multiple
# such nodes as well.
CONNECTED_SERVICE_ADDRESS = "http://127.0.0.1:8000"
POLITICAL_PARTIES = ["Democratic Party","Republican Party","Socialist party"]
VOTER_IDS=[
        'VOID001','VOID002','VOID003',
        'VOID004','VOID005','VOID006',
        'VOID007','VOID008','VOID009',
        'VOID010','VOID011','VOID012',
        'VOID013','VOID014','VOID015']

vote_check=[]

posts = []


def fetch_posts():
    """
    Function to fetch the chain from a blockchain node, parse the
    data and store it locally.
    """
    get_chain_address = "{}/chain".format(CONNECTED_SERVICE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        vote_count = []
        chain = json.loads(response.content)
        for block in chain["chain"]:
            for tx in block["transactions"]:
                tx["index"] = block["index"]
                tx["hash"] = block["previous_hash"]
                content.append(tx)


        global posts
        posts = sorted(content, key=lambda k: k['timestamp'],
                       reverse=True)
        
# Dictionary to store generated OTPs
otp_storage = {}

# Function to generate OTP
def generate_otp():
    return ''.join(random.choices('0123456789', k=6))

# Function to send OTP via email
def send_otp(receiver_email, otp):
    sender_email = "email"  # Your email address
    sender_password = "password"  # Your application-specific password

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = "OTP for Verification"

    body = f"Your OTP is: {otp}"
    message.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(message)


@app.route("/send_otp", methods=["POST"])
def send_otp_route():
    email = request.form["email"]
    otp = generate_otp()
    send_otp(email, otp)
    otp_storage[email] = otp
    flash(f"The OTP is generated and sent to {email}. Please check your email and enter the OTP by again clicking the Enter OTP.")
    return redirect(url_for('index', email=email))

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    email = request.form["email_verify"]
    entered_otp = request.form["otp"]
    stored_otp = otp_storage.get(email)
    
    if stored_otp == entered_otp:
        flash('OTP verification successful!', 'success')  # Use 'success' category for successful verification
    else:
        flash('OTP verification failed. Please try again.', 'error')  # Use 'error' category for failed verification
    
    return redirect('/')

@app.route('/')
def index():
    fetch_posts()

    vote_gain = []

    for post in posts:
        vote_gain.append(post["party"])

    return render_template('index.html',
                           title='PYBLOCK POLLS',
                           posts=posts,
                           vote_gain=vote_gain,
                           node_address=CONNECTED_SERVICE_ADDRESS,
                           readable_time=timestamp_to_string,
                           political_parties=POLITICAL_PARTIES,
                           voter_ids=VOTER_IDS)


@app.route('/submit', methods=['POST'])
def submit_textarea():
    """
    Endpoint to create a new transaction via our application.
    """
    party = request.form["party"]
    voter_id = request.form["voter_id"]

    post_object = {
        'voter_id': voter_id,
        'party': party,
    }
    if voter_id not in VOTER_IDS:
        flash('Voter ID invalid, please select voter ID from sample!', 'error',)
        return redirect('/')
    if voter_id in vote_check:
        flash('Voter ID ('+voter_id+') already vote, Vote can be done by unique vote ID only once!', 'error')
        return redirect('/')
    else:
        vote_check.append(voter_id)

    # Submit a transaction
    new_tx_address = "{}/new_transaction".format(CONNECTED_SERVICE_ADDRESS)

    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})
    # print(vote_check)
    flash('Voted to '+party+' successfully!', 'success')
    return redirect('/')


def timestamp_to_string(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%Y-%m-%d %H:%M')


    
if __name__ == '__main__':
    app.run(debug=True)

