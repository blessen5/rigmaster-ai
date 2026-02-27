# Backend route for DeepSeek-R1 AI analysis
@app.route('/ai/analyze', methods=['POST'])
@login_required
def ai_analyze():
    """
    DeepSeek-R1 AI Assistant endpoint
    Analyzes user budget and requirements, provides recommendations
    """
    try:
        if db is None:
            return jsonify({'status': 'error', 'message': 'Database not connected'}), 500

        data = request.json
        budget = float(data.get('budget', 0))
        usage = data.get('usage', 'gaming')
        requirements = data.get('requirements', '')

        if budget <= 0:
            return jsonify({'status': 'error', 'message': 'Please enter a valid budget'}), 400

        # Fetch available components from database
        # Fetch available components from database
        components_data = {
            'cpus': list(db.components.find({'category': 'cpu'}, {'_id': 0, 'name': 1, 'price': 1, 'cores': 1, 'socket': 1}).limit(20)),
            'gpus': list(db.components.find({'category': 'gpu'}, {'_id': 0, 'name': 1, 'price': 1, 'vram': 1}).limit(20)),
            'motherboards': list(db.components.find({'category': 'motherboard'}, {'_id': 0, 'name': 1, 'price': 1, 'socket': 1, 'form_factor': 1}).limit(20)),
            'ram': list(db.components.find({'category': 'ram'}, {'_id': 0, 'name': 1, 'price': 1, 'capacity': 1, 'speed': 1}).limit(20)),
            'storage': list(db.components.find({'category': 'storage'}, {'_id': 0, 'name': 1, 'price': 1, 'capacity': 1, 'type': 1}).limit(20)),
            'psu': list(db.components.find({'category': 'psu'}, {'_id': 0, 'name': 1, 'price': 1, 'wattage': 1}).limit(20))
        }

        # Build system prompt for DeepSeek-R1
        system_prompt = """You are an AI assistant for PC system assembly and configuration.
Use ONLY the provided component data to make recommendations.
Explain recommendations in simple, educational language.
Do NOT make final decisions for the user.
Do NOT suggest components outside the provided database.
Focus on explaining trade-offs, compatibility, and value."""

        # Build user prompt with structured data
        user_prompt = f"""Budget: ${budget}
Primary Use: {usage}
Special Requirements: {requirements if requirements else 'None'}

Available Components:
CPUs: {len(components_data['cpus'])} options
GPUs: {len(components_data['gpus'])} options  
Motherboards: {len(components_data['motherboards'])} options
RAM: {len(components_data['ram'])} options
Storage: {len(components_data['storage'])} options
PSUs: {len(components_data['psu'])} options

Please analyze this build request and provide:
1. Budget allocation strategy
2. Component priority recommendations
3. Compatibility considerations
4. Performance expectations

Keep response concise (under 300 words)."""

        # Call DeepSeek-R1 API
        deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        if not deepseek_key:
            return jsonify({'status': 'error', 'message': 'AI service not configured'}), 500

        try:
            resp = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                json={
                    "model": "deepseek-reasoner",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 500
                },
                headers={"Authorization": f"Bearer {deepseek_key}", "Content-Type": "application/json"},
                timeout=30
            )

            if resp.status_code == 200:
                ai_response = resp.json()['choices'][0]['message']['content']
                return jsonify({'status': 'success', 'response': ai_response})
            else:
                app.logger.error(f"DeepSeek API error: {resp.status_code} - {resp.text}")
                return jsonify({'status': 'error', 'message': 'AI assistant temporarily unavailable'}), 500

        except Exception as e:
            app.logger.error(f"DeepSeek API call failed: {e}")
            return jsonify({'status': 'error', 'message': 'AI assistant temporarily unavailable'}), 500

    except Exception as e:
        app.logger.error(f"AI analyze error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
