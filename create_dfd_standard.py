"""
RigMaster AI - Data Flow Diagram Generator (Standard DFD Symbols)
Uses exact symbols from the reference image:
- Rectangle: Data Source or Destination (External Entity)
- Oval: Process that Transforms Data Streams
- Parallel Lines: Data Store
- Arrow: A Flow of Data or Data Stream
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_standard_dfd():
    """Create DFD using standard symbols from the reference image"""
    
    # Create large canvas
    width, height = 3600, 2800
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a better font, fallback to default
    try:
        title_font = ImageFont.truetype("arial.ttf", 42)
        heading_font = ImageFont.truetype("arial.ttf", 20)
        label_font = ImageFont.truetype("arial.ttf", 16)
        small_font = ImageFont.truetype("arial.ttf", 14)
    except:
        title_font = ImageFont.load_default()
        heading_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Colors - keeping it simple like the reference
    text_color = (0, 0, 0)  # Black
    line_color = (0, 0, 0)  # Black
    fill_color = (255, 255, 255)  # White
    
    # Title
    draw.text((width//2 - 450, 30), "RigMaster AI - Data Flow Diagram (Level 0)", 
              fill=text_color, font=title_font)
    
    # Helper functions matching the reference symbols
    def draw_external_entity(x, y, w, h, text):
        """Draw a rectangle (Data Source or Destination)"""
        draw.rectangle([x, y, x+w, y+h], fill=fill_color, outline=line_color, width=3)
        lines = text.split('\n')
        total_h = len(lines) * 22
        start_y = y + (h - total_h) // 2
        for i, line in enumerate(lines):
            text_bbox = draw.textbbox((0, 0), line, font=heading_font)
            text_w = text_bbox[2] - text_bbox[0]
            draw.text((x + (w-text_w)//2, start_y + i*22), line, fill=text_color, font=heading_font)
    
    def draw_process(x, y, w, h, text):
        """Draw an oval (Process that Transforms Data Streams)"""
        draw.ellipse([x, y, x+w, y+h], fill=fill_color, outline=line_color, width=3)
        lines = text.split('\n')
        total_h = len(lines) * 20
        start_y = y + (h - total_h) // 2
        for i, line in enumerate(lines):
            text_bbox = draw.textbbox((0, 0), line, font=label_font)
            text_w = text_bbox[2] - text_bbox[0]
            draw.text((x + (w-text_w)//2, start_y + i*20), line, fill=text_color, font=label_font)
    
    def draw_data_store(x, y, w, h, text):
        """Draw parallel lines (Data Store)"""
        # Top line
        draw.line([x, y, x+w, y], fill=line_color, width=3)
        # Bottom line
        draw.line([x, y+h, x+w, y+h], fill=line_color, width=3)
        # Text
        lines = text.split('\n')
        total_h = len(lines) * 20
        start_y = y + (h - total_h) // 2
        for i, line in enumerate(lines):
            text_bbox = draw.textbbox((0, 0), line, font=label_font)
            text_w = text_bbox[2] - text_bbox[0]
            draw.text((x + (w-text_w)//2, start_y + i*20), line, fill=text_color, font=label_font)
    
    def draw_data_flow(x1, y1, x2, y2, label=""):
        """Draw an arrow (A Flow of Data or Data Stream)"""
        draw.line([x1, y1, x2, y2], fill=line_color, width=2)
        # Arrow head
        import math
        angle = math.atan2(y2-y1, x2-x1)
        arrow_len = 15
        arrow_angle = math.pi/6
        draw.line([x2, y2, 
                   x2 - arrow_len*math.cos(angle-arrow_angle), 
                   y2 - arrow_len*math.sin(angle-arrow_angle)], 
                  fill=line_color, width=2)
        draw.line([x2, y2, 
                   x2 - arrow_len*math.cos(angle+arrow_angle), 
                   y2 - arrow_len*math.sin(angle+arrow_angle)], 
                  fill=line_color, width=2)
        # Label
        if label:
            mid_x, mid_y = (x1+x2)//2, (y1+y2)//2
            draw.text((mid_x+5, mid_y-15), label, fill=text_color, font=small_font)
    
    # ========== EXTERNAL ENTITIES (Rectangles) ==========
    # Left side
    draw_external_entity(80, 300, 200, 100, "User")
    draw_external_entity(80, 2200, 200, 100, "Admin\n(Staff)")
    
    # Right side
    draw_external_entity(3200, 500, 280, 100, "AI Service\n(Gemini/Groq/Mistral)")
    draw_external_entity(3200, 1000, 280, 100, "Shopping API\n(Google Shopping)")
    draw_external_entity(3200, 1500, 280, 100, "Email Service\n(SMTP)")
    
    # ========== PROCESSES (Ovals) ==========
    # Column 1
    draw_process(500, 200, 220, 110, "1.0\nUser\nAuthentication")
    draw_process(500, 400, 220, 110, "2.0\nBuild\nConfiguration")
    draw_process(500, 600, 220, 110, "3.0\nComponent\nSelection")
    draw_process(500, 800, 220, 110, "4.0\nCompatibility\nValidation")
    
    # Column 2
    draw_process(900, 200, 220, 110, "5.0\nAI\nRecommendation")
    draw_process(900, 400, 220, 110, "6.0\nPrice\nTracking")
    draw_process(900, 600, 220, 110, "7.0\nBuild\nManagement")
    draw_process(900, 800, 220, 110, "8.0\nPerformance\nAnalysis")
    
    # Column 3
    draw_process(1300, 200, 220, 110, "9.0\nPassword\nReset")
    draw_process(1300, 400, 220, 110, "10.0\nAdmin\nManagement")
    draw_process(1300, 600, 220, 110, "11.0\nShopping\nIntegration")
    draw_process(1300, 800, 220, 110, "12.0\nBuild\nExport")
    
    # ========== DATA STORES (Parallel Lines) ==========
    draw_data_store(2400, 200, 400, 80, "D1: Users")
    draw_data_store(2400, 350, 400, 80, "D2: Components")
    draw_data_store(2400, 500, 400, 80, "D3: Saved Builds")
    draw_data_store(2400, 650, 400, 80, "D4: AI Cache")
    draw_data_store(2400, 800, 400, 80, "D5: Price Alerts")
    draw_data_store(2400, 950, 400, 80, "D6: Shopping Cache")
    draw_data_store(2400, 1100, 400, 80, "D7: OTPs")
    
    # ========== DATA FLOWS (Arrows) ==========
    
    # User to Processes
    draw_data_flow(280, 330, 500, 250, "Login credentials")
    draw_data_flow(280, 350, 500, 450, "Build requirements")
    draw_data_flow(280, 370, 500, 650, "Component selection")
    draw_data_flow(280, 390, 900, 450, "Set price alert")
    draw_data_flow(280, 410, 900, 650, "Save/Load build")
    
    # Processes to User (return flows)
    draw_data_flow(500, 280, 280, 360, "Auth token")
    draw_data_flow(500, 480, 280, 380, "Build interface")
    draw_data_flow(500, 680, 280, 400, "Component list")
    draw_data_flow(900, 480, 280, 420, "Price alerts")
    draw_data_flow(900, 680, 280, 440, "Saved builds")
    
    # Process 1 (Auth) to Data Store D1 (Users)
    draw_data_flow(720, 240, 2400, 240, "Validate user")
    draw_data_flow(2400, 260, 720, 260, "User data")
    
    # Process 3 (Component Selection) to D2 (Components)
    draw_data_flow(720, 650, 2400, 390, "Query components")
    draw_data_flow(2400, 410, 720, 670, "Component specs")
    
    # Process 4 (Validation) to D2 (Components)
    draw_data_flow(720, 850, 2400, 420, "Check compatibility")
    draw_data_flow(2400, 440, 720, 870, "Technical data")
    
    # Process 5 (AI Recommendation) to AI Service
    draw_data_flow(1120, 250, 3200, 550, "AI request")
    draw_data_flow(3200, 570, 1120, 270, "AI response")
    
    # Process 5 to D4 (AI Cache)
    draw_data_flow(1120, 260, 2400, 690, "Cache result")
    draw_data_flow(2400, 710, 1120, 280, "Cached data")
    
    # Process 6 (Price Tracking) to D5 (Price Alerts)
    draw_data_flow(1120, 450, 2400, 840, "Store alert")
    draw_data_flow(2400, 860, 1120, 470, "Alert data")
    
    # Process 7 (Build Management) to D3 (Saved Builds)
    draw_data_flow(1120, 650, 2400, 540, "Store build")
    draw_data_flow(2400, 560, 1120, 670, "Build data")
    
    # Process 8 (Performance Analysis) to D3 (Saved Builds)
    draw_data_flow(1120, 850, 2400, 570, "Get build config")
    draw_data_flow(2400, 590, 1120, 870, "Build specs")
    
    # Process 9 (Password Reset) to D1 (Users) and D7 (OTPs)
    draw_data_flow(1520, 250, 2400, 270, "Verify email")
    draw_data_flow(1520, 260, 2400, 1140, "Store OTP")
    draw_data_flow(2400, 1160, 1520, 280, "OTP data")
    
    # Process 9 to Email Service
    draw_data_flow(1520, 250, 3200, 1550, "Send OTP")
    draw_data_flow(3200, 1570, 280, 450, "OTP email")
    
    # Process 10 (Admin Management) to Data Stores
    draw_data_flow(1520, 450, 2400, 290, "User CRUD")
    draw_data_flow(1520, 470, 2400, 450, "Component CRUD")
    draw_data_flow(2400, 310, 1520, 490, "User list")
    draw_data_flow(2400, 470, 1520, 510, "Component list")
    
    # Process 11 (Shopping Integration) to Shopping API
    draw_data_flow(1520, 650, 3200, 1050, "Search products")
    draw_data_flow(3200, 1070, 1520, 670, "Product listings")
    
    # Process 11 to D6 (Shopping Cache)
    draw_data_flow(1520, 660, 2400, 990, "Cache results")
    draw_data_flow(2400, 1010, 1520, 680, "Cached listings")
    
    # Process 12 (Build Export) to D3 (Saved Builds)
    draw_data_flow(1520, 850, 2400, 600, "Get build")
    draw_data_flow(2400, 620, 1520, 870, "Build data")
    
    # Admin to Process 10
    draw_data_flow(280, 2250, 1300, 450, "Manage system")
    draw_data_flow(1300, 490, 280, 2280, "Admin dashboard")
    
    # Admin to Process 1 (Admin login)
    draw_data_flow(280, 2230, 500, 280, "Admin login")
    draw_data_flow(500, 290, 280, 2260, "Admin access")
    
    # ========== LEGEND ==========
    legend_x = 100
    legend_y = 1400
    
    draw.text((legend_x, legend_y), "Symbols", fill=text_color, font=title_font)
    
    # External Entity
    draw_external_entity(legend_x, legend_y + 80, 200, 80, "")
    draw.text((legend_x + 230, legend_y + 105), "Data Source or Destination", 
              fill=text_color, font=heading_font)
    
    # Data Flow
    draw_data_flow(legend_x, legend_y + 210, legend_x + 200, legend_y + 210, "")
    draw.text((legend_x + 230, legend_y + 195), "A Flow of Data or Data Stream", 
              fill=text_color, font=heading_font)
    
    # Process
    draw_process(legend_x, legend_y + 260, 200, 80, "")
    draw.text((legend_x + 230, legend_y + 285), "Process that Transforms Data Streams", 
              fill=text_color, font=heading_font)
    
    # Data Store
    draw_data_store(legend_x, legend_y + 390, 200, 40, "")
    draw.text((legend_x + 230, legend_y + 395), "Data Store", 
              fill=text_color, font=heading_font)
    
    # Save image
    output_file = "RigMaster_DFD_Standard.png"
    img.save(output_file, 'PNG', dpi=(300, 300))
    print(f"[SUCCESS] Standard DFD created: {output_file}")
    return output_file

def create_context_diagram_standard():
    """Create Context Diagram using standard symbols"""
    
    width, height = 2800, 2200
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype("arial.ttf", 44)
        heading_font = ImageFont.truetype("arial.ttf", 24)
        label_font = ImageFont.truetype("arial.ttf", 18)
    except:
        title_font = ImageFont.load_default()
        heading_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
    
    text_color = (0, 0, 0)
    line_color = (0, 0, 0)
    fill_color = (255, 255, 255)
    
    # Title
    draw.text((width//2 - 450, 40), "RigMaster AI - Context Diagram", 
              fill=text_color, font=title_font)
    
    def draw_rectangle(x, y, w, h, text):
        draw.rectangle([x, y, x+w, y+h], fill=fill_color, outline=line_color, width=3)
        lines = text.split('\n')
        total_h = len(lines) * 28
        start_y = y + (h - total_h) // 2
        for i, line in enumerate(lines):
            text_bbox = draw.textbbox((0, 0), line, font=heading_font)
            text_w = text_bbox[2] - text_bbox[0]
            draw.text((x + (w-text_w)//2, start_y + i*28), line, fill=text_color, font=heading_font)
    
    def draw_circle(x, y, r, text):
        draw.ellipse([x-r, y-r, x+r, y+r], fill=fill_color, outline=line_color, width=4)
        lines = text.split('\n')
        total_h = len(lines) * 32
        start_y = y - total_h // 2
        for i, line in enumerate(lines):
            text_bbox = draw.textbbox((0, 0), line, font=heading_font)
            text_w = text_bbox[2] - text_bbox[0]
            draw.text((x - text_w//2, start_y + i*32), line, fill=text_color, font=heading_font)
    
    def draw_arrow(x1, y1, x2, y2, label=""):
        draw.line([x1, y1, x2, y2], fill=line_color, width=3)
        import math
        angle = math.atan2(y2-y1, x2-x1)
        arrow_len = 20
        arrow_angle = math.pi/6
        draw.line([x2, y2, 
                   x2 - arrow_len*math.cos(angle-arrow_angle), 
                   y2 - arrow_len*math.sin(angle-arrow_angle)], 
                  fill=line_color, width=3)
        draw.line([x2, y2, 
                   x2 - arrow_len*math.cos(angle+arrow_angle), 
                   y2 - arrow_len*math.sin(angle+arrow_angle)], 
                  fill=line_color, width=3)
        if label:
            mid_x, mid_y = (x1+x2)//2, (y1+y2)//2
            draw.text((mid_x+10, mid_y-20), label, fill=text_color, font=label_font)
    
    # Central System (Process)
    center_x, center_y = width//2, height//2 + 100
    draw_circle(center_x, center_y, 300, "RigMaster AI\nPC Building\nSystem")
    
    # External Entities (Rectangles)
    draw_rectangle(200, 250, 280, 120, "User/\nCustomer")
    draw_rectangle(200, 1700, 280, 120, "Administrator\n(Staff)")
    draw_rectangle(2200, 250, 320, 120, "AI Services\n(Gemini/Groq/\nMistral)")
    draw_rectangle(2200, 800, 320, 120, "Shopping API\n(Google\nShopping)")
    draw_rectangle(2200, 1350, 320, 120, "Email Service\n(SMTP)")
    
    # Data Flows
    draw_arrow(480, 310, center_x-300, center_y-180, "Login, Build Config")
    draw_arrow(center_x-260, center_y-220, 420, 360, "Results, Builds")
    
    draw_arrow(480, 1760, center_x-250, center_y+250, "Admin, Manage")
    draw_arrow(center_x-200, center_y+270, 420, 1800, "Dashboard")
    
    draw_arrow(center_x+300, center_y-180, 2200, 310, "AI Request")
    draw_arrow(2200, 350, center_x+280, center_y-140, "AI Response")
    
    draw_arrow(center_x+250, center_y, 2200, 860, "Search Query")
    draw_arrow(2200, 900, center_x+270, center_y+40, "Product Listings")
    
    draw_arrow(center_x+200, center_y+200, 2200, 1410, "Send OTP")
    draw_arrow(2200, 1450, 460, 360, "OTP Email")
    
    output_file = "RigMaster_Context_Standard.png"
    img.save(output_file, 'PNG', dpi=(300, 300))
    print(f"[SUCCESS] Standard Context Diagram created: {output_file}")
    return output_file

if __name__ == "__main__":
    print("Generating RigMaster AI Data Flow Diagrams (Standard Symbols)...")
    print("=" * 70)
    
    context_file = create_context_diagram_standard()
    dfd_file = create_standard_dfd()
    
    print("=" * 70)
    print("All DFD diagrams created successfully using standard symbols!")
    print(f"\n1. Context Diagram: {context_file}")
    print(f"2. Level 0 DFD: {dfd_file}")
    print("\nSymbols used:")
    print("  - Rectangle: Data Source or Destination (External Entity)")
    print("  - Oval: Process that Transforms Data Streams")
    print("  - Parallel Lines: Data Store")
    print("  - Arrow: A Flow of Data or Data Stream")
