

# ============================================================================
# PRICE TRACKER FEATURE - Real-Time Component Pricing
# ============================================================================

@app.route('/api/component-prices', methods=['POST'])
def api_component_prices():
    """
    Get current market prices for all components in a build.
    Returns price data with retailer information.
    """
    try:
        data = request.json
        component_ids = {
            'cpu': data.get('cpu_id'),
            'gpu': data.get('gpu_id'),
            'motherboard': data.get('motherboard_id'),
            'ram': data.get('ram_id'),
            'storage': data.get('storage_id'),
            'psu': data.get('psu_id'),
            'case': data.get('case_id'),
            'cooler': data.get('cooler_id'),
            'monitor': data.get('monitor_id'),
            'os': data.get('os_id'),
            'peripherals': data.get('peripherals_id'),
            'keyboard': data.get('keyboard_id'),
            'mouse': data.get('mouse_id'),
            'headset': data.get('headset_id'),
            'webcam': data.get('webcam_id'),
            'fans': data.get('fans_id')
        }
        
        prices = {}
        total_cost = 0
        
        for category, comp_id in component_ids.items():
            if not comp_id or comp_id == "None Selected" or comp_id == "null" or comp_id == "":
                continue
                
            try:
                # Try unified components table first
                comp = db.components.find_one({'_id': ObjectId(comp_id)})
                
                # Fallback to category-specific tables
                if not comp:
                    col_map = {
                        'cpu': 'cpus', 'gpu': 'gpus', 'motherboard': 'motherboards',
                        'ram': 'ram', 'storage': 'storage', 'psu': 'psu',
                        'case': 'cases', 'cooler': 'coolers', 'monitor': 'monitors',
                        'os': 'os', 'fans': 'fans', 'keyboard': 'peripherals',
                        'mouse': 'peripherals', 'headset': 'peripherals',
                        'webcam': 'peripherals', 'peripherals': 'peripherals'
                    }
                    col = col_map.get(category, category)
                    comp = db[col].find_one({'_id': ObjectId(comp_id)})
                
                if comp:
                    # Extract price from component data
                    price = comp.get('price', comp.get('msrp', 0))
                    
                    # Handle price as string (e.g., "$299.99")
                    if isinstance(price, str):
                        price = float(price.replace('$', '').replace(',', ''))
                    
                    if price and price > 0:
                        prices[category] = {
                            'name': comp.get('name', 'Unknown'),
                            'price': round(price, 2),
                            'currency': 'USD',
                            'retailer': comp.get('retailer', 'Market Average'),
                            'url': comp.get('product_url', '#'),
                            'in_stock': comp.get('in_stock', True)
                        }
                        total_cost += price
                    else:
                        # No price data available
                        prices[category] = {
                            'name': comp.get('name', 'Unknown'),
                            'price': None,
                            'currency': 'USD',
                            'retailer': 'Price unavailable',
                            'url': '#',
                            'in_stock': False
                        }
                        
            except Exception as e:
                app.logger.error(f"Error fetching price for {category}: {e}")
                continue
        
        return jsonify({
            'status': 'success',
            'prices': prices,
            'total_cost': round(total_cost, 2),
            'currency': 'USD',
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Component prices error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/price-alert', methods=['POST'])
@login_required
def api_set_price_alert():
    """
    Set a price alert for a specific component.
    User will be notified when price drops below target.
    """
    try:
        data = request.json
        user_id = session.get('user_id')
        
        component_id = data.get('component_id')
        target_price = float(data.get('target_price', 0))
        
        if not component_id or target_price <= 0:
            return jsonify({
                'status': 'error',
                'message': 'Invalid component ID or target price'
            }), 400
        
        # Create or update price alert
        alert = {
            'user_id': ObjectId(user_id),
            'component_id': ObjectId(component_id),
            'target_price': target_price,
            'created_at': datetime.now(),
            'triggered': False
        }
        
        # Upsert (update if exists, insert if not)
        db.price_alerts.update_one(
            {
                'user_id': ObjectId(user_id),
                'component_id': ObjectId(component_id)
            },
            {'$set': alert},
            upsert=True
        )
        
        return jsonify({
            'status': 'success',
            'message': f'Price alert set for ${target_price:.2f}'
        })
        
    except Exception as e:
        app.logger.error(f"Price alert error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/price-history/<component_id>', methods=['GET'])
def api_price_history(component_id):
    """
    Get 30-day price history for a component.
    Returns simulated historical data for demonstration.
    """
    try:
        # Get current price
        comp = db.components.find_one({'_id': ObjectId(component_id)})
        if not comp:
            # Try category-specific tables
            for col in ['cpus', 'gpus', 'motherboards', 'ram', 'storage', 'psu', 'cases', 'coolers']:
                comp = db[col].find_one({'_id': ObjectId(component_id)})
                if comp:
                    break
        
        if not comp:
            return jsonify({
                'status': 'error',
                'message': 'Component not found'
            }), 404
        
        current_price = comp.get('price', comp.get('msrp', 299))
        if isinstance(current_price, str):
            current_price = float(current_price.replace('$', '').replace(',', ''))
        
        # Generate simulated 30-day price history
        import random
        from datetime import timedelta
        
        history = []
        base_price = current_price
        
        for i in range(30, 0, -1):
            date = datetime.now() - timedelta(days=i)
            # Add random variation (±10%)
            variation = random.uniform(-0.10, 0.10)
            price = base_price * (1 + variation)
            
            history.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': round(price, 2),
                'retailer': 'Market Average'
            })
        
        # Add current price as most recent
        history.append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'price': round(current_price, 2),
            'retailer': comp.get('retailer', 'Market Average')
        })
        
        return jsonify({
            'status': 'success',
            'component_name': comp.get('name', 'Unknown'),
            'history': history,
            'lowest_30d': round(min([h['price'] for h in history]), 2),
            'highest_30d': round(max([h['price'] for h in history]), 2),
            'average_30d': round(sum([h['price'] for h in history]) / len(history), 2)
        })
        
    except Exception as e:
        app.logger.error(f"Price history error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

