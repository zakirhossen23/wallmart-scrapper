import re

def clean_weight_and_check(name, average_weight=None):
    """
    Returns (weight_str, is_approximate)
    Rule: Exclude products whose weight contains approx, approximately or equivalent approximate-weight wording.
    """
    combined = f"{name or ''} {average_weight or ''}".lower()
    
    # Check for approximate weight terms
    approx_patterns = [
        r'\bapprox\b',
        r'\bapproximately\b',
        r'\bapprox\.\b',
        r'\bestimated\b',
        r'\bavg\b',
        r'\baverage\b',
        r'\bvariable\s*weight\b'
    ]
    for pat in approx_patterns:
        if re.search(pat, combined):
            return "", True
            
    # Try to extract weight from name or average_weight
    # Patterns: 64 fl oz, 16 oz, 1 lb, 28.2 OZ, 800 g, 100 ct, 4 pk, 1 Gallon, etc.
    patterns = [
        r'(\d+(?:\.\d+)?\s*(?:fl\s*oz|fl\.?\s*oz|oz|lb|lbs|g|kg|ct|count|pk|pack|gallon|gal|qt|quart|liter|l|ml))\b',
    ]
    for p in patterns:
        m = re.search(p, name or '', re.I)
        if m:
            return m.group(1).strip(), False
            
    if average_weight:
        return str(average_weight).strip(), False
        
    return "", False

def parse_price_and_deals(p):
    """
    Extract regular_price, sale_price, volume_deals, digital_deals, ppm.
    """
    price_info = p.get('priceInfo') or {}
    price_details = price_info.get('priceDetails') or {}
    price_lines = price_details.get('priceLines') or []
    
    regular_price = ""
    sale_price = ""
    ppm = ""
    
    # Check lines first
    current_val = ""
    was_val = ""
    discounted_val = ""
    unit_price_val = ""
    
    for line in price_lines:
        lt = line.get('lineType')
        vals = {v.get('key'): v.get('value') for v in line.get('values', []) if isinstance(v, dict)}
        if lt == 'CURRENT_PRICE':
            current_val = vals.get('PRICE') or ""
        elif lt == 'DISCOUNTED_PRICE':
            discounted_val = vals.get('PRICE') or ""
        elif lt == 'COMPARISON':
            was_val = vals.get('WAS_PRICE') or ""
        elif lt == 'UNIT_PRICE':
            unit_price_val = vals.get('UNIT_PRICE') or ""
            
    # Also fallback to priceInfo fields
    cur_p = price_info.get('currentPrice') or {}
    if not current_val and not discounted_val:
        if cur_p.get('price'):
            current_val = f"{float(cur_p['price']):.2f}"
            
    was_p = price_info.get('wasPrice') or {}
    if not was_val and was_p.get('price'):
        was_val = f"{float(was_p['price']):.2f}"
        
    up_p = price_info.get('unitPrice') or {}
    if not unit_price_val and up_p.get('priceString'):
        unit_price_val = str(up_p['priceString'])
        
    # Formatting regular vs sale price
    if was_val and (discounted_val or current_val):
        regular_price = was_val
        sale_price = discounted_val or current_val
    elif discounted_val and current_val and discounted_val != current_val:
        regular_price = current_val
        sale_price = discounted_val
    elif current_val:
        regular_price = current_val
        sale_price = ""
    elif discounted_val:
        regular_price = discounted_val
        sale_price = ""
        
    ppm = unit_price_val.strip()
    
    # Volume deals & Digital deals
    volume_deals_description = ""
    volume_deals_price = ""
    digital_deals_description = ""
    digital_deals_price = ""
    
    # Check promoData
    for promo in (p.get('promoData') or []):
        ptype = str(promo.get('type', '')).lower()
        desc = promo.get('description') or promo.get('text') or ''
        pr = promo.get('price') or ''
        if 'coupon' in desc.lower() or 'clip' in desc.lower() or 'digital' in ptype:
            digital_deals_description = desc
            if pr:
                digital_deals_price = str(pr)
        elif 'bogo' in desc.lower() or 'buy' in desc.lower() or 'volume' in ptype or 'multi' in ptype:
            volume_deals_description = desc
            if pr:
                volume_deals_price = str(pr)
                
    # Check badges
    badges = p.get('badges') or {}
    flags = badges.get('flags') or []
    for f in flags:
        ftext = f.get('text') or ''
        fkey = (f.get('key') or '').lower()
        if 'bogo' in ftext.lower() or 'buy' in ftext.lower() or 'multi' in fkey:
            if not volume_deals_description:
                volume_deals_description = ftext
                
    return {
        "regular_price": regular_price,
        "sale_price": sale_price,
        "volume_deals_description": volume_deals_description,
        "volume_deals_price": volume_deals_price,
        "digital_deals_description": digital_deals_description,
        "digital_deals_price": digital_deals_price,
        "ppm": ppm
    }

def is_private_label(brand, name, private_brands):
    b_norm = (brand or '').lower().strip()
    n_norm = (name or '').lower().strip()
    for pb in private_brands:
        pb_lower = pb.lower()
        if b_norm == pb_lower or n_norm.startswith(pb_lower):
            return "yes"
    return "no"

def build_record(p, category, sub_category, location_cfg, crawl_date, private_brands):
    name = p.get('name') or ''
    wt, is_approx = clean_weight_and_check(name, p.get('averageWeight'))
    if is_approx:
        return None  # Exclude approximate weight records per requirements
        
    prices = parse_price_and_deals(p)
    
    brand = p.get('brand') or ''
    store_brand = is_private_label(brand, name, private_brands)
    
    # URL
    can_url = p.get('canonicalUrl') or ''
    if can_url.startswith('/'):
        product_url = f"https://www.walmart.com{can_url.split('?')[0]}"
    else:
        product_url = can_url.split('?')[0] if can_url else ""
        
    # Image
    img_info = p.get('imageInfo') or {}
    image_url = img_info.get('thumbnailUrl') or ""
    
    # UPC
    upc = p.get('upc') or ""
    
    # 22-field strict order dict
    record = {
        "zipcode": str(location_cfg.get("zipcode") or ""),
        "store_name": str(location_cfg.get("store_name") or ""),
        "store_location": str(location_cfg.get("store_location") or ""),
        "store_logo": str(location_cfg.get("store_logo") or ""),
        "store_brand": store_brand,
        "category": str(category or ""),
        "sub_category": str(sub_category or ""),
        "product_title": str(name),
        "weight": str(wt),
        "regular_price": str(prices["regular_price"]),
        "sale_price": str(prices["sale_price"]),
        "volume_deals_description": str(prices["volume_deals_description"]),
        "volume_deals_price": str(prices["volume_deals_price"]),
        "digital_deals_description": str(prices["digital_deals_description"]),
        "digital_deals_price": str(prices["digital_deals_price"]),
        "image_url": str(image_url),
        "url": str(product_url),
        "upc": str(upc),
        "gupc": "",
        "ppm": str(prices["ppm"]),
        "unit_price": "",
        "crawl_date": str(crawl_date)
    }
    return record
