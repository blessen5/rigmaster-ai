"""
RigMaster AI - Data Flow Diagram Generator (Using Pillow)
Creates DFD diagrams without requiring Graphviz installation
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_dfd_image():
    """Create a comprehensive DFD as an image"""
    
    # Create large canvas
    width, height = 3000, 2400
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a better font, fallback to default
    try:
        title_font = ImageFont.truetype("arial.ttf", 36)
        heading_font = ImageFont.truetype("arial.ttf", 24)
        label_font = ImageFont.truetype("arial.ttf", 18)
        small_font = ImageFont.truetype("arial.ttf", 14)
    except:
        title_font = ImageFont.load_default()
        heading_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Colors
    entity_color = (144, 238, 144)  # Light green
    process_color = (255, 255, 153)  # Light yellow
    datastore_color = (255, 182, 193)  # Light pink
    text_color = (0, 0, 0)  # Black
    line_color = (100, 100, 100)  # Dark gray
    
    # Title
    draw.text((width//2 - 400, 30), "RigMaster AI - Data Flow Diagram (Level 0)", 
              fill=text_color, font=title_font)
    
    # Helper functions
    def draw_rectangle(x, y, w, h, fill, text, font):
        """Draw a rectangle (external entity)"""
        draw.rectangle([x, y, x+w, y+h], fill=fill, outline=text_color, width=2)
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        draw.text((x + (w-text_w)//2, y + (h-text_h)//2), text, fill=text_color, font=font)
    
    def draw_ellipse(x, y, w, h, fill, text, font):
        """Draw an ellipse (process)"""
        draw.ellipse([x, y, x+w, y+h], fill=fill, outline=text_color, width=2)
        lines = text.split('\n')
        total_h = len(lines) * 20
        start_y = y + (h - total_h) // 2
        for i, line in enumerate(lines):
            text_bbox = draw.textbbox((0, 0), line, font=font)
            text_w = text_bbox[2] - text_bbox[0]
            draw.text((x + (w-text_w)//2, start_y + i*20), line, fill=text_color, font=font)
    
    def draw_cylinder(x, y, w, h, fill, text, font):
        """Draw a cylinder (data store)"""
        # Draw cylinder body
        draw.rectangle([x, y+10, x+w, y+h-10], fill=fill, outline=text_color, width=2)
        # Top ellipse
        draw.ellipse([x, y, x+w, y+20], fill=fill, outline=text_color, width=2)
        # Bottom ellipse
        draw.ellipse([x, y+h-20, x+w, y+h], fill=fill, outline=text_color, width=2)
        # Text
        lines = text.split('\n')
        total_h = len(lines) * 18
        start_y = y + (h - total_h) // 2
        for i, line in enumerate(lines):
            text_bbox = draw.textbbox((0, 0), line, font=small_font)
            text_w = text_bbox[2] - text_bbox[0]
            draw.text((x + (w-text_w)//2, start_y + i*18), line, fill=text_color, font=small_font)
    
    def draw_arrow(x1, y1, x2, y2, label=""):
        """Draw an arrow with label"""
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
            draw.text((mid_x+5, mid_y-15), label, fill=(0, 0, 139), font=small_font)
    
    # External Entities
    draw_rectangle(100, 200, 180, 80, entity_color, "User", heading_font)
    draw_rectangle(100, 1800, 180, 80, entity_color, "Admin", heading_font)
    draw_rectangle(2700, 400, 200, 80, entity_color, "AI Service", label_font)
    draw_rectangle(2700, 800, 200, 80, entity_color, "Shopping\nAPI", label_font)
    draw_rectangle(2700, 1200, 200, 80, entity_color, "Email\nService", label_font)
    
    # Processes (Center)
    draw_ellipse(600, 150, 180, 100, process_color, "1.0\nUser Auth", label_font)
    draw_ellipse(600, 300, 180, 100, process_color, "2.0\nBuild\nConfig", label_font)
    draw_ellipse(600, 450, 180, 100, process_color, "3.0\nComponent\nSelection", label_font)
    draw_ellipse(600, 600, 180, 100, process_color, "4.0\nValidation", label_font)
    draw_ellipse(1000, 150, 180, 100, process_color, "5.0\nAI Recom", label_font)
    draw_ellipse(1000, 300, 180, 100, process_color, "6.0\nPrice\nTracking", label_font)
    draw_ellipse(1000, 450, 180, 100, process_color, "7.0\nBuild\nManage", label_font)
    draw_ellipse(1000, 600, 180, 100, process_color, "8.0\nPerform\nAnalysis", label_font)
    draw_ellipse(1400, 150, 180, 100, process_color, "9.0\nPassword\nReset", label_font)
    draw_ellipse(1400, 300, 180, 100, process_color, "10.0\nAdmin\nManage", label_font)
    draw_ellipse(1400, 450, 180, 100, process_color, "11.0\nShopping\nIntegrate", label_font)
    draw_ellipse(1400, 600, 180, 100, process_color, "12.0\nBuild\nExport", label_font)
    
    # Data Stores (Right side)
    draw_cylinder(2100, 150, 150, 100, datastore_color, "D1\nUsers", small_font)
    draw_cylinder(2100, 300, 150, 100, datastore_color, "D2\nComponents", small_font)
    draw_cylinder(2100, 450, 150, 100, datastore_color, "D3\nSaved\nBuilds", small_font)
    draw_cylinder(2100, 600, 150, 100, datastore_color, "D4\nAI Cache", small_font)
    draw_cylinder(2100, 750, 150, 100, datastore_color, "D5\nPrice\nAlerts", small_font)
    draw_cylinder(2100, 900, 150, 100, datastore_color, "D6\nShopping\nCache", small_font)
    draw_cylinder(2100, 1050, 150, 100, datastore_color, "D7\nOTPs", small_font)
    
    # Data Flows - User to Processes
    draw_arrow(280, 240, 600, 200, "Login")
    draw_arrow(280, 250, 600, 350, "Build req")
    draw_arrow(280, 260, 600, 500, "Select")
    draw_arrow(280, 270, 1000, 350, "Alert")
    draw_arrow(280, 280, 1000, 500, "Save")
    
    # Processes to Data Stores
    draw_arrow(780, 200, 2100, 200, "Validate")
    draw_arrow(780, 500, 2100, 350, "Query")
    draw_arrow(1180, 500, 2100, 500, "Store")
    draw_arrow(1180, 200, 2100, 650, "Cache")
    draw_arrow(1180, 350, 2100, 800, "Alert")
    
    # Processes to External Services
    draw_arrow(1180, 200, 2700, 440, "AI req")
    draw_arrow(1580, 500, 2700, 840, "Search")
    draw_arrow(1580, 200, 2700, 1240, "OTP")
    
    # Return flows
    draw_arrow(2700, 460, 1180, 220, "AI resp")
    draw_arrow(2700, 860, 1580, 520, "Listings")
    draw_arrow(2700, 1260, 280, 290, "Email")
    
    # Admin flows
    draw_arrow(280, 1840, 1400, 350, "Manage")
    draw_arrow(1400, 370, 2100, 200, "User CRUD")
    draw_arrow(1400, 380, 2100, 350, "Comp CRUD")
    
    # Legend
    legend_y = 1400
    draw.text((100, legend_y), "LEGEND:", fill=text_color, font=heading_font)
    draw_rectangle(100, legend_y+40, 120, 60, entity_color, "", small_font)
    draw.text((230, legend_y+55), "External Entity", fill=text_color, font=label_font)
    
    draw_ellipse(100, legend_y+120, 120, 60, process_color, "", small_font)
    draw.text((230, legend_y+135), "Process", fill=text_color, font=label_font)
    
    draw_cylinder(100, legend_y+200, 120, 60, datastore_color, "", small_font)
    draw.text((230, legend_y+215), "Data Store", fill=text_color, font=label_font)
    
    draw_arrow(100, legend_y+290, 220, legend_y+290, "")
    draw.text((230, legend_y+275), "Data Flow", fill=text_color, font=label_font)
    
    # Save image
    output_file = "RigMaster_DFD_Level0.png"
    img.save(output_file, 'PNG', dpi=(300, 300))
    print(f"[SUCCESS] DFD Level 0 created: {output_file}")
    return output_file

def create_context_diagram():
    """Create Context Diagram"""
    
    width, height = 2400, 1800
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype("arial.ttf", 40)
        heading_font = ImageFont.truetype("arial.ttf", 22)
        label_font = ImageFont.truetype("arial.ttf", 16)
    except:
        title_font = ImageFont.load_default()
        heading_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
    
    entity_color = (144, 238, 144)
    system_color = (173, 216, 230)
    text_color = (0, 0, 0)
    line_color = (100, 100, 100)
    
    # Title
    draw.text((width//2 - 400, 30), "RigMaster AI - Context Diagram", 
              fill=text_color, font=title_font)
    
    def draw_rectangle(x, y, w, h, fill, text, font):
        draw.rectangle([x, y, x+w, y+h], fill=fill, outline=text_color, width=3)
        lines = text.split('\n')
        total_h = len(lines) * 25
        start_y = y + (h - total_h) // 2
        for i, line in enumerate(lines):
            text_bbox = draw.textbbox((0, 0), line, font=font)
            text_w = text_bbox[2] - text_bbox[0]
            draw.text((x + (w-text_w)//2, start_y + i*25), line, fill=text_color, font=font)
    
    def draw_circle(x, y, r, fill, text, font):
        draw.ellipse([x-r, y-r, x+r, y+r], fill=fill, outline=text_color, width=3)
        lines = text.split('\n')
        total_h = len(lines) * 30
        start_y = y - total_h // 2
        for i, line in enumerate(lines):
            text_bbox = draw.textbbox((0, 0), line, font=font)
            text_w = text_bbox[2] - text_bbox[0]
            draw.text((x - text_w//2, start_y + i*30), line, fill=text_color, font=font)
    
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
            draw.text((mid_x+10, mid_y-20), label, fill=(0, 0, 139), font=label_font)
    
    # Central System
    center_x, center_y = width//2, height//2 + 50
    draw_circle(center_x, center_y, 250, system_color, "RigMaster AI\nPC Building\nSystem", heading_font)
    
    # External Entities
    draw_rectangle(200, 200, 200, 100, entity_color, "User/\nCustomer", heading_font)
    draw_rectangle(200, 1400, 200, 100, entity_color, "Administrator", heading_font)
    draw_rectangle(1900, 200, 250, 100, entity_color, "AI Services\n(Gemini/Groq)", heading_font)
    draw_rectangle(1900, 700, 250, 100, entity_color, "Shopping API", heading_font)
    draw_rectangle(1900, 1200, 250, 100, entity_color, "Email Service", heading_font)
    
    # Data Flows
    draw_arrow(400, 250, center_x-250, center_y-150, "Login, Build")
    draw_arrow(center_x-200, center_y-200, 350, 300, "Results")
    
    draw_arrow(400, 1450, center_x-200, center_y+200, "Admin")
    draw_arrow(center_x-150, center_y+220, 350, 1500, "Dashboard")
    
    draw_arrow(center_x+250, center_y-150, 1900, 250, "AI Request")
    draw_arrow(1900, 280, center_x+230, center_y-120, "AI Response")
    
    draw_arrow(center_x+200, center_y, 1900, 750, "Search")
    draw_arrow(1900, 780, center_x+220, center_y+30, "Listings")
    
    draw_arrow(center_x+150, center_y+150, 1900, 1250, "OTP")
    draw_arrow(1900, 1280, 400, 280, "Email")
    
    output_file = "RigMaster_Context_Diagram.png"
    img.save(output_file, 'PNG', dpi=(300, 300))
    print(f"[SUCCESS] Context Diagram created: {output_file}")
    return output_file

if __name__ == "__main__":
    print("Generating RigMaster AI Data Flow Diagrams...")
    print("=" * 60)
    
    context_file = create_context_diagram()
    dfd_file = create_dfd_image()
    
    print("=" * 60)
    print("All DFD diagrams created successfully!")
    print(f"\n1. Context Diagram: {context_file}")
    print(f"2. Level 0 DFD: {dfd_file}")
