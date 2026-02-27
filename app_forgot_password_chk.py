

# --- Forgot Password Logic ---

def send_email(to_email, otp):
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = os.getenv('SMTP_PORT')
    smtp_email = os.getenv('SMTP_EMAIL')
    smtp_password = os.getenv('SMTP_PASSWORD')

    if not all([smtp_server, smtp_port, smtp_email, smtp_password]):
        print(f"[MOCK EMAIL] SMTP not configured. OTP for {to_email}: {otp}")
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = to_email
        msg['Subject'] = "RigMaster AI - Password Reset OTP"

        body = f"Your OTP for password reset is: {otp}\n\nThis code expires in 10 minutes."
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_email, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_email, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email to {to_email}: {e}")
        # Fallback for dev/testing if email fails
        print(f"[FALLBACK] OTP for {to_email}: {otp}")
        return False

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Please enter your email address.')
            return redirect(url_for('forgot_password'))

        global db
        if db is None: db = get_db()
        
        user = db.users.find_one({'email': email})
        if not user:
            # Security: Don't reveal if user exists
            flash('If an account exists with that email, we have sent an OTP.')
            return redirect(url_for('verify_otp'))

        otp = ''.join(random.choices(string.digits, k=6))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        db.otps.update_one(
            {'email': email},
            {'$set': {'otp': otp, 'expires_at': expires_at}},
            upsert=True
        )

        send_email(email, otp)
        
        # Store email in session to verify later (but don't trust it fully for password reset yet)
        session['reset_email_pending'] = email
        flash('If an account exists with that email, we have sent an OTP.')
        return redirect(url_for('verify_otp'))

    return render_template('forgot_password.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        otp_input = request.form.get('otp')
        email = session.get('reset_email_pending')

        if not email or not otp_input:
            flash('Session expired or invalid input.')
            return redirect(url_for('forgot_password'))

        global db
        if db is None: db = get_db()

        record = db.otps.find_one({'email': email})
        
        if not record:
            flash('Invalid or expired OTP.')
            return redirect(url_for('verify_otp'))

        if datetime.now(timezone.utc) > record['expires_at'].replace(tzinfo=timezone.utc):
            flash('OTP has expired.')
            return redirect(url_for('forgot_password'))

        if record['otp'] != otp_input:
            flash('Invalid OTP.')
            return redirect(url_for('verify_otp'))

        # OTP Verified
        session.pop('reset_email_pending', None)
        session['reset_email_verified'] = email # Authorized for reset
        
        # Clean up OTP
        db.otps.delete_one({'email': email})
        
        return redirect(url_for('reset_password'))

    return render_template('verify_otp.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    email = session.get('reset_email_verified')
    if not email:
        flash('Unauthorized access. Please start over.')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not password or len(password) < 6:
            flash('Password must be at least 6 characters.')
            return redirect(url_for('reset_password'))

        if password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('reset_password'))

        global db
        if db is None: db = get_db()

        hashed = generate_password_hash(password)
        db.users.update_one(
            {'email': email},
            {'$set': {'password': hashed}}
        )

        session.pop('reset_email_verified', None)
        flash('Password reset successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('reset_password.html')
